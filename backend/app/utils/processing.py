"""
Data processing utilities for Excel parsing, calculations, and transformations.
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import io

from app.db.models import (
    StorageSystem, StoragePool, CapacityVolume,
    CapacityHost, CapacityDisk, Department, Alert
)


# Sheet name to model mapping
SHEET_MODEL_MAP = {
    'Storage_Systems': StorageSystem,
    'Storage_Pools': StoragePool,
    'Capacity_Volumes': CapacityVolume,
    'Capacity_Hosts': CapacityHost,
    'Capacity_Disks': CapacityDisk,
    'Departments': Department,
}

# Required sheets for validation
REQUIRED_SHEETS = list(SHEET_MODEL_MAP.keys())


def bytes_to_gib(bytes_val: float) -> float:
    """Convert bytes to GiB."""
    if pd.isna(bytes_val):
        return 0.0
    return bytes_val / (1024 ** 3)


def gib_to_tb(gib_val: float) -> float:
    """Convert GiB to TB."""
    if pd.isna(gib_val):
        return 0.0
    return gib_val / 1024


def tb_to_gib(tb_val: float) -> float:
    """Convert TB to GiB."""
    if pd.isna(tb_val):
        return 0.0
    return tb_val * 1024


def calculate_utilization_pct(used: float, total: float) -> float:
    """Calculate utilization percentage safely."""
    if pd.isna(used) or pd.isna(total) or total == 0:
        return 0.0
    return round((used / total) * 100, 2)


def calculate_days_until_full(
    current_pct: float,
    growth_rate_gib: Optional[float] = None,
    total_capacity_gib: Optional[float] = None
) -> int:
    """
    Calculate estimated days until storage is full.
    Uses different growth rates based on current utilization.
    """
    if pd.isna(current_pct) or current_pct >= 100:
        return 0
    
    # Determine daily growth percentage based on utilization
    if current_pct > 95:
        daily_growth_pct = 2.0  # Aggressive growth when critical
    elif current_pct > 80:
        daily_growth_pct = 1.5  # Moderate growth when high
    else:
        daily_growth_pct = 1.0  # Normal growth
    
    # If we have actual growth rate data, use it
    if growth_rate_gib is not None and total_capacity_gib is not None and total_capacity_gib > 0:
        # Calculate actual daily growth percentage
        actual_daily_pct = (growth_rate_gib / total_capacity_gib) * 100
        if actual_daily_pct > 0:
            daily_growth_pct = max(actual_daily_pct, 0.1)  # Minimum 0.1%
    
    remaining_pct = 100 - current_pct
    days = remaining_pct / daily_growth_pct
    
    return max(0, int(days))


def get_alert_level(utilization_pct: float) -> Optional[str]:
    """Determine alert level based on utilization percentage."""
    if utilization_pct >= 100:
        return 'emergency'
    elif utilization_pct >= 98:
        return 'critical'
    elif utilization_pct >= 90:
        return 'warning'
    return None


def clean_column_name(col: str) -> str:
    """Clean and normalize column names."""
    # Convert to lowercase and replace spaces/special chars with underscore
    clean = col.lower().strip()
    clean = clean.replace(' ', '_').replace('-', '_').replace('.', '_')
    clean = clean.replace('(', '').replace(')', '').replace('%', 'pct')
    clean = clean.replace('/', '_')
    # Remove consecutive underscores
    while '__' in clean:
        clean = clean.replace('__', '_')
    return clean.strip('_')


def validate_excel_file(file_content: bytes) -> Tuple[bool, List[str], Dict[str, pd.DataFrame]]:
    """
    Validate an Excel file has the required sheets and structure.
    Returns (is_valid, errors, dataframes_dict)
    """
    errors = []
    dataframes = {}
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        sheet_names = excel_file.sheet_names
        
        # Check for required sheets (case-insensitive)
        sheet_name_map = {s.lower(): s for s in sheet_names}
        
        for required in REQUIRED_SHEETS:
            required_lower = required.lower()
            if required_lower not in sheet_name_map:
                errors.append(f"Missing required sheet: {required}")
            else:
                actual_name = sheet_name_map[required_lower]
                try:
                    df = pd.read_excel(excel_file, sheet_name=actual_name)
                    dataframes[required] = df
                except Exception as e:
                    errors.append(f"Error reading sheet {required}: {str(e)}")
        
        is_valid = len(errors) == 0
        return is_valid, errors, dataframes
        
    except Exception as e:
        errors.append(f"Error reading Excel file: {str(e)}")
        return False, errors, {}


def clean_numeric_value(value):
    """
    Clean numeric values from Excel data.
    Handles: '-', 'N/A', empty strings, commas in numbers
    Returns 0.0 for NULL indicators (changed from None)
    """
    if pd.isna(value) or value is None:
        return 0.0
    
    # Convert to string for processing
    str_val = str(value).strip()
    
    # Handle empty, dash, or N/A - convert to 0.0 instead of None
    if str_val in ['', '-', 'N/A', 'n/a', '#N/A', 'null', 'NULL']:
        return 0.0
    
    # Remove commas from numbers like '46,576.00'
    str_val = str_val.replace(',', '')
    
    # Try to convert to float
    try:
        return float(str_val)
    except (ValueError, TypeError):
        # If conversion fails, return 0.0 for numeric fields
        return 0.0


def parse_compression_ratio(value):
    """
    Parse compression ratio from Excel format to float.
    Converts ratio strings like "1.3 : 1" to float value 1.3
    Returns 0.0 for NULL indicators (changed from None)
    
    Examples:
        "1 : 1" -> 1.0
        "1.3 : 1" -> 1.3
        "2.2 : 1" -> 2.2
        "-" -> 0.0
        "N/A" -> 0.0
        
    Reference: See docs/COMPRESSION_METRICS_DEFINITION.md for full documentation
    """
    if pd.isna(value) or value is None:
        return 0.0
    
    str_val = str(value).strip()
    
    # Handle empty, dash, or N/A - convert to 0.0 instead of None
    if str_val in ['', '-', 'N/A', 'n/a', '#N/A', 'null', 'NULL']:
        return 0.0
    
    # Parse ratio format "X : 1" or "X:1"
    if ':' in str_val:
        parts = str_val.split(':')
        if len(parts) == 2:
            try:
                numerator = float(parts[0].strip())
                return numerator
            except (ValueError, TypeError):
                return 0.0
    
    # Try direct float conversion
    try:
        return float(str_val)
    except (ValueError, TypeError):
        return 0.0


def clean_datetime_value(value):
    """
    Clean datetime values from Excel data.
    Handles: string dates, Excel datetime objects, timestamps
    Returns: datetime object or None
    """
    if pd.isna(value) or value is None:
        return None
    
    # Convert to string for processing
    str_val = str(value).strip()
    
    # Handle empty, dash, or N/A
    if str_val in ['', '-', 'N/A', 'n/a', '#N/A', 'null', 'NULL']:
        return None
    
    # If already a datetime, return it
    if isinstance(value, (datetime, date)):
        return value
    
    # Try to parse string dates like "Jul 13, 2021, 08:34:13" or "Nov 26, 2025, 06:56:38"
    try:
        return pd.to_datetime(str_val)
    except (ValueError, TypeError):
        # If conversion fails, return None
        return None


def normalize_storage_system_name(name):
    """
    Normalize storage system names with specific mappings and pattern-based transformations.
    
    Priority order:
    1. Apply specific hardcoded mappings (for complex transformations)
    2. Apply pattern-based transformations (underscore to hyphen)
    
    Examples:
        Specific mappings:
            FS9500_10.48.1.79 -> FS95K-R1
            Cluster_9.3.118.191 -> FS92K-A1
            FS92K_A1_9.3.118.191 -> FS92K-A1
            megasan18 -> MSAN18
        
        Pattern-based:
            FS92K_A1 -> FS92K-A1
            A9KR_R2 -> A9KR-R2
    
    This ensures consistent naming across all tables and prevents issues
    with underscore vs hyphen variations.
    """
    if pd.isna(name) or name is None:
        return name
    
    str_name = str(name).strip()
    
    # Specific mappings (applied first - highest priority)
    specific_mappings = {
        'FS9500_10.48.1.79': 'FS95K-R1',
        'Cluster_9.3.118.191': 'FS92K-A1',
        'FS92K_A1_9.3.118.191': 'FS92K-A1',
        'megasan18': 'MSAN18',
        # Add more specific mappings here as needed
    }
    
    # Check for specific mapping (case-sensitive)
    if str_name in specific_mappings:
        return specific_mappings[str_name]
    
    # Pattern-based transformation: replace ALL underscores with hyphens
    return str_name.replace('_', '-')


def process_dataframe(df: pd.DataFrame, model_class, report_date: date) -> pd.DataFrame:
    """
    Process a dataframe for database insertion.
    - Clean column names
    - Drop columns with all NULL values
    - Add report_date
    - Handle data type conversions
    - Clean numeric values (handle '-', commas, etc.)
    - Normalize storage system names (replace _ with -)
    """
    # Clean column names
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Drop columns that are 100% NULL
    null_counts = df.isnull().sum()
    cols_to_drop = null_counts[null_counts == len(df)].index.tolist()
    df = df.drop(columns=cols_to_drop)
    
    # Normalize storage system names (replace _ with -) for ALL tables
    storage_name_columns = ['name', 'storage_system_name', 'storage_system', 'system_name']
    for col in storage_name_columns:
        if col in df.columns:
            df[col] = df[col].apply(normalize_storage_system_name)
    
    # Add report_date only if not already present from Excel
    # If report_date exists in Excel, use it; otherwise use the provided report_date parameter
    if 'report_date' not in df.columns:
        df['report_date'] = report_date
    else:
        # Report_Date exists in Excel - clean and validate it
        from sqlalchemy.types import Date
        df['report_date'] = df['report_date'].apply(clean_datetime_value)
        # If any values are None after cleaning, fill with the parameter report_date
        df['report_date'] = df['report_date'].fillna(report_date)
    
    # Handle common column renames
    column_renames = {
        'storage_system': 'storage_system_name',
        'class': 'disk_class',
        'type': 'dept_type' if model_class == Department else 'type',
        'id': 'volume_id' if model_class == CapacityVolume else 'id',
    }
    
    # Special renames for CapacityVolume
    if model_class == CapacityVolume:
        column_renames['capacity_gib'] = 'provisioned_capacity_gib'
        column_renames['name'] = 'volume_name'
        column_renames['pool'] = 'pool_name'
    
    for old_name, new_name in column_renames.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Get model columns and their types
    model_columns = {}
    for c in model_class.__table__.columns:
        if c.name != 'id':
            model_columns[c.name] = c.type
    
    # Keep only columns that exist in the model
    df_columns = [col for col in df.columns if col in model_columns]
    df = df[df_columns]
    
    # Compression ratio columns (require special parsing from "X : 1" format)
    ratio_columns = ['total_compression_ratio', 'pool_compression_ratio', 
                     'data_reduction_ratio', 'drive_compression_ratio']
    
    # Clean numeric and datetime columns
    from sqlalchemy.types import Float, Integer, Numeric, DateTime, Date
    for col in df.columns:
        if col in model_columns:
            col_type = model_columns[col]
            
            # Special handling for compression ratio columns
            if col in ratio_columns and isinstance(col_type, (Float, Numeric)):
                df[col] = df[col].apply(parse_compression_ratio)
            # If column should be numeric (Float, Integer, Numeric)
            elif isinstance(col_type, (Float, Integer, Numeric)):
                df[col] = df[col].apply(clean_numeric_value)
            # If column should be datetime
            elif isinstance(col_type, (DateTime, Date)):
                df[col] = df[col].apply(clean_datetime_value)
    
    # Handle boolean columns
    bool_columns = ['compressed', 'thin_provisioned', 'acknowledged', 'active_quorum', 
                   'zero_capacity', 'solid_state']
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].map({'Yes': True, 'No': False, True: True, False: False})
    
    # Replace NaN with None for database
    df = df.replace({np.nan: None})
    
    return df


def calculate_pool_utilization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate utilization percentage for storage pools.
    
    IMPORTANT: Excel's 'Used Capacity (GiB)' field contains incorrect values (often 0).
    We calculate the correct used capacity from: usable_capacity - available_capacity
    
    Calculated Fields (not from Excel):
    - used_capacity_gib = usable_capacity_gib - available_capacity_gib
    - utilization_pct = (used_capacity_gib / usable_capacity_gib) * 100
    """
    if 'usable_capacity_gib' in df.columns and 'available_capacity_gib' in df.columns:
        # Calculate used_capacity_gib from usable - available (IGNORE Excel value)
        df['used_capacity_gib'] = df.apply(
            lambda row: (row.get('usable_capacity_gib') or 0) - (row.get('available_capacity_gib') or 0),
            axis=1
        )
        
        # Calculate utilization percentage using the calculated used_capacity_gib
        df['utilization_pct'] = df.apply(
            lambda row: calculate_utilization_pct(
                row.get('used_capacity_gib'),
                row.get('usable_capacity_gib')
            ),
            axis=1
        )
    return df


