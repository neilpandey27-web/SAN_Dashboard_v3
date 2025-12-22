"""
SQLAlchemy ORM models for OneIT SAN Analytics Dashboard.
Includes all 8 core storage tables + application tables.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text,
    ForeignKey, Index, UniqueConstraint, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


# ============================================================================
# Association Tables (Many-to-Many)
# ============================================================================

user_tenants = Table(
    'user_tenants',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('tenant_id', Integer, ForeignKey('tenants.id', ondelete='CASCADE'), primary_key=True)
)


# ============================================================================
# Application Tables
# ============================================================================

class User(Base):
    """User accounts for authentication and authorization."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default='user')  # 'admin' or 'user'
    status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'active', 'deactivated'
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenants = relationship('Tenant', secondary=user_tenants, back_populates='users')
    user_tenants = relationship('UserTenant', back_populates='user', viewonly=True)
    activity_logs = relationship('UserActivityLog', back_populates='user')
    upload_logs = relationship('UploadLog', back_populates='user')
    acknowledged_alerts = relationship('Alert', back_populates='acknowledged_by_user')
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserTenant(Base):
    """Explicit junction table for user-tenant relationships with extra fields."""
    __tablename__ = 'user_tenant_junction'
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='user_tenants')
    tenant = relationship('Tenant', back_populates='user_tenants')


class Tenant(Base):
    """Tenant organizations for multi-tenant data isolation."""
    __tablename__ = 'tenants'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship('User', secondary=user_tenants, back_populates='tenants')
    user_tenants = relationship('UserTenant', back_populates='tenant', viewonly=True)
    pool_mappings = relationship('TenantPoolMapping', back_populates='tenant')
    host_mappings = relationship('HostTenantMapping', back_populates='tenant')


class TenantPoolMapping(Base):
    """Maps storage pools to tenants for filtering."""
    __tablename__ = 'tenant_pool_mappings'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    pool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_system: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    tenant = relationship('Tenant', back_populates='pool_mappings')
    
    __table_args__ = (
        UniqueConstraint('pool_name', 'storage_system', name='uq_pool_system'),
    )


class HostTenantMapping(Base):
    """Maps hosts to tenants for filtering."""
    __tablename__ = 'host_tenant_mappings'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    host_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    tenant = relationship('Tenant', back_populates='host_mappings')
    
    __table_args__ = (
        UniqueConstraint('host_name', name='uq_host_mapping'),
    )


class MdiskSystemMapping(Base):
    """Maps managed disks to storage systems."""
    __tablename__ = 'mdisk_system_mappings'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mdisk_name: Mapped[str] = mapped_column(String(255), nullable=False)
    system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('mdisk_name', name='uq_mdisk_mapping'),
    )


class Alert(Base):
    """Storage capacity alerts."""
    __tablename__ = 'alerts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_system: Mapped[str] = mapped_column(String(255), nullable=False)
    utilization_pct: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # 'warning', 'critical', 'emergency'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    days_until_full: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    acknowledged_by_user = relationship('User', back_populates='acknowledged_alerts')
    
    __table_args__ = (
        Index('ix_alerts_level', 'level'),
        Index('ix_alerts_acknowledged', 'acknowledged'),
    )


class UploadLog(Base):
    """Logs of data uploads."""
    __tablename__ = 'upload_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    rows_added: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='success')  # 'success', 'partial', 'failed'
    upload_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    skipped_records_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of full row data
    upload_statistics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object with detailed statistics
    
    user = relationship('User', back_populates='upload_logs')


class UserActivityLog(Base):
    """User activity audit trail."""
    __tablename__ = 'user_activity_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='activity_logs')
    
    __table_args__ = (
        Index('ix_activity_user_id', 'user_id'),
        Index('ix_activity_timestamp', 'timestamp'),
    )


# ============================================================================
# Core Storage Tables (8 tables from Excel/PDF schema)
# ============================================================================

class StorageSystem(Base):
    """
    Central hub for all IBM storage systems.
    Expected ~28 rows per report_date.
    """
    __tablename__ = 'storage_systems'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    system_uuid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upload_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('upload_logs.id'), nullable=True)
    
    # Capacity metrics
    raw_capacity_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    usable_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    available_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    written_capacity_limit_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    available_written_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_provisioned_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mapped_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unmapped_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Compression metrics (parsed from ratio format like "1.3 : 1" to float 1.3)
    total_compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pool_compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_reduction_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_reduction_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Growth metrics
    recent_growth_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Counts
    pools: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    volumes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unprotected_volumes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    managed_disks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fc_ports: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Cache
    read_cache_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    write_cache_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # System info
    compressed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number_enclosure: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    firmware: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time_zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Probe info
    last_successful_probe: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_successful_monitor: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    storage_pools = relationship('StoragePool', back_populates='system')
    capacity_volumes = relationship('CapacityVolume', back_populates='system')
    capacity_disks = relationship('CapacityDisk', back_populates='system')
    
    __table_args__ = (
        UniqueConstraint('report_date', 'name', name='uq_system_report_name'),
        Index('ix_storage_systems_name', 'name'),
        Index('ix_storage_systems_vendor_type', 'vendor', 'type'),
    )


