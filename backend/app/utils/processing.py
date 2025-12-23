"""
Data processing utilities for Excel parsing, calculations, and transformations.
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import io

from app.db.models import (
    StorageSystem, StoragePool, CapacityVolume,
    CapacityHost, CapacityDisk, Department,
    VolumeHostMapping, Alert, Tenant, TenantPoolMapping
)
from sqlalchemy import and_


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
    
    # Special rename for CapacityVolume: capacity_gib -> provisioned_capacity_gib
    if model_class == CapacityVolume:
        column_renames['capacity_gib'] = 'provisioned_capacity_gib'
    
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
    field is usually blank. We calculate it using the formula:
    available_capacity_gib = provisioned_capacity_gib - used_capacity_gib
    
    This preprocessing applies only to volumes from these specific FlashSystem storage systems.
    """
    FLASHSYSTEM_NAMES = ['A9K-A1', 'A9KR-R1', 'A9KR-R2']
    
    if 'storage_system_name' not in df.columns:
        return df
    
    if 'provisioned_capacity_gib' not in df.columns or 'used_capacity_gib' not in df.columns:
        return df
    
    # Create a mask for FlashSystem volumes
    flashsystem_mask = df['storage_system_name'].isin(FLASHSYSTEM_NAMES)
    
    # Calculate available_capacity_gib for FlashSystem volumes
    # Only update if available_capacity_gib is blank/null
    df.loc[flashsystem_mask & df['available_capacity_gib'].isna(), 'available_capacity_gib'] = \
        df.loc[flashsystem_mask & df['available_capacity_gib'].isna()].apply(
            lambda row: (row.get('provisioned_capacity_gib') or 0) - (row.get('used_capacity_gib') or 0),
            axis=1
        )
    
    return df