def calculate_disk_used_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate used capacity for capacity disks.
    
    Calculated Field (not from Excel):
    - used_capacity_gib = capacity_gib - available_capacity_gib
    """
    if 'capacity_gib' in df.columns and 'available_capacity_gib' in df.columns:
        # Calculate used_capacity_gib from capacity - available
        df['used_capacity_gib'] = df.apply(
            lambda row: (row.get('capacity_gib') or 0) - (row.get('available_capacity_gib') or 0),
            axis=1
        )
    return df


def calculate_flashsystem_available_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate available_capacity_gib for FlashSystem volumes.
    
    For FlashSystem storage systems (A9K-A1, A9KR-R1, A9KR-R2), the available_capacity_gib
    field is ALWAYS recalculated using the formula:
    available_capacity_gib = provisioned_capacity_gib - used_capacity_gib
    
    This preprocessing applies only to volumes from these specific FlashSystem storage systems.
    Any existing values in the Excel file are overwritten with the calculated value.
    """
    FLASHSYSTEM_NAMES = ['A9K-A1', 'A9KR-R1', 'A9KR-R2']
    
    if 'storage_system_name' not in df.columns:
        return df
    
    if 'provisioned_capacity_gib' not in df.columns or 'used_capacity_gib' not in df.columns:
        return df
    
    # Create a mask for FlashSystem volumes
    flashsystem_mask = df['storage_system_name'].isin(FLASHSYSTEM_NAMES)
    
    # ALWAYS calculate available_capacity_gib for FlashSystem volumes
    # This overwrites any existing values from Excel
    df.loc[flashsystem_mask, 'available_capacity_gib'] = df.loc[flashsystem_mask].apply(
        lambda row: (row.get('provisioned_capacity_gib') or 0) - (row.get('used_capacity_gib') or 0),
        axis=1
    )
    
    return df


