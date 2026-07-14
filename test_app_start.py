#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Step 1: Import smart_db_router_simple", flush=True)
import smart_db_router_simple

print("Step 2: Import app.py directly", flush=True)
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
app_module = importlib.util.module_from_spec(spec)

print("Step 3: Execute app.py", flush=True)
spec.loader.exec_module(app_module)

print("Step 4: Get Flask app", flush=True)
flask_app = app_module.app
print(f"Flask app: {flask_app}", flush=True)

print("Step 5: Start server", flush=True)
flask_app.run(host='0.0.0.0', port=8889, debug=False, use_reloader=False)