#!/usr/bin/env python3
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_initialize():
    print("[DEBUG] Starting app.py initialization debug...")
    
    try:
        print("[DEBUG] Phase 1: Import app.py directly")
        import importlib.util
        spec = importlib.util.spec_from_file_location("app_py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
        app_py = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_py)
        print("[DEBUG] ✓ Phase 1 completed - app.py imported")
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 1 FAILED: {e}")
        traceback.print_exc()
        return None
    
    try:
        print("[DEBUG] Phase 2: Get Flask app instance")
        flask_app = app_py.app
        print(f"[DEBUG] ✓ Phase 2 completed - Flask app: {flask_app}")
    except Exception as e:
        print(f"[DEBUG] ✗ Phase 2 FAILED: {e}")
        traceback.print_exc()
        return None
    
    return flask_app

def run_debug():
    flask_app = debug_initialize()
    if flask_app:
        print("[DEBUG] Starting Flask server on port 8889...")
        flask_app.run(host='0.0.0.0', port=8889, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_debug()