def parse_hosts_to_mapping(
    volumes_df: pd.DataFrame,
    report_date: date
) -> List[Dict[str, Any]]:
    """
    Parse the 'hosts' column from volumes and create volume-host mapping records.
    The hosts column contains comma-separated host names.
    """
    mappings = []
    
    if 'hosts' not in volumes_df.columns:
        return mappings
    
    for _, row in volumes_df.iterrows():
        hosts_str = row.get('hosts')
        if pd.isna(hosts_str) or not hosts_str:
            continue
        
        volume_name = row.get('name')
        storage_system = row.get('storage_system_name', row.get('storage_system'))
        pool = row.get('pool')
        
        if not volume_name or not storage_system:
            continue
        
        # Parse comma-separated hosts
        hosts = [h.strip() for h in str(hosts_str).split(',') if h.strip()]
        
        for host_name in hosts:
            mappings.append({
                'volume_name': volume_name,
                'storage_system': storage_system,
                'pool': pool,
                'host_name': host_name,
                'mapping_date': report_date
            })
    
    return mappings


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
        identifier = record.get('name')
        if not identifier or identifier == 'None':
            # For disks without names, use pool + storage_system
            identifier = f"{record.get('storage_system_name', 'Unknown')}/{record.get('pool', 'Unknown')}"
        
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
    Uses capacity_volumes as primary data source, falls back to storage_systems if needed.
    """
    # Try capacity_volumes first (primary data source)
    volumes_query = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    )
    
    # Apply tenant filtering if needed
    if tenant_ids:
        from app.db.models import TenantPoolMapping
        # Get pool names for these tenants
        pool_names = db.query(TenantPoolMapping.pool_name).filter(
            TenantPoolMapping.tenant_id.in_(tenant_ids)
        ).distinct().all()
        pool_names = [p[0] for p in pool_names]
        if pool_names:
            volumes_query = volumes_query.filter(CapacityVolume.pool.in_(pool_names))
    
    volumes = volumes_query.all()
    
    if volumes:
        # Calculate from capacity_volumes
        # Use provisioned_capacity_gib or capacity_gib
        total_capacity = sum(
            (v.provisioned_capacity_gib or 0) for v in volumes
        )
        used_capacity = sum(v.used_capacity_gib or 0 for v in volumes)
        available_capacity = total_capacity - used_capacity
        
        # Get unique counts
        unique_systems = len(set(v.storage_system_name for v in volumes if v.storage_system_name))
        unique_pools = len(set(v.pool for v in volumes if v.pool))
        total_volumes = len(volumes)
        
        # Get hosts count
        hosts_count = db.query(func.count(func.distinct(CapacityHost.id))).filter(
            CapacityHost.report_date == report_date
        ).scalar() or 0
        
        # Compression/deduplication data (if available in volumes)
        compression_ratios = [v.compression_ratio for v in volumes if hasattr(v, 'compression_ratio') and v.compression_ratio]
        avg_compression = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 1.0
        
        data_reduction = 0  # Calculate from volumes if available
        
    else:
        # Fall back to storage_systems table (legacy)
        systems = db.query(StorageSystem).filter(
            StorageSystem.report_date == report_date
        ).all()
        
        if not systems:
            # No data at all
            return {
                'total_capacity_tb': 0,
                'used_capacity_tb': 0,
                'available_capacity_tb': 0,
                'utilization_pct': 0,
                'total_systems': 0,
                'total_pools': 0,
                'total_volumes': 0,
                'total_hosts': 0,
                'compression_ratio': 1.0,
                'data_reduction_tb': 0
            }
        
        total_capacity = sum(s.usable_capacity_gib or 0 for s in systems)
        available_capacity = sum(s.available_capacity_gib or 0 for s in systems)
        used_capacity = total_capacity - available_capacity
        
        # Get compression ratio average
        compression_ratios = [s.total_compression_ratio for s in systems if s.total_compression_ratio]
        avg_compression = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 1.0
        
        # Get data reduction
        data_reduction = sum(s.data_reduction_gib or 0 for s in systems)
        
        # Get counts
        unique_systems = len(systems)
        unique_pools = sum(s.pools or 0 for s in systems)
        total_volumes = sum(s.volumes or 0 for s in systems)
        
        # Get hosts count
        hosts_count = db.query(func.count(CapacityHost.id)).filter(
            CapacityHost.report_date == report_date
        ).scalar() or 0
    
    utilization = calculate_utilization_pct(used_capacity, total_capacity)
    
    return {
        'total_capacity_tb': gib_to_tb(total_capacity),
        'used_capacity_tb': gib_to_tb(used_capacity),
        'available_capacity_tb': gib_to_tb(available_capacity),
        'utilization_pct': utilization,
        'total_systems': unique_systems,
        'total_pools': unique_pools,
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
    """
    Get top storage systems by capacity usage.
    Uses capacity_volumes as primary data source.
    """
    # Try capacity_volumes first
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    ).all()
    
    if volumes:
        # Aggregate by storage system
        system_data = {}
        for v in volumes:
            sys_name = v.storage_system_name
            if not sys_name:
                continue
            
            if sys_name not in system_data:
                system_data[sys_name] = {
                    'name': sys_name,
                    'total_gib': 0,
                    'used_gib': 0
                }
            
            # Use provisioned_capacity_gib or capacity_gib
            capacity = v.provisioned_capacity_gib or 0
            used = v.used_capacity_gib or 0
            
            system_data[sys_name]['total_gib'] += capacity
            system_data[sys_name]['used_gib'] += used
        
        # Convert to list and calculate metrics
        result = []
        for sys_name, data in system_data.items():
            total = data['total_gib']
            used = data['used_gib']
            available = total - used
            
            result.append({
                'name': sys_name,
                'used_tb': gib_to_tb(used),
                'available_tb': gib_to_tb(available),
                'total_tb': gib_to_tb(total),
                'utilization_pct': calculate_utilization_pct(used, total)
            })
        
        # Sort by used capacity descending
        result.sort(key=lambda x: x['used_tb'], reverse=True)
        return result[:limit]
    
    else:
        # Fall back to storage_systems table
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
    """
    Get distribution of utilization across systems for histogram.
    Uses capacity_volumes as primary data source.
    """
    # Try capacity_volumes first
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    ).all()
    
    if volumes:
        # Aggregate by storage system
        system_utils = {}
        for v in volumes:
            sys_name = v.storage_system_name
            if not sys_name:
                continue
            
            if sys_name not in system_utils:
                system_utils[sys_name] = {'total': 0, 'used': 0}
            
            capacity = v.provisioned_capacity_gib or 0
            used = v.used_capacity_gib or 0
            
            system_utils[sys_name]['total'] += capacity
            system_utils[sys_name]['used'] += used
        
        # Calculate utilization percentages
        utilizations = []
        for sys_name, data in system_utils.items():
            if data['total'] > 0:
                util_pct = (data['used'] / data['total']) * 100
                utilizations.append(util_pct)
    
    else:
        # Fall back to storage_systems
        systems = db.query(StorageSystem).filter(
            StorageSystem.report_date == report_date
        ).all()
        
        utilizations = []
        for s in systems:
            total = s.usable_capacity_gib or 0
            if total > 0:
                available = s.available_capacity_gib or 0
                used = total - available
                util_pct = (used / total) * 100
                utilizations.append(util_pct)
    
    if not utilizations:
        return {'bins': [], 'counts': []}
    
    # Create histogram bins
    bins = [0, 20, 40, 60, 80, 100]
    bin_labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    counts = [0] * len(bin_labels)
    
    for util in utilizations:
        for i, threshold in enumerate(bins[1:]):
            if util <= threshold:
                counts[i] += 1
                break
    
    return {
        'bins': bin_labels,
        'counts': counts
    }
    
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
    # Try storage_pools first (has forecasting data)
    pools = db.query(StoragePool).filter(
        StoragePool.report_date == report_date,
        StoragePool.utilization_pct.isnot(None)
    ).order_by(StoragePool.utilization_pct.desc()).limit(limit).all()
    
    if pools:
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
    
    # Fall back to capacity_volumes (aggregate by pool)
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    ).all()
    
    if not volumes:
        return []
    
    # Aggregate by pool
    pool_data = {}
    for v in volumes:
        pool_key = (v.pool, v.storage_system_name)
        if pool_key not in pool_data:
            pool_data[pool_key] = {'total': 0, 'used': 0}
        
        capacity = v.provisioned_capacity_gib or 0
        used = v.used_capacity_gib or 0
        
        pool_data[pool_key]['total'] += capacity
        pool_data[pool_key]['used'] += used
    
    # Calculate utilization and create result
    result = []
    for (pool_name, system_name), data in pool_data.items():
        if data['total'] > 0:
            util_pct = (data['used'] / data['total']) * 100
            result.append({
                'name': pool_name,
                'utilization_pct': round(util_pct, 2),
                'days_until_full': None,  # No growth data available
                'storage_system': system_name
            })
    
    # Sort by utilization descending
    result.sort(key=lambda x: x['utilization_pct'], reverse=True)
    return result[:limit]


def get_storage_types_distribution(db: Session, report_date: date) -> List[Dict]:
    """Get distribution of storage by type."""
    # Try storage_systems first
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()
    
    if systems:
        type_capacity = {}
        for s in systems:
            stype = s.type or 'Unknown'
            capacity = gib_to_tb(s.usable_capacity_gib or 0)
            type_capacity[stype] = type_capacity.get(stype, 0) + capacity
        
        return [{'type': k, 'capacity_tb': round(v, 2)} for k, v in type_capacity.items()]
    
    # Fall back to capacity_volumes (all volumes counted as "Unknown" type)
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    ).all()
    
    if not volumes:
        return []
    
    # Aggregate all capacity (no type info in volumes table)
    total_capacity_gib = sum(
        (v.provisioned_capacity_gib or 0) for v in volumes
    )
    
    return [{'type': 'Storage', 'capacity_tb': round(gib_to_tb(total_capacity_gib), 2)}]

def get_treemap_data(db: Session, report_date: date, tenant_ids: Optional[List[int]] = None) -> Dict[str, List[Dict]]:
    """
    Get hierarchical data for treemap visualization with tenant integration.
    
    Hierarchy: All Storage → Storage System → Tenant → Pool
    
    Source: capacity_volumes table with tenant_pool_mappings join
    
    Args:
        db: Database session
        report_date: Report date to query
        tenant_ids: Optional list of tenant IDs to filter by (for non-admin users)
    
    Returns both simple average and weighted average treemap data.
    Treemap uses weighted_average only.
    Comparison table uses both simple_average and weighted_average.
    
    Returns:
        {
            'simple_average': [...],  # For comparison table (cross-system tenant grouping)
            'weighted_average': [...]  # For treemap visualization (per-system tenant grouping)
        }
    """
    try:
        # Ensure UNKNOWN tenant exists
        unknown_tenant = db.query(Tenant).filter(Tenant.name == 'UNKNOWN').first()
        if not unknown_tenant:
            unknown_tenant = Tenant(
                name='UNKNOWN',
                description='Catch-all for unmapped pools'
            )
            db.add(unknown_tenant)
            db.commit()
            db.refresh(unknown_tenant)
        
        # Query capacity_volumes with tenant joins
        query = db.query(
            CapacityVolume,
            Tenant.name.label('tenant_name'),
            Tenant.id.label('tenant_id')
        ).outerjoin(
            TenantPoolMapping,
            and_(
                TenantPoolMapping.pool_name == CapacityVolume.pool,
                TenantPoolMapping.storage_system == CapacityVolume.storage_system_name
            )
        ).outerjoin(
            Tenant,
            Tenant.id == TenantPoolMapping.tenant_id
        ).filter(
            CapacityVolume.report_date == report_date
        )
        
        # Apply tenant filtering if provided (for non-admin users)
        if tenant_ids:
            # Include volumes that belong to specified tenants OR are unmapped (UNKNOWN)
            query = query.filter(
                or_(
                    TenantPoolMapping.tenant_id.in_(tenant_ids),
                    TenantPoolMapping.tenant_id.is_(None)  # Include unmapped pools
                )
            )
        
        results = query.all()
    
    if not results:
        return {'simple_average': [], 'weighted_average': []}
    
    # Group volumes by system → tenant → pool
    hierarchy = {}
    
    for volume, tenant_name, tenant_id in results:
        system = volume.storage_system_name or 'Unknown System'
        pool = volume.pool or 'Unknown Pool'
        tenant = tenant_name or 'UNKNOWN'
        
        provisioned = volume.provisioned_capacity_gib or 0
        used = volume.used_capacity_gib or 0
        available = volume.available_capacity_gib or 0
        
        # Build hierarchy
        if system not in hierarchy:
            hierarchy[system] = {}
        if tenant not in hierarchy[system]:
            hierarchy[system][tenant] = {}
        if pool not in hierarchy[system][tenant]:
            hierarchy[system][tenant][pool] = {
                'provisioned': 0,
                'used': 0,
                'available': 0,
                'volume_count': 0
            }
        
        # Aggregate volumes into pools
        hierarchy[system][tenant][pool]['provisioned'] += provisioned
        hierarchy[system][tenant][pool]['used'] += used
        hierarchy[system][tenant][pool]['available'] += available
        hierarchy[system][tenant][pool]['volume_count'] += 1
    
    # Calculate totals
    total_capacity = 0
    total_used = 0
    total_available = 0
    
    for system_data in hierarchy.values():
        for tenant_data in system_data.values():
            for pool_data in tenant_data.values():
                total_capacity += pool_data['provisioned']
                total_used += pool_data['used']
                total_available += pool_data['available']
    
    # ============================================================================
    # WEIGHTED AVERAGE TREEMAP (for visualization)
    # Hierarchy: All Storage → System → Tenant (per-system) → Pool
    # ============================================================================
    weighted_result = []
    
    # Root node
    root_util = (total_used / total_capacity * 100) if total_capacity > 0 else 0
    weighted_result.append({
        'name': 'All Storage',
        'storage_system': '',
        'tenant_name': None,
        'total_capacity_gib': total_capacity,
        'used_capacity_gib': total_used,
        'available_capacity_gib': total_available,
        'utilization_pct': round(root_util, 1)
    })
    
    # System nodes
    for system_name, tenants in hierarchy.items():
        system_capacity = 0
        system_used = 0
        system_available = 0
        
        for tenant_data in tenants.values():
            for pool_data in tenant_data.values():
                system_capacity += pool_data['provisioned']
                system_used += pool_data['used']
                system_available += pool_data['available']
        
        system_util = (system_used / system_capacity * 100) if system_capacity > 0 else 0
        
        weighted_result.append({
            'name': system_name,
            'storage_system': 'All Storage',
            'tenant_name': None,
            'total_capacity_gib': system_capacity,
            'used_capacity_gib': system_used,
            'available_capacity_gib': system_available,
            'utilization_pct': round(system_util, 1)
        })
        
        # Tenant nodes (per-system)
        for tenant_name, pools in tenants.items():
            tenant_capacity = 0
            tenant_used = 0
            tenant_available = 0
            pool_names = []
            
            for pool_name, pool_data in pools.items():
                tenant_capacity += pool_data['provisioned']
                tenant_used += pool_data['used']
                tenant_available += pool_data['available']
                pool_names.append(pool_name)
            
            tenant_util = (tenant_used / tenant_capacity * 100) if tenant_capacity > 0 else 0
            
            # Only show tenants that have pools (hide empty tenants)
            if tenant_capacity > 0:
                # Make tenant node name unique by combining system and tenant
                unique_tenant_name = f"{system_name}|{tenant_name}"
                
                weighted_result.append({
                    'name': unique_tenant_name,
                    'storage_system': system_name,
                    'tenant_name': tenant_name,
                    'total_capacity_gib': tenant_capacity,
                    'used_capacity_gib': tenant_used,
                    'available_capacity_gib': tenant_available,
                    'utilization_pct': round(tenant_util, 1),
                    'pool_count': len(pools)
                })
                
                # Pool nodes (leaf nodes)
                for pool_name, pool_data in pools.items():
                    pool_util = (pool_data['used'] / pool_data['provisioned'] * 100) if pool_data['provisioned'] > 0 else 0
                    
                    weighted_result.append({
                        'name': pool_name,
                        'storage_system': unique_tenant_name,  # Parent is unique tenant name
                        'tenant_name': tenant_name,
                        'actual_system': system_name,  # For comparison table reference
                        'total_capacity_gib': pool_data['provisioned'],
                        'used_capacity_gib': pool_data['used'],
                        'available_capacity_gib': pool_data['available'],
                        'utilization_pct': round(pool_util, 1),
                        'volume_count': pool_data['volume_count']
                    })
    
    # ============================================================================
    # SIMPLE AVERAGE DATA (for comparison table)
    # Grouping: By Tenant ACROSS ALL SYSTEMS
    # ============================================================================
    simple_result = []
    
    # Aggregate by tenant across all systems
    tenant_aggregates = {}
    
    for system_name, tenants in hierarchy.items():
        for tenant_name, pools in tenants.items():
            if tenant_name not in tenant_aggregates:
                tenant_aggregates[tenant_name] = {
                    'systems': set(),
                    'pools': [],
                    'pool_utilizations': [],
                    'total_capacity': 0,
                    'total_used': 0,
                    'total_available': 0
                }
            
            for pool_name, pool_data in pools.items():
                tenant_aggregates[tenant_name]['systems'].add(system_name)
                tenant_aggregates[tenant_name]['pools'].append(f"{system_name}:{pool_name}")
                
                pool_util = (pool_data['used'] / pool_data['provisioned'] * 100) if pool_data['provisioned'] > 0 else 0
                tenant_aggregates[tenant_name]['pool_utilizations'].append(pool_util)
                
                tenant_aggregates[tenant_name]['total_capacity'] += pool_data['provisioned']
                tenant_aggregates[tenant_name]['total_used'] += pool_data['used']
                tenant_aggregates[tenant_name]['total_available'] += pool_data['available']
    
    # Build simple average result for comparison table
    for tenant_name, data in tenant_aggregates.items():
        simple_avg = sum(data['pool_utilizations']) / len(data['pool_utilizations']) if data['pool_utilizations'] else 0
        weighted_avg = (data['total_used'] / data['total_capacity'] * 100) if data['total_capacity'] > 0 else 0
        
        simple_result.append({
            'tenant_name': tenant_name,
            'systems': ', '.join(sorted(data['systems'])),
            'pools': data['pools'],
            'pool_count': len(data['pools']),
            'total_capacity_gib': data['total_capacity'],
            'used_capacity_gib': data['total_used'],
            'available_capacity_gib': data['total_available'],
            'simple_avg_utilization': round(simple_avg, 1),
            'weighted_avg_utilization': round(weighted_avg, 1)
        })
    
    # Sort by tenant name (UNKNOWN last)
    simple_result.sort(key=lambda x: (x['tenant_name'] == 'UNKNOWN', x['tenant_name']))
    
        return {
            'simple_average': simple_result,
            'weighted_average': weighted_result
        }
    except Exception as e:
        # Log error and return empty data gracefully
        print(f"Error in get_treemap_data: {str(e)}")
        return {
            'simple_average': [],
            'weighted_average': []
        }
