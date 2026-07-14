import sys
sys.path.insert(0, '.')

import os
import time

print(f"[DEBUG] Starting debug initialization...")
print(f"[DEBUG] PID: {os.getpid()}")

start_time = time.time()

try:
    print(f"[DEBUG] Step 1: Importing from app.__init__...")
    from app.__init__ import run_full_initialization
    
    print(f"[DEBUG] Step 2: Importing Flask app...")
    from app import app
    
    print(f"[DEBUG] Step 3: Calling run_full_initialization...")
    init_start = time.time()
    init_results, app = run_full_initialization(app)
    init_time = time.time() - init_start
    
    print(f"[DEBUG] Step 4: Initialization completed in {init_time:.2f}s")
    
    print(f"[DEBUG] Step 5: Starting server on port 8888...")
    app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"[DEBUG ERROR] {e}")
    import traceback
    traceback.print_exc()
    print(f"[DEBUG] Time elapsed: {time.time() - start_time:.2f}s")
