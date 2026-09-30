#!/usr/bin/env python3
"""auto_gen_ws v6.0 - WebSocket server (port 8889)"""
import asyncio, json, os, time, sqlite3
try:
    import websockets; WS_AVAIL = True
except ImportError: WS_AVAIL = False
WS_PORT = 8889
APP_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app.db")
TRIGGER_FILE = os.path.join(os.path.dirname(APP_DB), "_ws_trigger.json")
_CHANNEL_CLIENTS = {}; _ALL_CLIENTS = set(); _LAST_MTIME = 0

def _ensure():
    c = sqlite3.connect(APP_DB, timeout=5); c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS mt_ws_notifications (nid INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, payload TEXT, level TEXT DEFAULT 'info', pushed INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))""")
    c.commit(); c.close()

async def _broadcast(channel, msg):
    targets = list(set(_CHANNEL_CLIENTS.get(channel,set())) | _ALL_CLIENTS)
    if not targets: return
    data = json.dumps(msg, ensure_ascii=False)
    for ws in targets:
        try: await ws.send(data)
        except: pass

def _scan_trigger():
    global _LAST_MTIME
    try:
        if not os.path.exists(TRIGGER_FILE): return None
        st = os.stat(TRIGGER_FILE)
        if st.st_mtime == _LAST_MTIME: return None
        _LAST_MTIME = st.st_mtime
        with open(TRIGGER_FILE) as f: return json.load(f)
    except: return None

async def ws_handler(websocket):
    _ALL_CLIENTS.add(websocket); subscribed = set()
    try:
        await websocket.send(json.dumps({"type":"hello","server":"auto_gen_ws","port":WS_PORT,"ts":int(time.time())}))
        async for message in websocket:
            try:
                msg = json.loads(message)
                a = msg.get("type","")
                if a == "subscribe":
                    ch = msg.get("channel","")
                    if ch:
                        subscribed.add(ch)
                        _CHANNEL_CLIENTS.setdefault(ch,set()).add(websocket)
                        await websocket.send(json.dumps({"type":"subscribed","channel":ch}))
                elif a == "ping":
                    await websocket.send(json.dumps({"type":"pong","ts":int(time.time())}))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"type":"error","msg":"invalid json"}))
    except: pass
    finally:
        _ALL_CLIENTS.discard(websocket)
        for ch in subscribed:
            _CHANNEL_CLIENTS.get(ch,set()).discard(websocket)

async def broadcaster():
    while True:
        await asyncio.sleep(2)
        trigger = _scan_trigger()
        if not trigger: continue
        channel = trigger.get("channel","system"); nid = trigger.get("nid",0)
        await _broadcast(channel, {"type":"notify","channel":channel,"nid":nid,"ts":int(time.time())})
        try:
            c = sqlite3.connect(APP_DB, timeout=3)
            c.execute("UPDATE mt_ws_notifications SET pushed=1 WHERE nid=?",(nid,))
            c.commit(); c.close()
        except: pass

async def main():
    if not WS_AVAIL:
        print("[auto_gen_ws] websockets 未安装!"); return
    _ensure()
    print(f"[auto_gen_ws] WebSocket server ws://0.0.0.0:{WS_PORT}")
    asyncio.create_task(broadcaster())
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        await asyncio.Future()

def run():
    try: asyncio.run(main())
    except KeyboardInterrupt: print("[auto_gen_ws] shutdown")
if __name__ == "__main__": run()
