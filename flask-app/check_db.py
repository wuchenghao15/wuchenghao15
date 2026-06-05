#!/usr/bin/env python3
"""Check existing database structure"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
    print("Looking in app/ directory...")
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'app.db')

print(f"Checking database at: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n📊 Existing tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"    {col[1]} ({col[2]})")

print("\n✅ Check complete!")

conn.close()
