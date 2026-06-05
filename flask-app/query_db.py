#!/usr/bin/env python3
"""Detailed query of the database"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'app.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n🔍 AI Employees:")
cursor.execute("SELECT * FROM ai_employees")
employees = cursor.fetchall()
for emp in employees:
    print(f"  ID: {emp[0]}")
    print(f"  Name: {emp[1]}")
    print(f"  ...")

print("\n📋 Issue Tracking:")
cursor.execute("SELECT * FROM issue_tracking")
issues = cursor.fetchall()
for issue in issues:
    print(f"  {issue}")

print("\n✅ Query complete!")
conn.close()
