#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing app...")
    import app
    print("App imported successfully")
    
    print("Getting Flask app instance...")
    flask_app = app.app
    print(f"Flask app: {flask_app}")
    
    print("Starting server on port 8888...")
    flask_app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()