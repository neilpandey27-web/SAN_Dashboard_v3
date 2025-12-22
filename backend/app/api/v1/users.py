"""
User management API endpoints (admin only).
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Tenant, UserTenant, UserActivityLog, UploadLog
from app.db.schemas import (
    UserOut, UserUpdate, ActivityLogOut, UploadLogOut
)
from app.core.security import get_current_admin_user, hash_password
from app.utils.email import send_account_approved, send_account_rejected

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/list", response_model=List[UserOut])
async def list_users(
        status_filter: Optional[str] = Query(None, description="Filter by status"),
        role_filter: Optional[str] = Query(None, description="Filter by role"),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    query = db.query(User)

    if status_filter:
        query = query.filter(User.status == status_filter)
    if role_filter:
        query = query.filter(User.role == role_filter)

    users = query.order_by(User.created_at.desc()).all()

    return [
        UserOut(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            role=u.role,
            status=u.status,
            expiration_date=u.expiration_date,
            last_login=u.last_login,
            created_at=u.created_at,
            tenants=[{
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "created_at": t.created_at
            } for t in u.tenants]
        )
        for u in users
    ]


@router.get("/pending", response_model=List[UserOut])
async def list_pending_users(
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """List users pending approval (admin only)."""
    users = db.query(User).filter(User.status == "pending").order_by(User.created_at.desc()).all()

    return [
        UserOut(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            role=u.role,
            status=u.status,
            expiration_date=u.expiration_date,
            last_login=u.last_login,
            created_at=u.created_at,
            tenants=[{
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "created_at": t.created_at
            } for t in u.tenants]
        )
        for u in users
    ]


@router.get("/pending/count")
async def get_pending_count(
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Get count of pending user approvals (admin only)."""
    count = db.query(User).filter(User.status == "pending").count()
    return {"count": count}


@router.post("/approve/{user_id}")
async def approve_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Approve a pending user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User is not pending (current status: {user.status})"
        )

    # Approve user
    user.status = "active"

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="approve_user",
        details=f"Approved user: {user.email}"
    )
    db.add(activity)
    db.commit()

    # Send approval email
    send_account_approved(user.email, user.first_name)

    return {"success": True, "message": f"User {user.email} approved successfully"}


@router.post("/reject/{user_id}")
async def reject_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Reject and delete a pending user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User is not pending (current status: {user.status})"
        )

    user_email = user.email
    user_name = user.first_name

    # Send rejection email before deleting
    send_account_rejected(user_email, user_name)

    # Delete user tenant mappings
    db.query(UserTenant).filter(UserTenant.user_id == user_id).delete()

    # Delete user
    db.delete(user)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="reject_user",
        details=f"Rejected user: {user_email}"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"User {user_email} rejected and removed"}


@router.put("/edit/{user_id}", response_model=UserOut)
async def edit_user(
        user_id: int,
        user_update: UserUpdate,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Edit user details (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent editing self role
    if user.id == current_user.id and user_update.role and user_update.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own admin role"
        )

    # Update fields if provided
    if user_update.first_name:
        user.first_name = user_update.first_name
    if user_update.last_name:
        user.last_name = user_update.last_name
    if user_update.email:
        # Check if email is taken by another user
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role
    if user_update.status:
        user.status = user_update.status
    if user_update.expiration_date is not None:
        user.expiration_date = user_update.expiration_date

    # Update tenant assignments if provided
    if user_update.tenant_ids is not None:
        # Remove existing tenant mappings
        db.query(UserTenant).filter(UserTenant.user_id == user_id).delete()

        # Add new tenant mappings
        for tenant_id in user_update.tenant_ids:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                user_tenant = UserTenant(user_id=user_id, tenant_id=tenant_id)
                db.add(user_tenant)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="edit_user",
        details=f"Edited user: {user.email}"
    )
    db.add(activity)
    db.commit()
    db.refresh(user)

    return UserOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        status=user.status,
        expiration_date=user.expiration_date,
        last_login=user.last_login,
        created_at=user.created_at,
        tenants=[{
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "created_at": t.created_at
        } for t in user.tenants]
    )


@router.delete("/{user_id}")
async def delete_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_email = user.email

    # Delete tenant mappings
    db.query(UserTenant).filter(UserTenant.user_id == user_id).delete()

    # Delete user
    db.delete(user)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="delete_user",
        details=f"Deleted user: {user_email}"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"User {user_email} deleted"}


@router.put("/deactivate/{user_id}")
async def deactivate_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Deactivate a user account (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.status = "deactivated"

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="deactivate_user",
        details=f"Deactivated user: {user.email}"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"User {user.email} deactivated"}


@router.put("/activate/{user_id}")
async def activate_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Activate a deactivated user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.status = "active"

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="activate_user",
        details=f"Activated user: {user.email}"
    )
    db.add(activity)
    db.commit()

    return {"success": True, "message": f"User {user.email} activated"}


# ============================================================================
# Activity Logs
# ============================================================================

@router.get("/activity-logs", response_model=List[ActivityLogOut])
async def get_activity_logs(
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        limit: int = Query(100, le=1000),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Get user activity logs (admin only)."""
    query = db.query(UserActivityLog)

    if user_id:
        query = query.filter(UserActivityLog.user_id == user_id)

    logs = query.order_by(UserActivityLog.timestamp.desc()).limit(limit).all()

    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append(ActivityLogOut(
            id=log.id,
            user_id=log.user_id,
            user_name=user.full_name if user else "Unknown",
            action=log.action,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp
        ))

    return result


@router.get("/upload-logs", response_model=List[UploadLogOut])
async def get_upload_logs(
        limit: int = Query(50, le=500),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Get data upload logs (admin only)."""
    logs = db.query(UploadLog).order_by(UploadLog.upload_date.desc()).limit(limit).all()

    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append(UploadLogOut(
            id=log.id,
            upload_date=log.upload_date,
            file_name=log.file_name,
            user_id=log.user_id,
            user_name=user.full_name if user else "Unknown",
            rows_added=log.rows_added,
            duplicates_skipped=log.duplicates_skipped,
            errors=log.errors,
            status=log.status,
            upload_duration_seconds=log.upload_duration_seconds
        ))

    return result


# ============================================================================
# Tenants Management
# ============================================================================

@router.get("/tenants")
async def list_tenants(
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """List all tenants (admin only)."""
    tenants = db.query(Tenant).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "created_at": t.created_at,
            "user_count": len(t.users)
        }
        for t in tenants
    ]


@router.post("/tenants")
async def create_tenant(
        name: str,
        description: Optional[str] = None,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Create a new tenant (admin only)."""
    existing = db.query(Tenant).filter(Tenant.name == name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant name already exists"
        )

    tenant = Tenant(name=name, description=description)
    db.add(tenant)

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="create_tenant",
        details=f"Created tenant: {name}"
    )
    db.add(activity)
    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "description": tenant.description,
        "created_at": tenant.created_at
    }


@router.put("/tenants/{tenant_id}")
async def update_tenant(
        tenant_id: int,
        name: str,
        description: Optional[str] = None,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """Update an existing tenant (admin only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if new name conflicts with another tenant
    if name != tenant.name:
        existing = db.query(Tenant).filter(
            Tenant.name == name,
            Tenant.id != tenant_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant name already exists"
            )

    # Update tenant
    tenant.name = name
    tenant.description = description

    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="update_tenant",
        details=f"Updated tenant: {name}"
    )
    db.add(activity)
    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "description": tenant.description,
        "created_at": tenant.created_at
    }