class StoragePool(Base):
    """
    Storage pools with hierarchical structure (parent_name for self-reference).
    Expected ~87 rows per report_date (29 child, 58 parent).
    """
    __tablename__ = 'storage_pools'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_system_id: Mapped[int] = mapped_column(Integer, ForeignKey('storage_systems.id'), nullable=False)
    storage_system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('upload_logs.id'), nullable=True)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    parent_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Self-reference for hierarchy
    
    # Capacity metrics
    usable_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    used_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    available_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mapped_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unmapped_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Utilization (calculated)
    utilization_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Compression (parsed from ratio format like "1.3 : 1" to float 1.3)
    total_compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pool_compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Growth
    recent_growth_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recent_fill_rate_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Other
    zero_capacity: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    volumes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    node: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pool_attributes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    drives: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raid_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    solid_state: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    tier_distribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_data_collection: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    system = relationship('StorageSystem', back_populates='storage_pools')
    
    __table_args__ = (
        UniqueConstraint('report_date', 'name', 'storage_system_name', name='uq_pool_report_name_system'),
        Index('ix_storage_pools_system', 'storage_system_name'),
        Index('ix_storage_pools_parent', 'parent_name'),
        Index('ix_storage_pools_utilization', 'utilization_pct'),
    )


class CapacityVolume(Base):
    """
    Granular volume capacity data.
    Expected ~60,584 rows per report_date.
    """
    __tablename__ = 'capacity_volumes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    volume_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_system_id: Mapped[int] = mapped_column(Integer, ForeignKey('storage_systems.id'), nullable=False)
    storage_system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pool_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    upload_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('upload_logs.id'), nullable=True)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    storage_virtual_machine: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    copy_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    volume_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Capacity
    provisioned_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    used_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    available_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    real_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    written_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reserved_volume_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overhead_used_capacity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Utilization
    used_capacity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    written_capacity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shortfall_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Properties
    thin_provisioned: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    raid_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    node: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    virtual_disk_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    compression_savings_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Tier info
    scm_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tier0_flash_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tier_distribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hosts (comma-separated list, parsed to junction table)
    hosts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    last_data_collection: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    system = relationship('StorageSystem', back_populates='capacity_volumes')
    
    __table_args__ = (
        UniqueConstraint('report_date', 'volume_name', 'storage_system_name', 'pool_name', name='uq_volume_report_name_system_pool'),
        Index('ix_capacity_volumes_pool', 'pool_name'),
        Index('ix_capacity_volumes_system', 'storage_system_name'),
        Index('ix_capacity_volumes_utilization', 'used_capacity_pct'),
    )


class CapacityHost(Base):
    """
    Host capacity information.
    Expected ~2,388 rows per report_date.
    Note: Inventory_Hosts table removed as redundant - all data present in Capacity_Hosts.
    """
    __tablename__ = 'capacity_hosts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    host_uuid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upload_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('upload_logs.id'), nullable=True)
    
    condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_collection: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    probe_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    performance_monitor_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    san_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    used_san_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    primary_provisioned_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    primary_used_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    last_successful_probe: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_successful_monitor: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('report_date', 'name', name='uq_cap_host_report_name'),
        Index('ix_capacity_hosts_name', 'name'),
    )


class CapacityDisk(Base):
    """
    Disk capacity information.
    Expected ~70 rows per report_date.
    Note: Inventory_Disks table removed as redundant - all data present in Capacity_Disks.
    """
    __tablename__ = 'capacity_disks'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_system_id: Mapped[int] = mapped_column(Integer, ForeignKey('storage_systems.id'), nullable=False)
    storage_system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pool: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    upload_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('upload_logs.id'), nullable=True)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    easy_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    easy_tier_load: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    available_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    used_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Calculated: capacity_gib - available_capacity_gib
    
    pool_compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    drive_compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    disk_class: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raid_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    volumes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Backend references
    back_end_storage_system: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    back_end_pool: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    back_end_volume: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    last_data_collection: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    system = relationship('StorageSystem', back_populates='capacity_disks')
    
    __table_args__ = (
        # Unique constraint: report_date + name + storage_system + pool
        # Allows same disk name in different pools on same system
        # NULL names are allowed and won't violate uniqueness (NULL != NULL in SQL)
        UniqueConstraint('report_date', 'name', 'storage_system_name', 'pool', name='uq_cap_disk_report_name_system_pool'),
        Index('ix_capacity_disks_report_system', 'report_date', 'storage_system_name'),
    )


class Department(Base):
    """
    Department/organizational structure.
    Expected ~5 rows per report_date.
    """
    __tablename__ = 'departments'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('upload_logs.id'), nullable=True)
    
    block_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    block_available_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    block_used_capacity_gib: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    applications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dept_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('report_date', 'name', name='uq_dept_report_name'),
    )



