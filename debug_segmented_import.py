#!/usr/bin/env python3
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[DEBUG] Loading smart_db_router...", flush=True)
import smart_db_router

app_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
with open(app_py_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[DEBUG] app.py has {len(lines)} lines", flush=True)

segments = [
    (1, 50),     # Basic imports and Flask app creation
    (50, 150),   # CORS, static routes, security headers
    (150, 300),  # Database helpers, subject maps
    (300, 650),  # Subject tree and AI test subjects
    (650, 1300), # First batch of functions
    (1300, 2500),# Second batch
    (2500, 4000),# Third batch
    (4000, 6000),# Fourth batch
    (6000, 8000),# Fifth batch (includes init_points_tables)
    (8000, 10000),# Sixth batch
    (10000, 12000),# Seventh batch
    (12000, 14000),# Eighth batch
    (14000, 16000),# Ninth batch
    (16000, 17900),# Tenth batch (includes if __name__ block)
]

import importlib.util
spec = importlib.util.spec_from_file_location("app_py_debug", app_py_path)
app_py = importlib.util.module_from_spec(spec)

sys.modules['app_py_debug'] = app_py

app_py.__dict__['__name__'] = 'app_py_debug'
app_py.__dict__['__file__'] = app_py_path

for start, end in segments:
    segment_lines = lines[start-1:end]
    segment_code = ''.join(segment_lines)
    
    print(f"[DEBUG] Executing lines {start}-{end}...", flush=True)
    start_time = time.time()
    
    try:
        exec(segment_code, app_py.__dict__)
        elapsed = time.time() - start_time
        print(f"[DEBUG] ✓ Lines {start}-{end} completed in {elapsed:.2f}s", flush=True)
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[DEBUG] ✗ Lines {start}-{end} FAILED after {elapsed:.2f}s: {e}", flush=True)
        traceback.print_exc()
        break