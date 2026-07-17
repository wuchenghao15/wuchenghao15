#!/usr/bin/env python3
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_initialize():
    print("[DEBUG] Starting app.py initialization debug...", flush=True)
    
    try:
        print("[DEBUG] Phase 0: Load smart_db_router first", flush=True)
        import smart_db_router
        print("[DEBUG] ✓ Phase 0 completed - smart_db_router loaded", flush=True)
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 0 FAILED: {e}", flush=True)
        traceback.print_exc()
        return None
    
    try:
        print("[DEBUG] Phase 1: Import app.py directly", flush=True)
        import importlib.util
        import threading
        
        app_py = None
        error = None
        
        def do_import():
            nonlocal app_py, error
            try:
                spec = importlib.util.spec_from_file_location("app_py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
                app_py = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(app_py)
            except Exception as e:
                error = e
        
        import_thread = threading.Thread(target=do_import, daemon=True)
        import_thread.start()
        import_thread.join(timeout=30)
        
        if import_thread.is_alive():
            print("[DEBUG] ✗ Phase 1 TIMEOUT: app.py import took too long", flush=True)
            return None
        
        if error:
            print(f"[DEBUG] ✗ Phase 1 FAILED: {error}", flush=True)
            traceback.print_exc()
            return None
        
        print("[DEBUG] ✓ Phase 1 completed - app.py imported", flush=True)
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 1 FAILED: {e}", flush=True)
        traceback.print_exc()
        return None
    
    try:
        print("[DEBUG] Phase 2: Get Flask app instance", flush=True)
        flask_app = app_py.app
        print(f"[DEBUG] ✓ Phase 2 completed - Flask app: {flask_app}", flush=True)
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 2 FAILED: {e}", flush=True)
        traceback.print_exc()
        return None
    
    return flask_app, app_py

def run_debug():
    result = debug_initialize()
    if result is None:
        return
    
    flask_app, app_py = result
    
    try:
        print("[DEBUG] Phase 3: Run full initialization")
        from app import run_full_initialization
        print("[DEBUG] ✓ Phase 3a: run_full_initialization imported")
        
        init_results, flask_app = run_full_initialization(flask_app)
        print(f"[DEBUG] ✓ Phase 3 completed - initialization results: {init_results}")
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 3 FAILED: {e}")
        traceback.print_exc()
        return
    
    try:
        print("[DEBUG] Phase 4: Starting Flask server on port 8889...")
        flask_app.run(host='0.0.0.0', port=8889, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 4 FAILED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()