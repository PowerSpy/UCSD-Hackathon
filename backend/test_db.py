#!/usr/bin/env python3
"""Test script to verify lesson_history table exists and can be queried."""

import sys
from sqlalchemy import text
from app.database import engine, Base
from app.models import LessonHistory, LessonSession

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# Check if lesson_history table exists
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='lesson_history'")
    )
    if result.fetchone():
        print("✓ lesson_history table exists")
    else:
        print("✗ lesson_history table does NOT exist")
        print("\nAvailable tables:")
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        for row in result:
            print(f"  - {row[0]}")

# Check table schema
print("\nlesson_history schema:")
with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(lesson_history)"))
    for row in result:
        print(f"  {row[1]}: {row[2]}")

print("\nTest complete!")
