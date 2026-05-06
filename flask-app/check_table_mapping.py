#!/usr/bin/env python3
from app.utils.table_encryption import table_encryption

# 检查表名映射
print("表名映射:")
for original, encrypted in table_encryption.table_mapping.items():
    print(f"{original} -> {encrypted}")

# 检查questions表的加密名称
questions_encrypted = table_encryption.encrypt_table_name('questions')
print(f"\nquestions表加密后: {questions_encrypted}")
