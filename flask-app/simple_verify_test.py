#!/usr/bin/env python3
"""
Simple test of the verify_password function with exact values
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the security utils
from app.utils.security import security_utils

# Test with the exact values
stored_password = "0198ffaa5d35ecdbd7306ddb67f8433999cc07e3b383fb9c57eab7f51dca5ccff597394b93bd09ebbd5336d98bc25f50"
provided_password = "LoginMe.1988"

print(f"Testing verify_password function directly")
print(f"Stored password: {stored_password}")
print(f"Provided password: {provided_password}")
print(f"Password length: {len(stored_password)}")
print("=" * 60)

# Call the verify_password function
try:
    result = security_utils.verify_password(stored_password, provided_password)
    print(f"\n✓ Verification result: {result}")
    if result:
        print("✅ Login should now work!")
    else:
        print("❌ Login still fails")
except Exception as e:
    print(f"\n❌ Error during verification: {str(e)}")
    import traceback
    traceback.print_exc()
