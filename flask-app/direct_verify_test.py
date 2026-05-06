#!/usr/bin/env python3
"""
Test script that directly calls User.verify_credentials

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the User model
try:
    from app.models.user import User
    print("✅ Successfully imported User model")
except Exception as e:
    print(f"❌ Failed to import User model: {str(e)}")
    sys.exit(1)

# Test the verify_credentials method directly
username = "wuchenghao15"
password = "LoginMe.1988"

print("\nTesting User.verify_credentials directly")
print("=" * 50)
print(f"Username: {username}")
print(f"Password: {password}")

# Call the method
try:
    print(f"\n✅ Verification result: {'Success' if user else 'Failed'}")
    if user:
        print(f"✅ User found: {user.username}, Role: {user.role}")
    else:
        print("❌ User not found or password incorrect")
except Exception as e:
    print(f"\n❌ Error during verification: {str(e)}")
    traceback.print_exc()

"""