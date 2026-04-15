#!/usr/bin/env python3
"""
Simple start script for MTSCOS AI Project
Bypasses problematic configuration loading
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables to avoid loading dotenv
os.environ['FLASK_SKIP_DOTENV'] = '1'
os.environ['FLASK_ENV'] = 'development'

# Import only what we need from flask
from flask import Flask

# Create a minimal Flask app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key'

# Add a simple route
@app.route('/')
def index():
    return "MTSCOS AI Project is running!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    print("Starting MTSCOS AI Project on port 8888...")
    print("Access at: http://localhost:8888")
    print("Health check: http://localhost:8888/health")
    app.run(host='0.0.0.0', port=8888, debug=True)