"""
Tenant/Pool/Host mapping API endpoints (admin only).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io

from app.db.database import get_db
from app.db.models import (
    User, Tenant, TenantPoolMapping, HostTenantMapping,
    MdiskSystemMapping, UserActivityLog, StoragePool
)
from app.db.schemas import (
    TenantPoolMappingCreate, TenantPoolMappingOut,
    HostTenantMappingCreate, HostTenantMappingOut,
    MdiskSystemMappingCreate, MdiskSystemMappingOut
)
from app.core.security import get_current_admin_user

router = APIRouter(prefix="/mappings", tags=["Mappings"])


# ============================================================================
# Tenant-Pool Mappings
# ============================================================================

@router.get("/tenant-pools", response_model=List[TenantPoolMappingOut])
async def list_tenant_pool_mappings(
        tenant_id: Optional[int] = Query(None, description="Filter by tenant"),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """List all tenant-pool mappings (admin only)."""
    query = db.query(TenantPoolMapping)

    if tenant_id:
        query = query.filter(TenantPoolMapping.tenant_id == tenant_id)

    mappings = query.order_by(TenantPoolMapping.pool_name).all()

    result = []
    for m in mappings:
        tenant = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        result.append(TenantPoolMappingOut(
            id=m.id,
            tenant_id=m.tenant_id,
            tenant_name=tenant.name if tenant else None,
            pool_name=m.pool_name,
            storage_system=m.storage_system,
            created_at=m.created_at
        ))

    return result


@router.post("/tenant-pools", response_model=TenantPoolMappingOut)
async def create_tenant_pool_mapping(
        mapping_data: TenantPoolMappingCreate,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Create a new tenant-pool mapping (admin only)."""
    # Check tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == mapping_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not found"
        )

    # Check for duplicate
    existing = db.query(TenantPoolMapping).filter(
        TenantPoolMapping.pool_name == mapping_data.pool_name,
        TenantPoolMapping.storage_system == mapping_data.storage_system
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pool is already mapped to a tenant"
        )

    # Create mapping
    mapping = TenantPoolMapping(
        tenant_id=mapping_data.tenant_id,
        pool_name=mapping_data.pool_name,
        storage_system=mapping_data.storage_system
    )
    db.add(mapping)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="create_pool_mapping",
        details=f"Mapped pool '{mapping_data.pool_name}' to tenant '{tenant.name}'"
    )
    db.add(activity)
    db.commit()
    db.refresh(mapping)

    return TenantPoolMappingOut(
        id=mapping.id,
        tenant_id=mapping.tenant_id,
        tenant_name=tenant.name,
        pool_name=mapping.pool_name,
        storage_system=mapping.storage_system,
        created_at=mapping.created_at
    )


