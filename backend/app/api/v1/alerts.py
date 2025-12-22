"""
Alerts API endpoints.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Alert, TenantPoolMapping, UserActivityLog
from app.db.schemas import AlertOut
from app.core.security import get_current_user, get_user_tenant_ids

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/list", response_model=List[AlertOut])
async def list_alerts(
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    level: Optional[str] = Query(None, description="Filter by level (warning/critical/emergency)"),
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List alerts.
    Admins see all alerts, users see alerts for their tenants' pools.
    """
    query = db.query(Alert)
    
    # Filter by acknowledged status
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    
    # Filter by level
    if level:
        query = query.filter(Alert.level == level)
    
    # Filter by tenant pools for non-admin users
    if current_user.role != "admin":
        tenant_ids = get_user_tenant_ids(current_user)
        if tenant_ids:
            # Get pool names mapped to user's tenants
            pool_names = db.query(TenantPoolMapping.pool_name).filter(
                TenantPoolMapping.tenant_id.in_(tenant_ids)
            ).all()
            pool_names = [p[0] for p in pool_names]
            
            if pool_names:
                query = query.filter(Alert.pool_name.in_(pool_names))
            else:
                # No pools mapped to user's tenants
                return []
    
    # Order by created_at descending (newest first)
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    return [AlertOut.model_validate(a) for a in alerts]


@router.get("/unacknowledged")
async def get_unacknowledged_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get unacknowledged alerts for the notification bell.
    Returns alerts grouped by level with counts.
    """
    query = db.query(Alert).filter(Alert.acknowledged == False)
    
    # Filter by tenant pools for non-admin users
    if current_user.role != "admin":
        tenant_ids = get_user_tenant_ids(current_user)
        if tenant_ids:
            pool_names = db.query(TenantPoolMapping.pool_name).filter(
                TenantPoolMapping.tenant_id.in_(tenant_ids)
            ).all()
            pool_names = [p[0] for p in pool_names]
            
            if pool_names:
                query = query.filter(Alert.pool_name.in_(pool_names))
            else:
                return {
                    "total": 0,
                    "emergency": 0,
                    "critical": 0,
                    "warning": 0,
                    "alerts": []
                }
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    emergency_count = sum(1 for a in alerts if a.level == 'emergency')
    critical_count = sum(1 for a in alerts if a.level == 'critical')
    warning_count = sum(1 for a in alerts if a.level == 'warning')
    
    return {
        "total": len(alerts),
        "emergency": emergency_count,
        "critical": critical_count,
        "warning": warning_count,
        "alerts": [
            {
                "id": a.id,
                "pool_name": a.pool_name,
                "storage_system": a.storage_system,
                "utilization_pct": a.utilization_pct,
                "level": a.level,
                "message": a.message,
                "days_until_full": a.days_until_full,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts[:20]  # Limit to 20 for dropdown
        ]
    }


@router.get("/count")
async def get_alert_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unacknowledged alerts for badge."""
    query = db.query(Alert).filter(Alert.acknowledged == False)
    
    # Filter by tenant pools for non-admin users
    if current_user.role != "admin":
        tenant_ids = get_user_tenant_ids(current_user)
        if tenant_ids:
            pool_names = db.query(TenantPoolMapping.pool_name).filter(
                TenantPoolMapping.tenant_id.in_(tenant_ids)
            ).all()
            pool_names = [p[0] for p in pool_names]
            
            if pool_names:
                query = query.filter(Alert.pool_name.in_(pool_names))
            else:
                return {"count": 0}
    
    count = query.count()
    return {"count": count}


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Check if user has access to this alert (for non-admins)
    if current_user.role != "admin":
        tenant_ids = get_user_tenant_ids(current_user)
        if tenant_ids:
            pool_names = db.query(TenantPoolMapping.pool_name).filter(
                TenantPoolMapping.tenant_id.in_(tenant_ids)
            ).all()
            pool_names = [p[0] for p in pool_names]
            
            if alert.pool_name not in pool_names:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this alert"
                )
    
    # Acknowledge the alert
    alert.acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="acknowledge_alert",
        details=f"Acknowledged alert for pool: {alert.pool_name}"
    )
    db.add(activity)
    db.commit()
    
    return {
        "success": True,
        "message": f"Alert for pool '{alert.pool_name}' acknowledged"
    }


@router.post("/acknowledge-all")
async def acknowledge_all_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge all unacknowledged alerts visible to the user."""
    query = db.query(Alert).filter(Alert.acknowledged == False)
    
    # Filter by tenant pools for non-admin users
    if current_user.role != "admin":
        tenant_ids = get_user_tenant_ids(current_user)
        if tenant_ids:
            pool_names = db.query(TenantPoolMapping.pool_name).filter(
                TenantPoolMapping.tenant_id.in_(tenant_ids)
            ).all()
            pool_names = [p[0] for p in pool_names]
            
            if pool_names:
                query = query.filter(Alert.pool_name.in_(pool_names))
            else:
                return {"success": True, "acknowledged_count": 0}
    
    alerts = query.all()
    count = len(alerts)
    
    for alert in alerts:
        alert.acknowledged = True
        alert.acknowledged_by = current_user.id
        alert.acknowledged_at = datetime.utcnow()
    
    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="acknowledge_all_alerts",
        details=f"Acknowledged {count} alerts"
    )
    db.add(activity)
    db.commit()
    
    return {
        "success": True,
        "acknowledged_count": count,
        "message": f"{count} alerts acknowledged"
    }