def calculate_overhead_used_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate overhead_used_capacity for volumes (excluding FlashSystems).
    
    For non-FlashSystem storage systems, calculate the overhead using the formula:
    overhead_used_capacity = provisioned_capacity_gib - used_capacity_gib - available_capacity_gib
    
    This calculation is NOT applied to FlashSystem storage systems (A9K-A1, A9KR-R1, A9KR-R2).
    
    The overhead represents the difference between provisioned capacity and the sum of 
    used and available capacity, which can indicate system overhead, metadata, or other 
    storage management overhead.
    """
    FLASHSYSTEM_NAMES = ['A9K-A1', 'A9KR-R1', 'A9KR-R2']
    
    if 'storage_system_name' not in df.columns:
        return df
    
    required_columns = ['provisioned_capacity_gib', 'used_capacity_gib', 'available_capacity_gib']
    if not all(col in df.columns for col in required_columns):
        return df
    
    # Create a mask for NON-FlashSystem volumes
    non_flashsystem_mask = ~df['storage_system_name'].isin(FLASHSYSTEM_NAMES)
    
    # Calculate overhead_used_capacity for non-FlashSystem volumes
    df.loc[non_flashsystem_mask, 'overhead_used_capacity'] = df.loc[non_flashsystem_mask].apply(
        lambda row: (row.get('provisioned_capacity_gib') or 0) - 
                    (row.get('used_capacity_gib') or 0) - 
                    (row.get('available_capacity_gib') or 0),
        axis=1
    )
    
    # For FlashSystem volumes, set overhead_used_capacity to None/0
    df.loc[~non_flashsystem_mask, 'overhead_used_capacity'] = 0.0
    
    return df



def aggregate_host_duplicates(records: List[Dict[str, Any]], unique_keys: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Aggregate duplicate host records by summing numeric capacity fields.
    
    For host tables (Capacity_Hosts, Inventory_Hosts), when duplicate hosts exist
    in the same Excel file, combine them into a single row by:
    - Keeping first occurrence's non-numeric fields (condition, status, etc.)
    - Summing all numeric capacity fields (san_capacity_gib, used_san_capacity_gib, etc.)
    
    Example: Host "zpfp18p04" appears twice with 100 GiB and 50 GiB
    Result: Single row with 150 GiB total capacity
    
    Returns (aggregated_records, aggregated_info_list)
    """
    from collections import defaultdict
    
    # Fields to sum (numeric capacity fields)
    sum_fields = [
        'san_capacity_gib',
        'used_san_capacity_gib',
        'primary_provisioned_capacity_gib',
        'primary_used_capacity_gib'
    ]
    
    # Group records by unique key
    grouped = defaultdict(list)
    for record in records:
        # Build unique key tuple
        key_values = tuple(
            (k, str(record.get(k)) if record.get(k) is not None else 'None')
            for k in sorted(unique_keys)
        )
        grouped[key_values].append(record)
    
    # Aggregate duplicates
    aggregated_records = []
    aggregated_info = []
    
    for key_tuple, duplicate_records in grouped.items():
        if len(duplicate_records) == 1:
            # No duplicates, use as-is
            aggregated_records.append(duplicate_records[0])
        else:
            # Duplicates found - aggregate them
            base_record = duplicate_records[0].copy()
            identifier = base_record.get('name', 'Unknown')
            
            # Sum numeric fields from all duplicates
            for field in sum_fields:
                if field in base_record:
                    total = sum(
                        float(rec.get(field) or 0) 
                        for rec in duplicate_records 
                        if rec.get(field) is not None
                    )
                    base_record[field] = total if total > 0 else None
            
            aggregated_records.append(base_record)
            
            # Track aggregation info
            aggregated_info.append({
                'table': 'capacity_hosts',
                'reason': f'aggregated_{len(duplicate_records)}_duplicates',
                'identifier': identifier,
                'full_row': base_record,  # The combined record
                'original_count': len(duplicate_records)
            })
    
    return aggregated_records, aggregated_info


