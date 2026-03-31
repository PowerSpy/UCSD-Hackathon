#!/usr/bin/env python3
"""Test script to check if lesson_history has data."""

from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

try:
    # Check row count
    result = db.execute(text("SELECT COUNT(*) FROM lesson_history"))
    count = result.scalar()
    print(f"Total records in lesson_history: {count}")
    
    if count > 0:
        print("\nRecent entries:")
        result = db.execute(
            text("SELECT session_id, section_index, section_name, subsection_name FROM lesson_history ORDER BY created_at DESC LIMIT 5")
        )
        for row in result:
            print(f"  Session: {row[0]}, Index: {row[1]}, Section: {row[2]}, Subsection: {row[3]}")
    else:
        print("No data in lesson_history yet - have you called /lesson/generate?")
finally:
    db.close()
