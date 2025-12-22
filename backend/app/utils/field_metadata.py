"""
Field metadata for categorizing database fields as Imported or Calculated.

This module defines which fields come directly from Excel (Imported) and which
are calculated during preprocessing (Calculated).
"""
from typing import Dict, List, Literal

FieldCategory = Literal["Imported", "Calculated"]


# Field categories for each model/table
FIELD_CATEGORIES: Dict[str, Dict[str, FieldCategory]] = {
    "storage_systems": {
        # Common fields
        "id": "Imported",
        "report_date": "Imported",
        "upload_id": "Imported",
        "created_at": "Imported",
        
        # Storage Systems specific
        "name": "Imported",
        "type": "Imported",
        "model": "Imported",
        "serial_number": "Imported",
        "code_level": "Imported",
        "usable_capacity_gib": "Imported",
        "available_capacity_gib": "Imported",
        "used_capacity_gib": "Imported",
        "used_capacity_percent": "Imported",
        "pools": "Imported",
        "volumes": "Imported",
        "hosts": "Imported",
        "data_reduction_gib": "Imported",
        "total_compression_ratio": "Imported",
        "pool_compression_ratio": "Imported",
        "data_reduction_ratio": "Imported",
        "drive_compression_ratio": "Imported",
    },
    
    "storage_pools": {
        # Common fields
        "id": "Imported",
        "report_date": "Imported",
        "upload_id": "Imported",
        "storage_system_id": "Imported",
        "created_at": "Imported",
        
        # Storage Pools specific - Imported from Excel
        "name": "Imported",
        "storage_system_name": "Imported",
        "pool": "Imported",
        "type": "Imported",
        "usable_capacity_gib": "Imported",
        "available_capacity_gib": "Imported",
        "compressed": "Imported",
        "thin_provisioned": "Imported",
        "recent_growth_gib": "Imported",
        
        # CALCULATED FIELDS (computed during preprocessing)
        "used_capacity_gib": "Calculated",  # = usable_capacity_gib - available_capacity_gib
        "utilization_pct": "Calculated",    # = (used_capacity_gib / usable_capacity_gib) * 100
    },
    
    "capacity_volumes": {
        # Common fields
        "id": "Imported",
        "report_date": "Imported",
        "upload_id": "Imported",
        "storage_system_id": "Imported",
        "created_at": "Imported",
        
        # Capacity Volumes specific
        "name": "Imported",
        "volume_id": "Imported",
        "storage_system_name": "Imported",
        "pool": "Imported",
        "capacity_gib": "Imported",
        "used_capacity_gib": "Imported",
        "real_capacity_gib": "Imported",
        "hosts": "Imported",
        "host_count": "Imported",
    },
    
    "capacity_hosts": {
        # Common fields
        "id": "Imported",
        "report_date": "Imported",
        "upload_id": "Imported",
        "created_at": "Imported",
        
        # Capacity Hosts specific
        "name": "Imported",
        "host_cluster": "Imported",
        "location": "Imported",
        "san_capacity_gib": "Imported",
        "used_san_capacity_gib": "Imported",  # This is correct from Excel
        "primary_provisioned_capacity_gib": "Imported",
        "primary_used_capacity_gib": "Imported",
    },
    
    "capacity_disks": {
        # Common fields
        "id": "Imported",
        "report_date": "Imported",
        "upload_id": "Imported",
        "storage_system_id": "Imported",
        "created_at": "Imported",
        
        # Capacity Disks specific - Imported from Excel
        "storage_system_name": "Imported",
        "pool": "Imported",
        "capacity_gib": "Imported",
        "available_capacity_gib": "Imported",
        "active_quorum": "Imported",
        "zero_capacity": "Imported",
        
        # CALCULATED FIELDS (computed during preprocessing)
        "used_capacity_gib": "Calculated",  # = capacity_gib - available_capacity_gib
    },
    
    "departments": {
        # Common fields
        "id": "Imported",
        "report_date": "Imported",
        "upload_id": "Imported",
        "created_at": "Imported",
        
        # Departments specific
        "name": "Imported",
        "dept_type": "Imported",
        "contact": "Imported",
        "email": "Imported",
    },
    
    "alerts": {
        # All fields are system-generated
        "id": "Calculated",
        "pool_name": "Calculated",
        "storage_system": "Calculated",
        "utilization_pct": "Calculated",
        "level": "Calculated",
        "message": "Calculated",
        "days_until_full": "Calculated",
        "acknowledged": "Calculated",
        "created_at": "Calculated",
    },
    
    "upload_logs": {
        # All fields are system-generated
        "id": "Calculated",
        "user_id": "Calculated",
        "original_filename": "Calculated",
        "file_size_bytes": "Calculated",
        "report_date": "Calculated",
        "upload_datetime": "Calculated",
        "rows_uploaded": "Calculated",
        "duplicates_skipped": "Calculated",
        "upload_duration_seconds": "Calculated",
        "status": "Calculated",
        "error_message": "Calculated",
    },
    
    "users": {
        # All user management fields
        "id": "Imported",
        "username": "Imported",
        "email": "Imported",
        "hashed_password": "Imported",
        "full_name": "Imported",
        "role": "Imported",
        "is_active": "Imported",
        "created_at": "Imported",
    },
    
    "tenants": {
        # All tenant management fields
        "id": "Imported",
        "name": "Imported",
        "description": "Imported",
        "created_at": "Imported",
    },
    
    "user_tenants": {
        # User-Tenant mapping fields
        "id": "Imported",
        "user_id": "Imported",
        "tenant_id": "Imported",
        "created_at": "Imported",
    },
    
    "tenant_pool_mappings": {
        # Tenant-Pool mapping fields
        "id": "Imported",
        "tenant_id": "Imported",
        "pool_name": "Imported",
        "storage_system": "Imported",
        "created_at": "Imported",
    },
    
    "host_tenant_mappings": {
        # Host-Tenant mapping fields
        "id": "Imported",
        "tenant_id": "Imported",
        "host_name": "Imported",
        "created_at": "Imported",
    },
    
    "mdisk_system_mappings": {
        # MDisk-System mapping fields
        "id": "Imported",
        "mdisk_name": "Imported",
        "storage_system": "Imported",
        "created_at": "Imported",
    },
    
    "user_activity_logs": {
        # All fields are system-generated
        "id": "Calculated",
        "user_id": "Calculated",
        "action": "Calculated",
        "details": "Calculated",
        "timestamp": "Calculated",
        "ip_address": "Calculated",
    },
}


def get_field_category(table_name: str, field_name: str) -> FieldCategory:
    """
    Get the category (Imported or Calculated) for a specific field in a table.
    
    Args:
        table_name: Name of the database table
        field_name: Name of the field/column
        
    Returns:
        "Imported" if field comes from Excel, "Calculated" if computed
        Defaults to "Imported" if not found in metadata
    """
    table_fields = FIELD_CATEGORIES.get(table_name, {})
    return table_fields.get(field_name, "Imported")


def get_table_field_categories(table_name: str) -> Dict[str, FieldCategory]:
    """
    Get all field categories for a specific table.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        Dictionary mapping field names to their categories
    """
    return FIELD_CATEGORIES.get(table_name, {})


def get_calculated_fields(table_name: str) -> List[str]:
    """
    Get list of calculated field names for a table.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        List of field names that are calculated (not imported)
    """
    table_fields = FIELD_CATEGORIES.get(table_name, {})
    return [field for field, category in table_fields.items() if category == "Calculated"]


def get_imported_fields(table_name: str) -> List[str]:
    """
    Get list of imported field names for a table.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        List of field names that are imported from Excel
    """
    table_fields = FIELD_CATEGORIES.get(table_name, {})
    return [field for field, category in table_fields.items() if category == "Imported"]
