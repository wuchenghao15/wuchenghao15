"""auto_gen_ws subscriber"""
import json, time, sqlite3, os
class WSPublisher:
    def __init__(self, trigger_dir=None):
        if trigger_dir is None: trigger_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        self.trigger_file = os.path.join(trigger_dir, "_ws_trigger.json")
    def push(self, channel, payload=None, level="info"):
        payload = payload or {}
        try:
            app_db = os.path.join(os.path.dirname(self.trigger_file), "engines", "app.db")
            c = sqlite3.connect(app_db, timeout=3)
            c.execute("CREATE TABLE IF NOT EXISTS mt_ws_notifications (nid INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, payload TEXT, level TEXT DEFAULT 'info', pushed INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))")
            cur = c.execute("INSERT INTO mt_ws_notifications (channel,payload,level) VALUES (?,?,?)", (channel, json.dumps(payload, ensure_ascii=False), level))
            nid = cur.lastrowid; c.commit(); c.close()
            with open(self.trigger_file,"w") as f: json.dump({"nid":nid,"channel":channel,"ts":int(time.time())}, f)
            return nid
        except Exception as e:
            print(f"[WSPublisher] err: {e}"); return -1
if __name__ == "__main__":
    nid = WSPublisher().push("system", {"msg":"auto_gen_ws test","source":"daemon"}, "info")
    print(f"push nid={nid}")
