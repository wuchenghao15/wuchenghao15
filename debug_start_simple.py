#!/usr/bin/env python3
import os
import sys
import threading
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

result = None
error_info = None

def run_main():
    global result, error_info
    try:
        print("[DEBUG] Phase 0: Load smart_db_router", flush=True)
        import smart_db_router
        print("[DEBUG] ✓ smart_db_router loaded", flush=True)
        
        print("[DEBUG] Phase 1: Import app.py", flush=True)
        import importlib.util
        spec = importlib.util.spec_from_file_location("app_py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
        app_py = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_py)
        print("[DEBUG] ✓ app.py imported", flush=True)
        
        print("[DEBUG] Phase 2: Get Flask app", flush=True)
        flask_app = app_py.app
        print(f"[DEBUG] ✓ Flask app: {flask_app}", flush=True)
        
        print("[DEBUG] Phase 3: Run initialization", flush=True)
        from app import run_full_initialization
        init_results, flask_app = run_full_initialization(flask_app)
        print(f"[DEBUG] ✓ Initialization done", flush=True)
        
        result = flask_app
        
    except Exception as e:
        error_info = str(e)
        print(f"[DEBUG] ERROR: {e}", flush=True)
        traceback.print_exc()

thread = threading.Thread(target=run_main, daemon=True)
thread.start()
thread.join(timeout=60)

if thread.is_alive():
    print("[DEBUG] TIMEOUT after 60 seconds!", flush=True)
elif error_info:
    print(f"[DEBUG] FAILED: {error_info}", flush=True)
elif result:
    print("[DEBUG] SUCCESS! Starting server...", flush=True)
    result.run(host='0.0.0.0', port=8889, debug=False, use_reloader=False)
else:
    print("[DEBUG] Unknown result", flush=True)