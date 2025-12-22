#!/usr/bin/env python3
"""
CLI tool for importing Excel data directly to the database.
Much faster than GUI upload as it bypasses HTTP overhead.

Usage:
    python import_data.py /path/to/your/file.xlsx
    python import_data.py /path/to/your/file.xlsx --user-id 1
    python import_data.py /path/to/your/file.xlsx --dry-run
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, date
import pandas as pd
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.db.models import (
    StorageSystem, StoragePool, CapacityVolume, CapacityHost,
    CapacityDisk, Department, UploadLog, User
)
from app.utils.processing import (
    process_dataframe, insert_data_with_duplicate_check,
    SHEET_MODEL_MAP
)
from app.core.config import settings


def get_or_create_cli_user(db: Session):
    """Get or create a CLI user for imports."""
    cli_user = db.query(User).filter(User.username == 'cli_import').first()
    if not cli_user:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        cli_user = User(
            username='cli_import',
            email='cli@system.local',
            first_name='CLI',
            last_name='Import',
            password_hash=pwd_context.hash('cli_import_system'),
            role='admin',
            status='active'
        )
        db.add(cli_user)
        db.commit()
        db.refresh(cli_user)
    return cli_user


def import_excel_file(file_path: str, user_id: int = None, dry_run: bool = False):
    """
    Import Excel file directly to database.
    
    Args:
        file_path: Path to Excel file
        user_id: User ID for upload log (default: CLI user)
        dry_run: If True, process data but don't commit to database
    """
    start_time = datetime.utcnow()
    
    # Validate file
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return False
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        print(f"❌ Error: File must be .xlsx or .xls format")
        return False
    
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"\n{'='*70}")
    print(f"📊 OneIT SAN Analytics - CLI Data Import")
    print(f"{'='*70}")
    print(f"File: {file_name}")
    print(f"Size: {file_size / (1024*1024):.2f} MB")
    print(f"Mode: {'DRY RUN (no database changes)' if dry_run else 'LIVE IMPORT'}")
    print(f"{'='*70}\n")
    
    db = SessionLocal()
    
    try:
        # Get or create user
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"❌ Error: User ID {user_id} not found")
                return False
        else:
            user = get_or_create_cli_user(db)
        
        print(f"👤 Import User: {user.username} (ID: {user.id})\n")
        
        # Read Excel file
        print("📖 Reading Excel file...")
        try:
            sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
        except Exception as e:
            print(f"❌ Error reading Excel file: {str(e)}")
            return False
        
        print(f"✅ Found {len(sheets)} sheets: {list(sheets.keys())}\n")
        
        # Extract report date from first sheet
        report_date = date.today()
        first_sheet = next(iter(sheets.values()))
        if 'Report_Date' in first_sheet.columns and not first_sheet['Report_Date'].empty:
            try:
                report_date_value = pd.to_datetime(first_sheet['Report_Date'].iloc[0])
                report_date = report_date_value.date()
                print(f"📅 Report Date: {report_date} (from Excel)")
            except:
                print(f"📅 Report Date: {report_date} (default - today)")
        else:
            print(f"📅 Report Date: {report_date} (default - today)")
        
        # Create upload log
        if not dry_run:
            upload_log = UploadLog(
                user_id=user.id,
                file_name=file_name,
                file_size=file_size,
                upload_date=datetime.utcnow(),
                status='processing',
                report_date=report_date
            )
            db.add(upload_log)
            db.commit()
            db.refresh(upload_log)
            upload_id = upload_log.id
            print(f"📝 Upload Log ID: {upload_id}\n")
        else:
            upload_id = None
            print(f"📝 Upload Log: Skipped (dry run)\n")
        
        # Process each sheet
        total_added = 0
        total_duplicates = 0
        total_filtered = 0
        sheet_stats = {}
        
        expected_sheets = ['Storage_Systems', 'Storage_Pools', 'Capacity_Volumes',
                          'Capacity_Hosts', 'Capacity_Disks', 'Departments']
        
        print("🔄 Processing sheets...\n")
        
        for sheet_name in expected_sheets:
            if sheet_name not in sheets:
                print(f"⚠️  Skipping {sheet_name}: Sheet not found")
                continue
            
            df = sheets[sheet_name]
            if df.empty:
                print(f"⚠️  Skipping {sheet_name}: Empty sheet")
                continue
            
            model_class = SHEET_MODEL_MAP.get(sheet_name)
            if not model_class:
                print(f"⚠️  Skipping {sheet_name}: No model mapping")
                continue
            
            print(f"📋 Processing {sheet_name}...")
            print(f"   Raw rows: {len(df)}")
            
            # Process dataframe
            try:
                processed_df = process_dataframe(df, model_class, report_date)
                records = processed_df.to_dict('records')
                
                # Add upload_id to each record
                if upload_id:
                    for record in records:
                        record['upload_id'] = upload_id
                
                print(f"   Processed: {len(records)} records")
                
                # Handle foreign keys for child tables
                if sheet_name in ['Storage_Pools', 'Capacity_Volumes', 'Capacity_Disks']:
                    # Get system_id_map
                    systems = db.query(StorageSystem).filter(
                        StorageSystem.report_date == report_date
                    ).all()
                    system_id_map = {s.name: s.id for s in systems}
                    
                    # Resolve foreign keys
                    valid_records = []
                    filtered_count = 0
                    for record in records:
                        system_name = record.get('storage_system_name')
                        if system_name and system_name in system_id_map:
                            record['storage_system_id'] = system_id_map[system_name]
                            valid_records.append(record)
                        else:
                            filtered_count += 1
                    
                    records = valid_records
                    if filtered_count > 0:
                        print(f"   Filtered: {filtered_count} records (no matching storage system)")
                        total_filtered += filtered_count
                
                # Insert into database
                if not dry_run and records:
                    # Define unique keys for duplicate detection
                    unique_keys_map = {
                        'Storage_Systems': ['report_date', 'name'],
                        'Storage_Pools': ['report_date', 'name', 'storage_system_name'],
                        'Capacity_Volumes': ['report_date', 'name', 'storage_system_name', 'pool'],
                        'Capacity_Hosts': ['report_date', 'name'],
                        'Capacity_Disks': ['report_date', 'name', 'storage_system_name', 'pool'],
                        'Departments': ['report_date', 'name'],
                    }
                    
                    unique_keys = unique_keys_map.get(sheet_name, ['report_date', 'name'])
                    
                    rows_added, duplicates_skipped, _ = insert_data_with_duplicate_check(
                        db, model_class, records, unique_keys
                    )
                    
                    db.flush()
                    
                    print(f"   ✅ Added: {rows_added}")
                    if duplicates_skipped > 0:
                        print(f"   ⏭️  Skipped: {duplicates_skipped} (duplicates)")
                    
                    total_added += rows_added
                    total_duplicates += duplicates_skipped
                    sheet_stats[sheet_name] = {
                        'added': rows_added,
                        'duplicates': duplicates_skipped,
                        'filtered': filtered_count
                    }
                else:
                    print(f"   ℹ️  Would add: {len(records)} records")
                    sheet_stats[sheet_name] = {
                        'would_add': len(records)
                    }
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}\n")
                if not dry_run:
                    db.rollback()
                continue
        
        # Commit transaction
        if not dry_run:
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            upload_log.status = 'completed'
            upload_log.rows_added = total_added
            upload_log.duplicates_skipped = total_duplicates
            upload_log.duration_seconds = duration
            
            db.commit()
            
            print(f"{'='*70}")
            print(f"✅ Import Completed Successfully!")
            print(f"{'='*70}")
            print(f"Total Records Added: {total_added}")
            print(f"Duplicates Skipped: {total_duplicates}")
            print(f"Invalid/Filtered: {total_filtered}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Upload Log ID: {upload_id}")
            print(f"{'='*70}\n")
            
        else:
            db.rollback()
            print(f"{'='*70}")
            print(f"✅ Dry Run Completed - No Changes Made")
            print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        if not dry_run:
            db.rollback()
        return False
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Import Excel data directly to OneIT SAN Analytics database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import file with CLI user
  python import_data.py /path/to/data.xlsx
  
  # Import with specific user ID
  python import_data.py /path/to/data.xlsx --user-id 1
  
  # Dry run (validate without importing)
  python import_data.py /path/to/data.xlsx --dry-run
  
  # Combine options
  python import_data.py /path/to/data.xlsx --user-id 2 --dry-run
        """
    )
    
    parser.add_argument('file', help='Path to Excel file (.xlsx or .xls)')
    parser.add_argument('--user-id', type=int, help='User ID for upload log (default: CLI user)')
    parser.add_argument('--dry-run', action='store_true', help='Validate data without importing')
    
    args = parser.parse_args()
    
    success = import_excel_file(args.file, args.user_id, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
