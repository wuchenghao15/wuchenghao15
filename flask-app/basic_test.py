#!/usr/bin/env python3
"""
Basic Flask Test Script

from flask import Flask

# Create a simple Flask app
app = Flask(__name__)

# Add a simple route
@app.route('/')
def hello():
    return "Hello, MTSCOS AI Project!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    print("Starting basic Flask server on port 8888...")
    app.run(host='0.0.0.0', port=8888, debug=True)

"""