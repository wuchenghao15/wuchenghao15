#!/usr/bin/env python3
"""
Simple run script for MTSCOS AI Project

import sys
import os

# Set the app directory as the working directory
app_dir = os.path.abspath('.')
os.chdir(app_dir)

# Add the app directory to the Python path
sys.path.insert(0, app_dir)

# Set Flask environment variables
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'

# Import and run the app
from app import app

if __name__ == '__main__':
    print("Starting MTSCOS AI Project server...")
    print(f"Environment: {os.environ.get('FLASK_ENV')}")
    print(f"App: {os.environ.get('FLASK_APP')}")

    try:
        # Try running on port 8888 first
        app.run(host='127.0.0.1', port=8888, debug=True, use_reloader=False)
    except OSError as e:
        print(f"Error running on port 8888: {e}")
        print("Trying port 8080...")
        # Fallback to port 8080 if 8888 is in use
        app.run(host='127.0.0.1', port=8080, debug=True, use_reloader=False)

"""