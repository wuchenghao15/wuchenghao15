"""Seedance 2.5 视频生成 daemon — 定时轮询 + 结果回写"""
import os, sys, time, sqlite3, json, logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(BASE_DIR))
LOG_DIR = os.path.join(PROJECT, "_runtime", "logs")
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "app.db")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "auto_gen_seedance.log")),
        logging.StreamHandler(sys.stdout)
    ])
log = logging.getLogger("seedance_daemon")


class SeedanceDaemon:
    def __init__(self, poll_interval=60):
        self.interval = poll_interval
        from .client import SeedanceClient
        self.client = SeedanceClient()
        self._running = False
        log.info(f"SeedanceDaemon init model={self.client.model} available={self.client.available}")

    def ensure_tables(self, db):
        c = db.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS mt_seedance_tasks (
            task_id TEXT PRIMARY KEY,
            prompt TEXT,
            refs_json TEXT,
            ratio TEXT DEFAULT '16:9',
            duration INTEGER DEFAULT 5,
            generate_audio INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            video_url TEXT,
            usage_json TEXT,
            error_msg TEXT,
            created_at TEXT,
            updated_at TEXT
        )""")
        db.commit()

    def submit(self, prompt, refs=None, ratio="16:9", duration=5, generate_audio=False):
        if not self.client.available:
            return {"success": False, "error": "api_key not available"}
        sub = self.client.generate(prompt, refs=refs, ratio=ratio,
                                   duration=duration, generate_audio=generate_audio)
        if sub.get("success"):
            tid = sub["task_id"]
            db = sqlite3.connect(DB_PATH, timeout=10)
            try:
                self.ensure_tables(db)
                now = time.strftime("%Y-%m-%d %H:%M:%S")
                db.execute("INSERT OR REPLACE INTO mt_seedance_tasks"
                    "(task_id, prompt, refs_json, ratio, duration, generate_audio, status, created_at, updated_at)"
                    "VALUES (?,?,?,?,?,?, 'pending', ?,?)",
                    (tid, prompt[:500], json.dumps(refs or [], ensure_ascii=False),
                     ratio, duration, 1 if generate_audio else 0, now, now))
                db.commit()
            finally:
                db.close()
            log.info(f"SUBMIT {tid} prompt={prompt[:50]} dur={duration}s")
        return sub

    def poll_once(self):
        db = sqlite3.connect(DB_PATH, timeout=10)
        try:
            self.ensure_tables(db)
            rows = db.execute("SELECT task_id FROM mt_seedance_tasks"
                " WHERE status IN ('pending', 'running')"
                " ORDER BY created_at DESC LIMIT 10").fetchall()
            for (tid,) in rows:
                log.info(f"POLL {tid}")
                resp = self.client.poll(tid, max_wait=self.interval, interval=3)
                now = time.strftime("%Y-%m-%d %H:%M:%S")
                if resp.get("success"):
                    db.execute("UPDATE mt_seedance_tasks"
                        " SET status='succeeded', video_url=?, usage_json=?, updated_at=?"
                        " WHERE task_id=?",
                        (resp.get("video_url", ""),
                         json.dumps(resp.get("usage", {}), ensure_ascii=False), now, tid))
                    log.info(f"DONE  {tid} video={resp.get('video_url','')[:80]}")
                elif resp.get("status") == "timeout":
                    db.execute("UPDATE mt_seedance_tasks SET status='running', updated_at=? WHERE task_id=?", (now, tid))
                else:
                    db.execute("UPDATE mt_seedance_tasks"
                        " SET status='failed', error_msg=?, updated_at=?"
                        " WHERE task_id=?", (json.dumps(resp.get("error", {}), ensure_ascii=False)[:500], now, tid))
                    log.warning(f"FAIL  {tid} err={resp.get('error',{}).get('message','')[:80]}")
                db.commit()
        finally:
            db.close()

    def run(self):
        self._running = True
        log.info("SeedanceDaemon STARTED loop=%ds", self.interval)
        h = self.client.health()
        log.info(f"HEALTH {h}")
        while self._running:
            try:
                self.poll_once()
            except Exception as e:
                log.error(f"loop err: {e}")
            time.sleep(self.interval)


def main():
    poll_interval = int(os.environ.get("SEEDANCE_POLL_INTERVAL", "60"))
    d = SeedanceDaemon(poll_interval=poll_interval)
    try:
        d.run()
    except KeyboardInterrupt:
        d._running = False
        log.info("SeedanceDaemon STOPPED")


if __name__ == "__main__":
    main()
