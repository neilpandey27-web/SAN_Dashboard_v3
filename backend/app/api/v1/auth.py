"""
Authentication API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Tenant, UserTenant, UserActivityLog
from app.db.schemas import UserSignup, UserLogin, TokenResponse, UserOut, PasswordChange
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    validate_password, get_current_user
)
from app.core.config import settings
from app.utils.email import send_signup_confirmation, send_admin_new_signup_notification

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=dict)
async def signup(
    user_data: UserSignup,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    Status will be 'pending' until approved by an admin.
    """
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    is_valid, msg = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Check tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == user_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant selected"
        )
    
    # Create user with pending status
    new_user = User(
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="user",
        status="pending"
    )
    db.add(new_user)
    db.flush()  # Get the user ID
    
    # Add tenant mapping
    user_tenant = UserTenant(user_id=new_user.id, tenant_id=tenant.id)
    db.add(user_tenant)
    
    # Log activity
    activity = UserActivityLog(
        user_id=new_user.id,
        action="signup",
        details=f"New user signup for tenant: {tenant.name}",
        ip_address=request.client.host if request.client else None
    )
    db.add(activity)
    
    db.commit()
    
    # Send confirmation email to user
    send_signup_confirmation(new_user.email, new_user.first_name)
    
    # Get admin emails and notify them
    admins = db.query(User).filter(User.role == "admin", User.status == "active").all()
    admin_emails = [a.email for a in admins]
    if admin_emails:
        send_admin_new_signup_notification(
            admin_emails,
            new_user.first_name,
            new_user.last_name,
            new_user.email,
            tenant.name
        )
    
    return {
        "success": True,
        "message": "Registration successful. Your account is pending approval."
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    """
    # Find user by username
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check user status
    if user.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending approval"
        )
    
    if user.status == "deactivated":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated"
        )
    
    # Check expiration
    if user.expiration_date and user.expiration_date < datetime.utcnow():
        user.status = "deactivated"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has expired"
        )
    
    # Get tenant IDs
    tenant_ids = [ut.tenant_id for ut in user.user_tenants]
    
    # Create tokens
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_ids": tenant_ids
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Log activity
    activity = UserActivityLog(
        user_id=user.id,
        action="login",
        details="User logged in",
        ip_address=request.client.host if request.client else None
    )
    db.add(activity)
    db.commit()
    
    # Build user response
    user_out = UserOut(
        id=user.id,
        username=user.username,
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
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_out
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log out the current user.
    Note: JWT tokens are stateless, so this just logs the action.
    Client should delete the token.
    """
    activity = UserActivityLog(
        user_id=current_user.id,
        action="logout",
        details="User logged out",
        ip_address=request.client.host if request.client else None
    )
    db.add(activity)
    db.commit()
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return UserOut(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        expiration_date=current_user.expiration_date,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        tenants=[{
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "created_at": t.created_at
        } for t in current_user.tenants]
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change the current user's password."""
    # Verify old password
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    is_valid, msg = validate_password(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    
    # Log activity
    activity = UserActivityLog(
        user_id=current_user.id,
        action="password_change",
        details="User changed password"
    )
    db.add(activity)
    db.commit()
    
    return {"success": True, "message": "Password changed successfully"}


@router.get("/tenants")
async def get_tenants(db: Session = Depends(get_db)):
    """Get list of available tenants for signup."""
    tenants = db.query(Tenant).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description
        }
        for t in tenants
    ]
