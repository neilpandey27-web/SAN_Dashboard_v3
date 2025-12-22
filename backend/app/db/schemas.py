"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserSignup(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    tenant_id: int
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class PasswordChange(BaseModel):
    """Schema for password change."""
    old_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


# ============================================================================
# User Schemas
# ============================================================================

class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str
    description: Optional[str] = None


class TenantOut(TenantBase):
    """Tenant output schema."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    first_name: str
    last_name: str
    email: EmailStr


class UserOut(UserBase):
    """User output schema (excludes password)."""
    id: int
    role: str
    status: str
    expiration_date: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    tenants: List[TenantOut] = []
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user details."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    expiration_date: Optional[datetime] = None
    tenant_ids: Optional[List[int]] = None


class UserBulkImport(BaseModel):
    """Schema for bulk user import row."""
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    tenant_name: str
    role: str = "user"


# ============================================================================
# Mapping Schemas
# ============================================================================

class TenantPoolMappingCreate(BaseModel):
    """Schema for creating tenant-pool mapping."""
    tenant_id: int
    pool_name: str
    storage_system: Optional[str] = None


class TenantPoolMappingOut(BaseModel):
    """Tenant-pool mapping output."""
    id: int
    tenant_id: int
    tenant_name: Optional[str] = None
    pool_name: str
    storage_system: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class HostTenantMappingCreate(BaseModel):
    """Schema for creating host-tenant mapping."""
    tenant_id: int
    host_name: str


class HostTenantMappingOut(BaseModel):
    """Host-tenant mapping output."""
    id: int
    tenant_id: int
    tenant_name: Optional[str] = None
    host_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class MdiskSystemMappingCreate(BaseModel):
    """Schema for creating mDisk-system mapping."""
    mdisk_name: str
    system_name: str


class MdiskSystemMappingOut(BaseModel):
    """mDisk-system mapping output."""
    id: int
    mdisk_name: str
    system_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertOut(BaseModel):
    """Alert output schema."""
    id: int
    pool_name: str
    storage_system: str
    utilization_pct: float
    level: str
    message: str
    days_until_full: Optional[int] = None
    created_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    alert_id: int


# ============================================================================
# Data/Upload Schemas
# ============================================================================

class UploadLogOut(BaseModel):
    """Upload log output schema."""
    id: int
    upload_date: datetime
    file_name: str
    user_id: int
    user_name: Optional[str] = None
    rows_added: int
    duplicates_skipped: int
    errors: Optional[str] = None
    status: str
    upload_duration_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response schema for file upload."""
    success: bool
    message: str
    rows_added: int = 0
    duplicates_skipped: int = 0
    errors: List[str] = []
    sheets_processed: List[str] = []


# ============================================================================
# Activity Log Schemas
# ============================================================================

class ActivityLogOut(BaseModel):
    """Activity log output schema."""
    id: int
    user_id: int
    user_name: Optional[str] = None
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Dashboard Data Schemas
# ============================================================================

class KPIData(BaseModel):
    """KPI card data."""
    total_capacity_tb: float
    used_capacity_tb: float
    available_capacity_tb: float
    utilization_pct: float
    total_systems: int
    total_pools: int
    total_volumes: int
    total_hosts: int
    compression_ratio: float
    data_reduction_tb: float


class AlertSummary(BaseModel):
    """Alert summary for dashboard."""
    critical_count: int
    warning_count: int
    critical_pools: List[dict]
    warning_pools: List[dict]


class SystemSummary(BaseModel):
    """Storage system summary."""
    id: int
    name: str
    type: Optional[str]
    model: Optional[str]
    vendor: Optional[str]
    usable_capacity_tb: float
    available_capacity_tb: float
    used_capacity_tb: float
    utilization_pct: float
    pools: int
    volumes: int
    location: Optional[str]


class PoolSummary(BaseModel):
    """Storage pool summary."""
    id: int
    name: str
    storage_system: str
    usable_capacity_tb: float
    used_capacity_tb: float
    available_capacity_tb: float
    utilization_pct: float
    days_until_full: Optional[int]
    status: Optional[str]


class OverviewData(BaseModel):
    """Complete overview dashboard data."""
    kpis: KPIData
    alerts: AlertSummary
    top_systems: List[dict]
    utilization_distribution: List[dict]
    forecasting_data: List[dict]
    storage_types: List[dict]
    top_hosts: List[dict]
    savings_data: List[dict]
    treemap_data: List[dict]
    recommendations: List[dict]
    report_date: date


class HistoricalQuery(BaseModel):
    """Query parameters for historical data."""
    start_date: date
    end_date: date
    tenant_ids: Optional[List[int]] = None
    system_names: Optional[List[str]] = None
    pool_names: Optional[List[str]] = None


class HistoricalTrendData(BaseModel):
    """Historical trend data point."""
    date: date
    total_capacity_tb: float
    used_capacity_tb: float
    available_capacity_tb: float
    utilization_pct: float


# ============================================================================
# Storage System Detail Schemas
# ============================================================================

class StorageSystemOut(BaseModel):
    """Full storage system details."""
    id: int
    report_date: date
    name: str
    system_uuid: Optional[str]
    raw_capacity_gb: Optional[float]
    usable_capacity_gib: Optional[float]
    available_capacity_gib: Optional[float]
    utilization_pct: Optional[float]
    total_compression_ratio: Optional[float]
    data_reduction_gib: Optional[float]
    recent_growth_gib: Optional[float]
    pools: Optional[int]
    volumes: Optional[int]
    managed_disks: Optional[int]
    vendor: Optional[str]
    type: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    firmware: Optional[str]
    location: Optional[str]
    ip_address: Optional[str]
    last_successful_probe: Optional[datetime]
    
    class Config:
        from_attributes = True


class StorageSystemListItem(BaseModel):
    """Storage system list item for table view."""
    id: int
    name: str
    type: Optional[str]
    model: Optional[str]
    capacity_tb: float
    used_tb: float
    available_tb: float
    utilization_pct: float
    pools: int
    volumes: int
    location: Optional[str]
    
    class Config:
        from_attributes = True


# Update forward references
TokenResponse.model_rebuild()
