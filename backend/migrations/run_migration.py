#!/usr/bin/env python3
"""
Migration script: Add used_capacity_gib column to capacity_disks table
Run this script to apply the database migration.

Usage:
    python migrations/run_migration.py
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import engine
from sqlalchemy import text


def run_migration():
    """Apply migration to add used_capacity_gib column."""
    
    print("=" * 60)
    print("MIGRATION: Add used_capacity_gib to capacity_disks")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if column already exists
            print("\n1. Checking if column already exists...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'capacity_disks' 
                AND column_name = 'used_capacity_gib'
            """))
            
            if result.fetchone():
                print("   ✓ Column 'used_capacity_gib' already exists. Skipping migration.")
                trans.rollback()
                return
            
            # Add the column
            print("\n2. Adding column 'used_capacity_gib' to capacity_disks...")
            conn.execute(text("""
                ALTER TABLE capacity_disks 
                ADD COLUMN used_capacity_gib FLOAT NULL
            """))
            print("   ✓ Column added successfully")
            
            # Calculate values for existing records
            print("\n3. Calculating values for existing records...")
            result = conn.execute(text("""
                UPDATE capacity_disks 
                SET used_capacity_gib = capacity_gib - available_capacity_gib
                WHERE capacity_gib IS NOT NULL 
                  AND available_capacity_gib IS NOT NULL
            """))
            rows_updated = result.rowcount
            print(f"   ✓ Updated {rows_updated} existing records")
            
            # Commit transaction
            trans.commit()
            print("\n" + "=" * 60)
            print("✓ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            trans.rollback()
            raise


if __name__ == '__main__':
    try:
        run_migration()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ MIGRATION FAILED: {e}")
        sys.exit(1)
