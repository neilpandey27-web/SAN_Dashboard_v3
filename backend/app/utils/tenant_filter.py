"""
Tenant filtering utilities for multi-tenant data isolation.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Tenant, TenantPoolMapping, HostTenantMapping, CapacityVolume


def get_tenant_pool_names(db: Session, tenant_name: str) -> List[str]:
    """
    Get list of pool names for a specific tenant.

    Args:
        db: Database session
        tenant_name: Name of the tenant

    Returns:
        List of pool names belonging to the tenant
    """
    tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
    if not tenant:
        return []

    pool_mappings = db.query(TenantPoolMapping).filter(
        TenantPoolMapping.tenant_id == tenant.id
    ).all()

    return [mapping.pool_name for mapping in pool_mappings]


def get_tenant_host_names(db: Session, tenant_name: str) -> List[str]:
    """
    Get list of host names for a specific tenant.

    Args:
        db: Database session
        tenant_name: Name of the tenant

    Returns:
        List of host names belonging to the tenant
    """
    tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
    if not tenant:
        return []

    host_mappings = db.query(HostTenantMapping).filter(
        HostTenantMapping.tenant_id == tenant.id
    ).all()

    return [mapping.host_name for mapping in host_mappings]


def get_tenant_system_names(db: Session, tenant_name: str) -> List[str]:
    """
    Get list of storage system names for a specific tenant.
    Derived from tenant's pool mappings via capacity_volumes JOIN.

    This uses capacity_volumes.pool to match tenant_pool_mappings.pool_name
    because capacity_volumes.pool preserves the original naming (with underscores),
    ensuring exact matches with tenant mappings.

    Args:
        db: Database session
        tenant_name: Name of the tenant

    Returns:
        List of unique storage system names belonging to the tenant
    """
    tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
    if not tenant:
        return []

    # Get tenant's pool names
    pool_names = db.query(TenantPoolMapping.pool_name).filter(
        TenantPoolMapping.tenant_id == tenant.id
    ).all()
    pool_names_list = [p[0] for p in pool_names]

    if not pool_names_list:
        return []

    # Get latest report date
    latest_report_date = db.query(func.max(CapacityVolume.report_date)).scalar()
    if not latest_report_date:
        return []

    # JOIN capacity_volumes to get actual storage_system_name values
    # This ensures we get the exact system names as they appear in the database
    system_names = db.query(CapacityVolume.storage_system_name).filter(
        CapacityVolume.pool.in_(pool_names_list),
        CapacityVolume.report_date == latest_report_date
    ).distinct().all()

    return [s[0] for s in system_names]
