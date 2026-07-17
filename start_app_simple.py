#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(f"[START] Loading smart_db_router...", flush=True)
import smart_db_router

print(f"[START] Importing app.py...", flush=True)
start_time = time.time()

import importlib.util
spec = importlib.util.spec_from_file_location("app_py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
app_py = importlib.util.module_from_spec(spec)

print(f"[START] Executing app.py...", flush=True)
spec.loader.exec_module(app_py)

import_time = time.time() - start_time
print(f"[START] app.py loaded in {import_time:.2f}s", flush=True)

print(f"[START] Getting Flask app...", flush=True)
flask_app = app_py.app
print(f"[START] Flask app: {flask_app}", flush=True)

print(f"[START] Starting server on port 8889...", flush=True)
flask_app.run(host='0.0.0.0', port=8889, debug=False, use_reloader=False)