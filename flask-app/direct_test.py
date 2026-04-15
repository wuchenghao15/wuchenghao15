#!/usr/bin/env python3
"""
Direct test of the verify_password function with debug logging
"""

import logging
import sys
import os

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from app.utils.security import security_utils

# Test with the exact password hash from the database
stored_password = "0198ffaa5d35ecdbd7306ddb67f8433999cc07e3b383fb9c57eab7f51dca5ccff597394b93bd09ebbd5336d98bc25f50"
provided_password = "LoginMe.1988"

print(f"Testing password verification directly")
print(f"Stored password: {stored_password}")
print(f"Provided password: {provided_password}")
print(f"Password length: {len(stored_password)}")
print("=" * 60)

# Test the verify_password function directly
result = security_utils.verify_password(stored_password, provided_password)
print(f"\nFinal result: {result}")
