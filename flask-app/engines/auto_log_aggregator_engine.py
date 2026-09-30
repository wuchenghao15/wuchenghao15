#!/usr/bin/env python3
"""auto_log_aggregator v6.0 - 多源日志聚合 + 异常聚类"""
import os, re, json, sqlite3
from collections import defaultdict

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "_runtime", "logs")
DB = os.path.join(os.path.dirname(__file__), "app.db")

def collect_logs():
    logs = []
    if not os.path.isdir(_LOG_DIR): return logs
    for f in os.listdir(_LOG_DIR):
        if not f.endswith(".log"): continue
        fp = os.path.join(_LOG_DIR, f)
        try:
            with open(fp, "r", errors="ignore") as fh:
                for line in fh.readlines()[-100:]:
                    logs.append({"file": f, "line": line.strip()})
        except: pass
    return logs

def cluster_errors(logs):
    pats = [r"database is locked", r"IndentationError", r"PermissionError", r"Connection refused", r"Traceback", r"SyntaxError"]
    clusters = defaultdict(list)
    for log in logs:
        for pat in pats:
            if re.search(pat, log["line"], re.I):
                clusters[pat].append(log)
                break
    return dict(clusters)

def write_db(clusters):
    conn = sqlite3.connect(DB, timeout=5)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""CREATE TABLE IF NOT EXISTS mt_ai_log_aggregations (
        agg_id INTEGER PRIMARY KEY AUTOINCREMENT, pattern TEXT, count INTEGER,
        sample TEXT, created_at TEXT DEFAULT (datetime('now')))""")
    for pat, items in clusters.items():
        conn.execute("INSERT INTO mt_ai_log_aggregations (pattern, count, sample) VALUES (?,?,?)",
                     (pat, len(items), json.dumps(items[:3], ensure_ascii=False)))
    conn.commit(); conn.close()

if __name__ == "__main__":
    logs = collect_logs(); clusters = cluster_errors(logs)
    write_db(clusters)
    print(f"[auto_log_agg] {len(logs)} lines, {len(clusters)} patterns")
