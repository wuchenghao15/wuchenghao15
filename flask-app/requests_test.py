#!/usr/bin/env python3
"""
Test script using requests library to test the login endpoint
"""

import requests

# Test the login endpoint
url = "http://localhost:8888/auth/login"
payload = {
    "username": "wuchenghao15",
    "password": "LoginMe.1988"
}

print(f"Testing login at: {url}")
print(f"Payload: {payload}")
print("=" * 50)

# Send a POST request with form data
try:
    response = requests.post(url, data=payload)
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")
    print(f"Response headers: {dict(response.headers)}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed")
