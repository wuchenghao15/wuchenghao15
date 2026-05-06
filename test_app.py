#!/usr/bin/env python3
"""
Test script to start the app with minimal initialization

import os
import sys
import flask

# Disable dotenv loading to avoid timeout issues
os.environ['FLASK_SKIP_DOTENV'] = '1'

# Add the flask-app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask-app'))

# Create a minimal Flask app
app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key-for-testing'

@app.route('/')
def index():
    return "MTSCOS AI Project - Running on port 8888"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    print("[INFO] Starting minimal app on port 8888...")
    app.run(host='0.0.0.0', port=8888, debug=True, use_reloader=False)

"""