@router.delete("/tenant-pools/{mapping_id}")
async def delete_tenant_pool_mapping(
        mapping_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Delete a tenant-pool mapping (admin only)."""
    mapping = db.query(TenantPoolMapping).filter(TenantPoolMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    pool_name = mapping.pool_name
    db.delete(mapping)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="delete_pool_mapping",
        details=f"Removed mapping for pool '{pool_name}'"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"Mapping for pool '{pool_name}' deleted"}


# ============================================================================
# 🆕 NEW: Tenant-Pool CSV Upload
# ============================================================================

@router.post("/tenant-pools/upload-csv")
async def upload_tenant_pool_csv(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Upload CSV file with tenant-pool mappings.
    CSV format: tenant,pool,storage_system (with headers)
    Example:
        tenant,pool,storage_system
        Engineering,Pool_01,FlashSystem_A
        Finance,Pool_03,FlashSystem_B

    Note: storage_system column is optional
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    try:
        # Read CSV content
        content = await file.read()
        content_str = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content_str))

        # Validate headers (tenant and pool are required, storage_system is optional)
        if 'tenant' not in csv_reader.fieldnames or 'pool' not in csv_reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must have 'tenant' and 'pool' columns (storage_system is optional)"
            )

        # Get all tenants for lookup
        tenants = {t.name: t.id for t in db.query(Tenant).all()}

        added = 0
        skipped = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (1 is header)
            tenant_name = row.get('tenant', '').strip()
            pool_name = row.get('pool', '').strip()
            storage_system = row.get('storage_system', '').strip() or None

            if not tenant_name or not pool_name:
                errors.append(f"Row {row_num}: Missing tenant or pool")
                continue

            # Check if tenant exists
            if tenant_name not in tenants:
                errors.append(f"Row {row_num}: Tenant '{tenant_name}' not found")
                continue

            tenant_id = tenants[tenant_name]

            # Check if mapping already exists
            existing = db.query(TenantPoolMapping).filter(
                TenantPoolMapping.pool_name == pool_name
            ).first()

            if existing:
                skipped += 1
                continue

            # Create mapping
            mapping = TenantPoolMapping(
                tenant_id=tenant_id,
                pool_name=pool_name,
                storage_system=storage_system
            )
            db.add(mapping)
            added += 1

        # Commit all mappings
        db.commit()

        # Log activity
        activity = UserActivityLog(
            user_id=current_user.id,
            action="upload_tenant_pool_csv",
            details=f"Uploaded CSV: {added} mappings added, {skipped} skipped"
        )
        db.add(activity)
        db.commit()

        return {
            "success": True,
            "message": f"CSV processed successfully",
            "added": added,
            "skipped": skipped,
            "errors": errors
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV encoding. Please use UTF-8"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )


@router.get("/available-pools")
async def get_available_pools(
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Get list of pools not yet mapped to any tenant."""
    # Get all mapped pool names
    mapped_pools = db.query(TenantPoolMapping.pool_name).all()
    mapped_pool_names = [p[0] for p in mapped_pools]

    # Get all pools from latest data
    pools = db.query(StoragePool.name, StoragePool.storage_system_name).distinct().all()

    available = [
        {"name": p[0], "storage_system": p[1]}
        for p in pools
        if p[0] not in mapped_pool_names
    ]

    return available


# ============================================================================
# Host-Tenant Mappings
# ============================================================================

@router.get("/host-tenants", response_model=List[HostTenantMappingOut])
async def list_host_tenant_mappings(
        tenant_id: Optional[int] = Query(None, description="Filter by tenant"),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """List all host-tenant mappings (admin only)."""
    query = db.query(HostTenantMapping)

    if tenant_id:
        query = query.filter(HostTenantMapping.tenant_id == tenant_id)

    mappings = query.order_by(HostTenantMapping.host_name).all()

    result = []
    for m in mappings:
        tenant = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        result.append(HostTenantMappingOut(
            id=m.id,
            tenant_id=m.tenant_id,
            tenant_name=tenant.name if tenant else None,
            host_name=m.host_name,
            created_at=m.created_at
        ))

    return result


@router.post("/host-tenants", response_model=HostTenantMappingOut)
async def create_host_tenant_mapping(
        mapping_data: HostTenantMappingCreate,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Create a new host-tenant mapping (admin only)."""
    # Check tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == mapping_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not found"
        )

    # Check for duplicate
    existing = db.query(HostTenantMapping).filter(
        HostTenantMapping.host_name == mapping_data.host_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host is already mapped to a tenant"
        )

    # Create mapping
    mapping = HostTenantMapping(
        tenant_id=mapping_data.tenant_id,
        host_name=mapping_data.host_name
    )
    db.add(mapping)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="create_host_mapping",
        details=f"Mapped host '{mapping_data.host_name}' to tenant '{tenant.name}'"
    )
    db.add(activity)
    db.commit()
    db.refresh(mapping)

    return HostTenantMappingOut(
        id=mapping.id,
        tenant_id=mapping.tenant_id,
        tenant_name=tenant.name,
        host_name=mapping.host_name,
        created_at=mapping.created_at
    )


@router.delete("/host-tenants/{mapping_id}")
async def delete_host_tenant_mapping(
        mapping_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Delete a host-tenant mapping (admin only)."""
    mapping = db.query(HostTenantMapping).filter(HostTenantMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    host_name = mapping.host_name
    db.delete(mapping)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="delete_host_mapping",
        details=f"Removed mapping for host '{host_name}'"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"Mapping for host '{host_name}' deleted"}


@router.post("/host-tenants/upload-csv")
async def upload_host_tenant_csv(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Upload CSV file with tenant-host mappings.
    CSV format: tenant,host (with headers)
    Example:
        tenant,host
        BTC,host001
        HMC,host002
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    try:
        # Read CSV content
        content = await file.read()
        content_str = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content_str))

        # Validate headers
        if 'tenant' not in csv_reader.fieldnames or 'host' not in csv_reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must have 'tenant' and 'host' columns"
            )

        # Get all tenants for lookup
        tenants = {t.name: t.id for t in db.query(Tenant).all()}

        added = 0
        skipped = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (1 is header)
            tenant_name = row.get('tenant', '').strip()
            host_name = row.get('host', '').strip()

            if not tenant_name or not host_name:
                errors.append(f"Row {row_num}: Missing tenant or host")
                continue

            # Check if tenant exists
            if tenant_name not in tenants:
                errors.append(f"Row {row_num}: Tenant '{tenant_name}' not found")
                continue

            tenant_id = tenants[tenant_name]

            # Check if mapping already exists
            existing = db.query(HostTenantMapping).filter(
                HostTenantMapping.host_name == host_name
            ).first()

            if existing:
                skipped += 1
                continue

            # Create mapping
            mapping = HostTenantMapping(
                tenant_id=tenant_id,
                host_name=host_name
            )
            db.add(mapping)
            added += 1

        # Commit all mappings
        db.commit()

        # Log activity
        activity = UserActivityLog(
            user_id=current_user.id,
            action="upload_host_tenant_csv",
            details=f"Uploaded CSV: {added} mappings added, {skipped} skipped"
        )
        db.add(activity)
        db.commit()

        return {
            "success": True,
            "message": f"CSV processed successfully",
            "added": added,
            "skipped": skipped,
            "errors": errors
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV encoding. Please use UTF-8"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )


# ============================================================================
# mDisk-System Mappings
# ============================================================================

@router.get("/mdisk-systems", response_model=List[MdiskSystemMappingOut])
async def list_mdisk_system_mappings(
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """List all mDisk-system mappings (admin only)."""
    mappings = db.query(MdiskSystemMapping).order_by(MdiskSystemMapping.mdisk_name).all()
    return [MdiskSystemMappingOut.model_validate(m) for m in mappings]


@router.post("/mdisk-systems", response_model=MdiskSystemMappingOut)
async def create_mdisk_system_mapping(
        mapping_data: MdiskSystemMappingCreate,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Create a new mDisk-system mapping (admin only)."""
    # Check for duplicate
    existing = db.query(MdiskSystemMapping).filter(
        MdiskSystemMapping.mdisk_name == mapping_data.mdisk_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mDisk is already mapped"
        )

    # Create mapping
    mapping = MdiskSystemMapping(
        mdisk_name=mapping_data.mdisk_name,
        system_name=mapping_data.system_name
    )
    db.add(mapping)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="create_mdisk_mapping",
        details=f"Mapped mDisk '{mapping_data.mdisk_name}' to system '{mapping_data.system_name}'"
    )
    db.add(activity)
    db.commit()
    db.refresh(mapping)

    return MdiskSystemMappingOut.model_validate(mapping)


@router.delete("/mdisk-systems/{mapping_id}")
async def delete_mdisk_system_mapping(
        mapping_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Delete a mDisk-system mapping (admin only)."""
    mapping = db.query(MdiskSystemMapping).filter(MdiskSystemMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    mdisk_name = mapping.mdisk_name
    db.delete(mapping)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="delete_mdisk_mapping",
        details=f"Removed mapping for mDisk '{mdisk_name}'"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"Mapping for mDisk '{mdisk_name}' deleted"}
