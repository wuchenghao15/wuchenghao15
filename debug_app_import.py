#!/usr/bin/env python3
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[DEBUG] Loading smart_db_router...", flush=True)
import smart_db_router

print("[DEBUG] Reading app.py lines...", flush=True)
app_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
with open(app_py_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[DEBUG] app.py has {len(lines)} lines", flush=True)

print("[DEBUG] Creating module spec...", flush=True)
import importlib.util
spec = importlib.util.spec_from_file_location("app_py_debug", app_py_path)
app_py = importlib.util.module_from_spec(spec)

print("[DEBUG] Setting up custom loader...", flush=True)

class DebugLoader:
    def __init__(self, original_loader):
        self.original_loader = original_loader
    
    def exec_module(self, module):
        print("[DEBUG] Starting exec_module...", flush=True)
        try:
            self.original_loader.exec_module(module)
            print("[DEBUG] exec_module completed!", flush=True)
        except Exception as e:
            print(f"[DEBUG] exec_module ERROR: {e}", flush=True)
            traceback.print_exc()

spec.loader = DebugLoader(spec.loader)

print("[DEBUG] Executing app.py...", flush=True)
start_time = time.time()
try:
    spec.loader.exec_module(app_py)
    elapsed = time.time() - start_time
    print(f"[DEBUG] app.py executed in {elapsed:.2f}s", flush=True)
except Exception as e:
    elapsed = time.time() - start_time
    print(f"[DEBUG] ERROR after {elapsed:.2f}s: {e}", flush=True)
    traceback.print_exc()