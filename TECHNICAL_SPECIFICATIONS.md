# 📘 Technical Specifications and Features

**Version:** 2.0.0  
**Last Updated:** December 11, 2025

---

## 📋 Table of Contents

1. [Features Overview](#features-overview)
2. [Technology Stack](#technology-stack)
3. [Application Architecture](#application-architecture)
4. [API Endpoints](#api-endpoints)
5. [Data Models](#data-models)
6. [Metrics and Calculations](#metrics-and-calculations)
7. [Excel Upload Format](#excel-upload-format)
8. [Future Enhancements](#future-enhancements)

---

## 🎯 Features Overview

### **✅ Implemented Features (December 2025)**

#### **1. Enhanced Dashboard**
- **Overview Tab:**
  - Total capacity, used, available storage metrics
  - Utilization percentage with color-coded indicators
  - Interactive treemaps for pool and disk capacity visualization
  - Critical capacity alerts and forecasting
  - Duration filters (3, 6, 12 months, All time)
  - PDF export capability

- **Historical Data Tab:**
  - Capacity growth tracking over time
  - Monthly/quarterly growth rates
  - Trend analysis and projections
  - Historical utilization charts

- **Compression Tab:**
  - Compression ratio metrics
  - Deduplication savings
  - Virtual capacity calculations
  - Data reduction statistics

#### **2. Storage Systems (with Drill-Down)** ✅ **Recently Fixed**
- **Correct 7-column display**:
  - System Name
  - Capacity (TB)
  - Used (TB)
  - Available (TB)
  - Util %
  - Pools
  - Volumes
- **Three-level drill-down hierarchy**:
  1. Storage Systems (aggregated)
  2. Storage Pools (by system)
  3. Capacity Volumes (by pool)
- Breadcrumb navigation
- Color-coded utilization badges
- Search and filter functionality
- Sortable columns
- Pagination support

#### **3. Database Management** ✅ **Recently Enhanced**
- **Excel Upload:**
  - Single-file upload for all data types
  - Supports multiple sheets in one workbook
  - Automatic data extraction and classification
  - Duplicate detection and handling
  - Upload history tracking
  - Success/failure statistics
  - Detailed logs with skipped records

- **Tables View:**
  - View all database tables
  - Data and Schema tabs
  - **Tooltips on Schema View** ✅ (Column descriptions on hover)
  - **CSV Download** ✅ (Export any table data)
  - Row counts and data preview
  - Search and filter

- **Upload History:**
  - Track all uploads with timestamps
  - Success/failure status
  - Records processed count
  - Error logging
  - View detailed logs

#### **4. Storage Pools**
- Pool-level capacity information
- Utilization tracking
- Compression metrics per pool
- Relationship to parent systems
- Detailed capacity breakdowns
- RAID level information
- Tier classification

#### **5. Capacity Volumes**
- Individual volume information
- Thin provisioning status
- Capacity and usage metrics
- Host mappings
- Compression savings
- RAID level and virtual disk type
- Volume status tracking

#### **6. Capacity Disks**
- Physical disk information
- Serial number tracking
- Capacity and usage by disk
- System association
- Disk class and type
- RAID level configuration
- Condition monitoring

#### **7. Capacity Hosts**
- Host server inventory
- Storage allocation per host
- Block capacity metrics
- Applications running
- Total provisioned capacity
- Status tracking

#### **8. Alerts**
- Threshold-based alerting system
- High utilization warnings (>80%)
- Critical alerts (>90%)
- Email notifications (configurable)
- Alert history and status tracking
- Severity levels
- Acknowledgment system

#### **9. User Management**
- User authentication (JWT-based)
- Role-based access control (Admin, User, Viewer)
- User approval workflow
- Password reset functionality
- Session management
- User activity tracking
- Permissions management

#### **10. Reports**
- Generate capacity reports
- Utilization summaries
- Export to PDF/Excel
- Scheduled report generation
- Historical trend reports
- Custom date ranges

---

## 💻 Technology Stack

### **Frontend**
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript 5.0+
- **Styling**: 
  - Bootstrap 5.3
  - React Bootstrap
  - Custom CSS
- **Data Visualization**:
  - Plotly.js (Treemaps, Charts)
  - Chart.js
- **HTTP Client**: Axios
- **PDF Generation**: jsPDF, html2canvas
- **State Management**: React hooks (useState, useEffect)
- **Routing**: Next.js App Router

### **Backend**
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.9+
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Excel Processing**: 
  - openpyxl (reading/writing Excel)
  - pandas (data transformation)
- **Database Migration**: Alembic
- **CORS**: fastapi-cors-middleware
- **Environment**: python-dotenv

### **Database**
- **Production**: PostgreSQL 15+
- **Development**: SQLite 3
- **Connection Pooling**: SQLAlchemy pool
- **Migrations**: Alembic

### **DevOps**
- **Containerization**: Docker, Docker Compose
- **Reverse Proxy**: Nginx (optional)
- **Process Management**: PM2 (optional)
- **CI/CD**: GitHub Actions (optional)

---

## 🏗️ Application Architecture

### **Overall Architecture**

```
┌──────────────────────────────────────────────┐
│           Client (Browser)                   │
│                                              │
│  • Chrome, Firefox, Safari, Edge             │
│  • JavaScript Runtime                        │
│  • LocalStorage for JWT                      │
└────────────────┬─────────────────────────────┘
                 │ HTTPS/HTTP
                 │
┌────────────────▼─────────────────────────────┐
│         Frontend (Next.js)                   │
│         Port: 3000                           │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Pages (React Components)            │   │
│  │  • Dashboard (Overview, Historical)  │   │
│  │  • Storage Systems (Drill-down)      │   │
│  │  • Database Management (Upload)      │   │
│  │  • User Management                   │   │
│  │  • Alerts, Reports                   │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  API Client (Axios)                  │   │
│  │  • Authentication interceptor        │   │
│  │  • Error handling                    │   │
│  │  • Base URL configuration            │   │
│  └─────────────────────────────────────┘   │
└────────────────┬─────────────────────────────┘
                 │ REST API (JSON)
                 │ /api/v1/*
┌────────────────▼─────────────────────────────┐
│         Backend (FastAPI)                    │
│         Port: 8000                           │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  API Routes (/api/v1/)               │   │
│  │  • /auth (Login, Signup, Logout)     │   │
│  │  • /data (Systems, Pools, Volumes)   │   │
│  │  • /alerts (Get, Create, Update)     │   │
│  │  • /users (CRUD operations)          │   │
│  │  • /mappings (Tenant, Host)          │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Business Logic                      │   │
│  │  • Data processing                   │   │
│  │  • Excel parsing                     │   │
│  │  • Metrics calculation               │   │
│  │  • Alert generation                  │   │
│  │  • Authentication/Authorization      │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Database Layer (SQLAlchemy)         │   │
│  │  • ORM Models                        │   │
│  │  • Query optimization                │   │
│  │  • Transaction management            │   │
│  │  • Connection pooling                │   │
│  └─────────────────────────────────────┘   │
└────────────────┬─────────────────────────────┘
                 │ SQL
                 │
┌────────────────▼─────────────────────────────┐
│         Database (PostgreSQL/SQLite)         │
│         Port: 5432 (PostgreSQL)              │
│                                              │
│  Tables:                                     │
│  • storage_systems                           │
│  • storage_pools                             │
│  • capacity_volumes                          │
│  • capacity_disks                            │
│  • capacity_hosts                            │
│  • departments                               │
│  • tenants                                   │
│  • users                                     │
│  • alerts                                    │
│  • upload_logs                               │
│  • host_tenant_mappings                      │
│  • tenant_pool_mappings                      │
└──────────────────────────────────────────────┘
```

### **Request Flow Example**

```
User clicks "Storage Systems" → 

Frontend:
  1. Route: /systems
  2. Component: systems/page.tsx
  3. API call: apiClient.getStorageSystems()
  
Backend:
  4. Endpoint: GET /api/v1/data/systems
  5. Controller: backend/app/api/v1/data.py
  6. Query: db.query(StorageSystem).all()
  
Database:
  7. Execute: SELECT * FROM storage_systems
  8. Return: List of storage system records
  
Backend:
  9. Transform: Format data to JSON
  10. Return: { items: [...], total: 100, page: 1 }

Frontend:
  11. Receive: JSON response
  12. Render: Display table with data
  13. User sees: Storage systems list
```

---

## 🔌 API Endpoints

### **Authentication (/api/v1/auth)**

- `POST /signup` - Create new user account
- `POST /login` - Login and get JWT token
- `POST /logout` - Logout (invalidate token)
- `GET /me` - Get current user info

### **Data Endpoints (/api/v1/data)**

**Storage Systems**:
- `GET /systems` - List all storage systems (with pagination, filtering)
- `GET /systems/{system_name}/pools` - Get pools for a system
- `GET /pools/{pool_name}/volumes` - Get volumes for a pool
- `GET /enhanced-overview` - Get dashboard overview data

**Database Management**:
- `POST /upload` - Upload Excel file
- `GET /upload-logs` - Get upload history
- `GET /tables` - List all database tables
- `GET /tables/{table_name}/schema` - Get table schema
- `GET /tables/{table_name}/data` - Get table data
- `DELETE /upload-logs/{log_id}` - Delete upload log
- `GET /upload-logs/{log_id}/details` - Get detailed upload log

**Historical Data**:
- `GET /historical/capacity` - Get historical capacity data
- `GET /historical/utilization` - Get historical utilization trends
- `GET /historical/growth` - Get capacity growth trends

### **Alerts (/api/v1/alerts)**

- `GET /` - Get all alerts (with filtering)
- `POST /` - Create new alert
- `PUT /{alert_id}` - Update alert
- `DELETE /{alert_id}` - Delete alert
- `POST /{alert_id}/acknowledge` - Acknowledge alert

### **Users (/api/v1/users)**

- `GET /` - List all users (admin only)
- `GET /{user_id}` - Get user by ID
- `POST /approve/{user_id}` - Approve user registration
- `DELETE /{user_id}` - Delete user

### **Mappings (/api/v1/mappings)**

- `GET /tenant-pool` - Get tenant-pool mappings
- `POST /tenant-pool` - Create tenant-pool mapping
- `DELETE /tenant-pool/{mapping_id}` - Delete mapping
- `POST /host-tenant/upload` - Upload host-tenant CSV

---

## 📊 Data Models

### **StorageSystem**
```python
class StorageSystem(Base):
    id: int (PK)
    name: str (Unique with report_date)
    report_date: date
    vendor: str
    type: str
    model: str
    serial_number: str
    firmware: str
    raw_capacity_gb: float
    usable_capacity_gib: float
    available_capacity_gib: float
    total_compression_ratio: float
    data_reduction_ratio: float
    pools: int  # Count
    volumes: int  # Count
    managed_disks: int  # Count
```

### **StoragePool**
```python
class StoragePool(Base):
    id: int (PK)
    name: str (Unique with storage_system, report_date)
    report_date: date
    storage_system: str (FK)
    status: str
    usable_capacity_gib: float
    available_capacity_gib: float
    utilization_pct: float  # Calculated
    tier: str
    raid_level: str
    compression_enabled: bool
```

### **CapacityVolume**
```python
class CapacityVolume(Base):
    id: int (PK)
    name: str (Unique with storage_system, report_date)
    report_date: date
    storage_system: str (FK)
    pool: str (FK)
    status: str
    capacity_gib: float
    used_capacity_gib: float
    available_capacity_gib: float
    thin_provisioned: bool
    raid_level: str
    virtual_disk_type: str
    compression_savings_pct: float
```

### **User**
```python
class User(Base):
    id: int (PK)
    email: str (Unique)
    hashed_password: str
    full_name: str
    role: str  # Admin, User, Viewer
    is_approved: bool
    is_active: bool
    created_at: datetime
```

---

## 📐 Metrics and Calculations

### **Utilization Percentage**
```python
utilization_pct = (used_capacity_gib / usable_capacity_gib) × 100
```

### **Data Reduction**
```python
data_reduction_gib = written_capacity_gib - used_capacity_gib
data_reduction_ratio = written_capacity_gib / used_capacity_gib
```

### **Compression Savings**
```python
compression_savings_gib = (1 - (1 / compression_ratio)) × capacity_gib
compression_savings_pct = (savings / capacity_gib) × 100
```

### **Volume Written Percentage**
```python
written_capacity_pct = (written_capacity_gib / real_capacity_gib) × 100
```

### **Pool Aggregations**
```python
# Sum all pools for a system
system_total_capacity = SUM(pools.usable_capacity_gib)
system_total_used = SUM(pools.used_capacity_gib)
system_utilization = (system_total_used / system_total_capacity) × 100
```

---

## 📁 Excel Upload Format

### **Required Sheets**

The Excel file must contain these sheets:

1. **Storage_Systems**
2. **Storage_Pools**
3. **Capacity_Volumes**
4. **Capacity_Hosts**
5. **Capacity_Disks**
6. **Departments**

### **Example: Storage_Systems Sheet**

| Storage system | Vendor | Type | Model | Serial number | Raw capacity (GB) | Usable capacity (GiB) | Available capacity (GiB) | Compression ratio | ... |
|---------------|--------|------|-------|---------------|-------------------|----------------------|--------------------------|------------------|-----|
| FS92K-A1      | IBM    | Flash| 92K   | SN12345       | 100000           | 95000                | 25000                   | 2.5              | ... |
| FS7K-B2       | IBM    | Flash| 7K    | SN67890       | 50000            | 47500                | 15000                   | 2.0              | ... |

### **Data Processing**

1. **Capacity Unit Conversion**:
   - All capacity values converted to GiB
   - Source units detected automatically (GB, TB, PB)

2. **Duplicate Handling**:
   - Unique key: `(name, report_date)`
   - If duplicate: Update existing record
   - If new: Insert new record

3. **Validation**:
   - Required fields checked
   - Data types validated
   - Range checks for percentages
   - NULL handling

4. **Calculated Fields**:
   - Utilization percentages
   - Compression savings
   - Data reduction metrics

---

## 🚀 Future Enhancements

### **Planned Features**

1. **Advanced Analytics**:
   - Predictive capacity forecasting using ML
   - Anomaly detection for usage patterns
   - Cost optimization recommendations
   - Trend analysis dashboards

2. **Enhanced Reporting**:
   - Customizable report templates
   - Automated report scheduling
   - Multi-format export (PDF, Excel, CSV, JSON)
   - Email distribution lists

3. **Integration Capabilities**:
   - REST API for third-party integrations
   - Webhook notifications
   - SNMP trap support
   - Syslog integration
   - ServiceNow connector

4. **Advanced Visualization**:
   - 3D capacity maps
   - Heat maps for utilization
   - Sankey diagrams for data flow
   - Real-time monitoring dashboards

5. **Mobile Support**:
   - Responsive design improvements
   - Native mobile app (iOS/Android)
   - Push notifications
   - Mobile-optimized dashboards

6. **Security Enhancements**:
   - Two-factor authentication (2FA)
   - Single Sign-On (SSO) integration
   - LDAP/Active Directory integration
   - API key management
   - Audit logging

7. **Performance Optimization**:
   - Data caching layer (Redis)
   - Background job processing (Celery)
   - Query optimization
   - CDN integration for static assets

8. **Additional Data Sources**:
   - Direct IBM Spectrum Control integration
   - Dell EMC Unisphere integration
   - NetApp OnCommand integration
   - Pure Storage integration
   - HPE 3PAR integration

---

## 📚 Related Documentation

- `DEPLOYMENT_GUIDE.md` - Setup and deployment instructions
- `FIXES_AND_UPDATES.md` - Recent fixes and updates
- `DATABASE_DOCUMENTATION.md` - Database schemas and data persistence
- `README.md` - Project overview

---

## 🆘 Support

For technical questions or feature requests:

1. Check the API documentation: http://localhost:8000/api/docs
2. Review this technical specification
3. Check related documentation files
4. Submit an issue via GitHub (if applicable)

---

**Status**: ✅ Complete technical specifications covering features, architecture, APIs, and future enhancements

**Last Updated**: December 11, 2025
