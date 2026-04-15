#!/usr/bin/env python3
"""
Super simple password verification test
"""

import hashlib

# Exact values from the database
stored_hash = "0198ffaa5d35ecdbd7306ddb67f8433999cc07e3b383fb9c57eab7f51dca5ccff597394b93bd09ebbd5336d98bc25f50"
provided_password = "LoginMe.1988"

print("Super simple password verification test")
print("=" * 50)
print(f"Stored hash: {stored_hash}")
print(f"Provided password: {provided_password}")
print(f"Hash length: {len(stored_hash)}")

# Extract salt and hash
salt_hex = stored_hash[:32]  # 16 bytes = 32 hex characters
hash_hex = stored_hash[32:]  # 32 bytes = 64 hex characters

print(f"\nExtracted:")
print(f"  Salt hex: {salt_hex}")
print(f"  Hash hex: {hash_hex}")

# Convert to bytes
salt = bytes.fromhex(salt_hex)
stored_hashed_bytes = bytes.fromhex(hash_hex)

print(f"  Salt bytes length: {len(salt)} bytes")
print(f"  Stored hash bytes length: {len(stored_hashed_bytes)} bytes")

# Compute hash with the same parameters
computed_hashed_bytes = hashlib.pbkdf2_hmac(
    'sha256',
    provided_password.encode('utf-8'),
    salt,
    100000
)

print(f"  Computed hash bytes length: {len(computed_hashed_bytes)} bytes")
print(f"  Computed hash hex: {computed_hashed_bytes.hex()}")

# Compare
result = computed_hashed_bytes == stored_hashed_bytes
print(f"\n✅ Match: {result}")

if result:
    print("\n🎉 Password verification works correctly!")
    print("The issue must be in the integration or logging.")
else:
    print("\n❌ Password verification fails.")