def insert_data_with_duplicate_check(
    db: Session,
    model_class,
    records: List[Dict[str, Any]],
    unique_keys: List[str]
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Insert records into database, handling duplicates appropriately.
    
    For HOST tables (Capacity_Hosts, Inventory_Hosts):
      - Aggregates within-file duplicates by summing capacity fields
      - Example: Two records for "zpfp18p04" with 100GB and 50GB → One record with 150GB
    
    For OTHER tables:
      - Skips within-file duplicates (uses first occurrence)
    
    For ALL tables:
      - Skips database duplicates (from previous uploads)
    
    Returns (rows_added, duplicates_skipped, skipped_records_list)
    """
    rows_added = 0
    duplicates_skipped = 0
    skipped_records = []
    
    # Check if this is a host table that needs aggregation
    table_name = model_class.__tablename__ if hasattr(model_class, '__tablename__') else ''
    is_host_table = table_name in ['capacity_hosts']
    
    # For host tables, aggregate duplicates first
    if is_host_table:
        original_count = len(records)
        records, aggregated_info = aggregate_host_duplicates(records, unique_keys)
        aggregated_count = original_count - len(records)
        if aggregated_count > 0:
            print(f"Aggregated {aggregated_count} duplicate host records into {len(records)} unique hosts")
            # Add aggregated records to skipped list so users can see what was combined
            skipped_records.extend(aggregated_info)
    
    # Track records added in this session to prevent within-file duplicates
    session_keys_seen = set()
    
    for record in records:
        # Build filter for duplicate check
        filters = {key: record.get(key) for key in unique_keys if key in record}
        
        # Create a hashable tuple of unique key values for within-file duplicate check
        # Handle None values by converting to string 'None'
        key_tuple = tuple(
            (k, str(v) if v is not None else 'None') 
            for k, v in sorted(filters.items())
        )
        
        # Build a readable identifier for the record
        identifier = record.get('volume_name') or record.get('name')
        if not identifier or identifier == 'None':
            # For disks without names, use pool + storage_system
            identifier = f"{record.get('storage_system_name', 'Unknown')}/{record.get('pool_name') or record.get('pool', 'Unknown')}"
        
        # Check for within-file duplicates (should not happen for hosts after aggregation)
        if key_tuple in session_keys_seen:
            duplicates_skipped += 1
            skipped_records.append({
                'table': table_name,
                'reason': 'within_file_duplicate',
                'identifier': identifier,
                'full_row': record  # Store complete row data
            })
            continue
        
        # Check if record already exists in database
        existing = db.query(model_class).filter_by(**filters).first()
        
        if existing:
            duplicates_skipped += 1
            skipped_records.append({
                'table': table_name,
                'reason': 'already_exists_in_db',
                'identifier': identifier,
                'full_row': record  # Store complete row data
            })
        else:
            try:
                db_record = model_class(**record)
                db.add(db_record)
                session_keys_seen.add(key_tuple)  # Track this record in current session
                rows_added += 1
            except Exception as e:
                print(f"Error inserting record: {e}")
                duplicates_skipped += 1
                skipped_records.append({
                    'table': table_name,
                    'reason': f'insert_error: {str(e)}',
                    'identifier': identifier,
                    'full_row': record  # Store complete row data
                })
    
    return rows_added, duplicates_skipped, skipped_records


def generate_alerts_from_pools(db: Session, report_date: date) -> List[Alert]:
    """
    Generate alerts for pools that exceed utilization thresholds.
    """
    alerts = []
    
    # Query pools from latest report date
    pools = db.query(StoragePool).filter(
        StoragePool.report_date == report_date
    ).all()
    
    for pool in pools:
        if pool.utilization_pct is None:
            continue
        
        level = get_alert_level(pool.utilization_pct)
        if level:
            days = calculate_days_until_full(
                pool.utilization_pct,
                pool.recent_growth_gib,
                pool.usable_capacity_gib
            )
            
            message = f"Pool '{pool.name}' on system '{pool.storage_system_name}' "
            message += f"is at {pool.utilization_pct:.1f}% utilization. "
            
            if days > 0:
                message += f"Estimated {days} days until full."
            else:
                message += "Immediate action required!"
            
            alert = Alert(
                pool_name=pool.name,
                storage_system=pool.storage_system_name,
                utilization_pct=pool.utilization_pct,
                level=level,
                message=message,
                days_until_full=days,
                acknowledged=False
            )
            alerts.append(alert)
    
    return alerts


def get_overview_kpis(db: Session, report_date: date, tenant_ids: Optional[List[int]] = None) -> Dict:
    """
    Calculate KPI metrics for the overview dashboard.
    """
    # Get latest systems
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()
    
    total_capacity = sum(s.usable_capacity_gib or 0 for s in systems)
    available_capacity = sum(s.available_capacity_gib or 0 for s in systems)
    used_capacity = total_capacity - available_capacity
    
    utilization = calculate_utilization_pct(used_capacity, total_capacity)
    
    # Get compression ratio average
    compression_ratios = [s.total_compression_ratio for s in systems if s.total_compression_ratio]
    avg_compression = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 1.0
    
    # Get data reduction
    data_reduction = sum(s.data_reduction_gib or 0 for s in systems)
    
    # Get counts
    total_pools = sum(s.pools or 0 for s in systems)
    total_volumes = sum(s.volumes or 0 for s in systems)
    
    # Get hosts count
    hosts_count = db.query(func.count(CapacityHost.id)).filter(
        CapacityHost.report_date == report_date
    ).scalar() or 0
    
    return {
        'total_capacity_tb': gib_to_tb(total_capacity),
        'used_capacity_tb': gib_to_tb(used_capacity),
        'available_capacity_tb': gib_to_tb(available_capacity),
        'utilization_pct': utilization,
        'total_systems': len(systems),
        'total_pools': total_pools,
        'total_volumes': total_volumes,
        'total_hosts': hosts_count,
        'compression_ratio': round(avg_compression, 2),
        'data_reduction_tb': gib_to_tb(data_reduction)
    }


def get_top_systems_by_usage(
    db: Session,
    report_date: date,
    limit: int = 10
) -> List[Dict]:
    """Get top storage systems by capacity usage."""
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()
    
    system_data = []
    for s in systems:
        total = s.usable_capacity_gib or 0
        available = s.available_capacity_gib or 0
        used = total - available
        
        system_data.append({
            'name': s.name,
            'used_tb': gib_to_tb(used),
            'available_tb': gib_to_tb(available),
            'total_tb': gib_to_tb(total),
            'utilization_pct': calculate_utilization_pct(used, total)
        })
    
    # Sort by used capacity descending
    system_data.sort(key=lambda x: x['used_tb'], reverse=True)
    return system_data[:limit]


def get_utilization_distribution(db: Session, report_date: date) -> List[Dict]:
    """Get distribution of utilization across systems for histogram."""
    # Get systems with utilization percentages
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()
    
    # Return raw utilization percentages for histogram
    # Frontend Plotly histogram will automatically create bins
    result = []
    for system in systems:
        if system.used_capacity_percent is not None:
            result.append({
                'utilization_pct': system.used_capacity_percent,
                'name': system.name
            })
    
    return result


def get_forecasting_data(db: Session, report_date: date, limit: int = 10) -> List[Dict]:
    """Get pools with forecasting data for the combo chart."""
    pools = db.query(StoragePool).filter(
        StoragePool.report_date == report_date,
        StoragePool.utilization_pct.isnot(None)
    ).order_by(StoragePool.utilization_pct.desc()).limit(limit).all()
    
    result = []
    for pool in pools:
        days = calculate_days_until_full(
            pool.utilization_pct,
            pool.recent_growth_gib,
            pool.usable_capacity_gib
        )
        result.append({
            'name': pool.name,
            'utilization_pct': pool.utilization_pct,
            'days_until_full': days,
            'storage_system': pool.storage_system_name
        })
    
    return result


def get_storage_types_distribution(db: Session, report_date: date) -> List[Dict]:
    """Get distribution of storage by type."""
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()
    
    type_capacity = {}
    for s in systems:
        stype = s.type or 'Unknown'
        capacity = gib_to_tb(s.usable_capacity_gib or 0)
        type_capacity[stype] = type_capacity.get(stype, 0) + capacity
    
    return [{'type': k, 'capacity_tb': round(v, 2)} for k, v in type_capacity.items()]


def get_treemap_data(db: Session, report_date: date) -> Dict[str, List[Dict]]:
    """
    Get hierarchical data for treemap visualization using capacity_volumes table.
    
    Hierarchy: All Storage → Storage System → Pool → Volumes
    
    Returns both simple average and weighted average treemap data with full capacity details.
    Each node includes: total_capacity_gib, used_capacity_gib, available_capacity_gib, utilization_pct
    
    Returns:
        {
            'simple_average': [...],  # Average of volume utilization percentages
            'weighted_average': [...]  # Weighted by actual capacity usage
        }
    """
    # Use capacity_volumes table instead of storage_pools
    from app.db.models import CapacityVolume
    
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    ).all()
    
    if not volumes:
        return {'simple_average': [], 'weighted_average': []}
    
    # Sort volumes by capacity (largest first)
    sorted_volumes = sorted(volumes, key=lambda v: v.provisioned_capacity_gib or 0, reverse=True)
    
    # Calculate total capacity and adaptive threshold
    total_capacity = sum(v.provisioned_capacity_gib or 0 for v in volumes)
    total_used = sum(v.used_capacity_gib or 0 for v in volumes)
    total_available = sum(v.available_capacity_gib or 0 for v in volumes)
    
    # Adaptive threshold based on volume count (for aggregating small volumes)
    if len(volumes) > 200:
        threshold_pct = 0.02  # 2% for many volumes
    elif len(volumes) > 100:
        threshold_pct = 0.01  # 1% for moderate volumes
    else:
        threshold_pct = 0.005  # 0.5% for few volumes
    
    min_capacity_threshold = total_capacity * threshold_pct
    
    # ============================================================================
    # Build hierarchical structure: System → Pool → Volume
    # ============================================================================
    
    # Group volumes by system and pool
    system_pool_volumes = {}
    for volume in volumes:
        sys_name = volume.storage_system_name or 'Unknown System'
        pool_name = volume.pool_name or 'Unknown Pool'
        
        if sys_name not in system_pool_volumes:
            system_pool_volumes[sys_name] = {}
        
        if pool_name not in system_pool_volumes[sys_name]:
            system_pool_volumes[sys_name][pool_name] = []
        
        system_pool_volumes[sys_name][pool_name].append(volume)
    
    # ============================================================================
    # SIMPLE AVERAGE TREEMAP (Method 1)
    # ============================================================================
    simple_result = []
    
    # Root node - simple average (average of all volume utilizations)
    total_util_sum = 0
    volume_count = 0
    for volume in volumes:
        prov_cap = volume.provisioned_capacity_gib or 0
        used_cap = volume.used_capacity_gib or 0
        if prov_cap > 0:
            vol_util = (used_cap / prov_cap) * 100
            total_util_sum += vol_util
            volume_count += 1
    
    avg_total_util = total_util_sum / volume_count if volume_count > 0 else 0
    
    simple_result.append({
        'name': 'All Storage',
        'storage_system': '',
        'total_capacity_gib': total_capacity,
        'used_capacity_gib': total_used,
        'available_capacity_gib': total_available,
        'utilization_pct': round(avg_total_util, 1)
    })
    
    # Add system nodes and pool nodes - simple average
    for sys_name, pools in system_pool_volumes.items():
        # Calculate system-level aggregates
        sys_total = 0
        sys_used = 0
        sys_available = 0
        sys_util_sum = 0
        sys_volume_count = 0
        
        for pool_name, pool_volumes in pools.items():
            for vol in pool_volumes:
                prov_cap = vol.provisioned_capacity_gib or 0
                used_cap = vol.used_capacity_gib or 0
                avail_cap = vol.available_capacity_gib or 0
                
                sys_total += prov_cap
                sys_used += used_cap
                sys_available += avail_cap
                
                if prov_cap > 0:
                    vol_util = (used_cap / prov_cap) * 100
                    sys_util_sum += vol_util
                    sys_volume_count += 1
        
        sys_avg_util = sys_util_sum / sys_volume_count if sys_volume_count > 0 else 0
        
        # Add system node
        simple_result.append({
            'name': sys_name,
            'storage_system': 'All Storage',
            'total_capacity_gib': sys_total,
            'used_capacity_gib': sys_used,
            'available_capacity_gib': sys_available,
            'utilization_pct': round(sys_avg_util, 1)
        })
        
        # Add pool nodes
        for pool_name, pool_volumes in pools.items():
            pool_total = 0
            pool_used = 0
            pool_available = 0
            pool_util_sum = 0
            pool_volume_count = 0
            
            for vol in pool_volumes:
                prov_cap = vol.provisioned_capacity_gib or 0
                used_cap = vol.used_capacity_gib or 0
                avail_cap = vol.available_capacity_gib or 0
                
                pool_total += prov_cap
                pool_used += used_cap
                pool_available += avail_cap
                
                if prov_cap > 0:
                    vol_util = (used_cap / prov_cap) * 100
                    pool_util_sum += vol_util
                    pool_volume_count += 1
            
            pool_avg_util = pool_util_sum / pool_volume_count if pool_volume_count > 0 else 0
            
            # Add pool node
            simple_result.append({
                'name': pool_name,
                'storage_system': sys_name,
                'total_capacity_gib': pool_total,
                'used_capacity_gib': pool_used,
                'available_capacity_gib': pool_available,
                'utilization_pct': round(pool_avg_util, 1)
            })
            
            # Add volume nodes (with aggregation of small volumes)
            sorted_pool_volumes = sorted(pool_volumes, key=lambda v: v.provisioned_capacity_gib or 0, reverse=True)
            small_volumes_data = {
                'capacity': 0,
                'used': 0,
                'available': 0,
                'count': 0,
                'util_sum': 0
            }
            
            for vol in sorted_pool_volumes:
                prov_cap = vol.provisioned_capacity_gib or 0
                used_cap = vol.used_capacity_gib or 0
                avail_cap = vol.available_capacity_gib or 0
                vol_util = (used_cap / prov_cap * 100) if prov_cap > 0 else 0
                
                if prov_cap >= min_capacity_threshold:
                    # Large volume - add individual node
                    simple_result.append({
                        'name': vol.volume_name or 'Unnamed Volume',
                        'storage_system': pool_name,
                        'total_capacity_gib': prov_cap,
                        'used_capacity_gib': used_cap,
                        'available_capacity_gib': avail_cap,
                        'utilization_pct': round(vol_util, 1)
                    })
                else:
                    # Small volume - aggregate
                    small_volumes_data['capacity'] += prov_cap
                    small_volumes_data['used'] += used_cap
                    small_volumes_data['available'] += avail_cap
                    small_volumes_data['count'] += 1
                    small_volumes_data['util_sum'] += vol_util
            
            # Add aggregated small volumes node
            if small_volumes_data['count'] > 0:
                avg_small_util = small_volumes_data['util_sum'] / small_volumes_data['count']
                simple_result.append({
                    'name': f"Other Volumes ({small_volumes_data['count']})",
                    'storage_system': pool_name,
                    'total_capacity_gib': small_volumes_data['capacity'],
                    'used_capacity_gib': small_volumes_data['used'],
                    'available_capacity_gib': small_volumes_data['available'],
                    'utilization_pct': round(avg_small_util, 1)
                })
    
    # ============================================================================
    # WEIGHTED AVERAGE TREEMAP (Method 2)
    # ============================================================================
    weighted_result = []
    
    # Root node - weighted average
    weighted_total_util = (total_used / total_capacity * 100) if total_capacity > 0 else 0
    
    weighted_result.append({
        'name': 'All Storage',
        'storage_system': '',
        'total_capacity_gib': total_capacity,
        'used_capacity_gib': total_used,
        'available_capacity_gib': total_available,
        'utilization_pct': round(weighted_total_util, 1)
    })
    
    # Add system nodes and pool nodes - weighted average
    for sys_name, pools in system_pool_volumes.items():
        # Calculate system-level aggregates
        sys_total = 0
        sys_used = 0
        sys_available = 0
        
        for pool_name, pool_volumes in pools.items():
            for vol in pool_volumes:
                sys_total += (vol.provisioned_capacity_gib or 0)
                sys_used += (vol.used_capacity_gib or 0)
                sys_available += (vol.available_capacity_gib or 0)
        
        sys_weighted_util = (sys_used / sys_total * 100) if sys_total > 0 else 0
        
        # Add system node
        weighted_result.append({
            'name': sys_name,
            'storage_system': 'All Storage',
            'total_capacity_gib': sys_total,
            'used_capacity_gib': sys_used,
            'available_capacity_gib': sys_available,
            'utilization_pct': round(sys_weighted_util, 1)
        })
        
        # Add pool nodes
        for pool_name, pool_volumes in pools.items():
            pool_total = 0
            pool_used = 0
            pool_available = 0
            
            for vol in pool_volumes:
                pool_total += (vol.provisioned_capacity_gib or 0)
                pool_used += (vol.used_capacity_gib or 0)
                pool_available += (vol.available_capacity_gib or 0)
            
            pool_weighted_util = (pool_used / pool_total * 100) if pool_total > 0 else 0
            
            # Add pool node
            weighted_result.append({
                'name': pool_name,
                'storage_system': sys_name,
                'total_capacity_gib': pool_total,
                'used_capacity_gib': pool_used,
                'available_capacity_gib': pool_available,
                'utilization_pct': round(pool_weighted_util, 1)
            })
            
            # Add volume nodes (with aggregation of small volumes)
            sorted_pool_volumes = sorted(pool_volumes, key=lambda v: v.provisioned_capacity_gib or 0, reverse=True)
            small_volumes_data = {
                'capacity': 0,
                'used': 0,
                'available': 0,
                'count': 0
            }
            
            for vol in sorted_pool_volumes:
                prov_cap = vol.provisioned_capacity_gib or 0
                used_cap = vol.used_capacity_gib or 0
                avail_cap = vol.available_capacity_gib or 0
                vol_util = (used_cap / prov_cap * 100) if prov_cap > 0 else 0
                
                if prov_cap >= min_capacity_threshold:
                    # Large volume - add individual node
                    weighted_result.append({
                        'name': vol.volume_name or 'Unnamed Volume',
                        'storage_system': pool_name,
                        'total_capacity_gib': prov_cap,
                        'used_capacity_gib': used_cap,
                        'available_capacity_gib': avail_cap,
                        'utilization_pct': round(vol_util, 1)
                    })
                else:
                    # Small volume - aggregate
                    small_volumes_data['capacity'] += prov_cap
                    small_volumes_data['used'] += used_cap
                    small_volumes_data['available'] += avail_cap
                    small_volumes_data['count'] += 1
            
            # Add aggregated small volumes node (weighted average)
            if small_volumes_data['count'] > 0:
                weighted_small_util = (small_volumes_data['used'] / small_volumes_data['capacity'] * 100) if small_volumes_data['capacity'] > 0 else 0
                weighted_result.append({
                    'name': f"Other Volumes ({small_volumes_data['count']})",
                    'storage_system': pool_name,
                    'total_capacity_gib': small_volumes_data['capacity'],
                    'used_capacity_gib': small_volumes_data['used'],
                    'available_capacity_gib': small_volumes_data['available'],
                    'utilization_pct': round(weighted_small_util, 1)
                })
    
    return {
        'simple_average': simple_result,
        'weighted_average': weighted_result
    }
