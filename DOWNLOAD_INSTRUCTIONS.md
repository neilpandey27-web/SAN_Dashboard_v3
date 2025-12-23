# 📦 SAN Dashboard v3 - Download Package

## 📥 Download Information

**File**: `SAN_Dashboard_v3_Latest.zip`
**Size**: 629 KB (compressed)
**Date**: December 23, 2024
**Version**: 6.2.0

---

## ✨ What's Included in This Release

### 🆕 Latest Changes (Dec 23, 2024)
1. **✅ Fixed Comparison Table Structure**
   - Changed from System-based to Tenant-based organization
   - New columns: Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %
   - Properly calculates simple and weighted averages per tenant

2. **✅ Enhanced Data Organization**
   - Tenant inference from pool names (Pool1-5 → Tenant X, Pool3 → Tenant Y, etc.)
   - Color-coded utilization badges (Red >80%, Yellow >70%, Green ≤70%)
   - Sorted display with UNKNOWN tenants at the end

3. **✅ Debug Improvements**
   - Added console logging for treemap data
   - Enhanced error tracking for blank treemap issues

### 📂 Package Contents

```
SAN_Dashboard_v3_Latest.zip
├── backend/                    # Python FastAPI backend
│   ├── app/                    # Application code
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core configuration
│   │   ├── db/                # Database models & schemas
│   │   └── utils/             # Utility functions
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend Docker config
│
├── frontend/                   # Next.js React frontend
│   ├── app/                   # Next.js 13+ app directory
│   │   ├── overview/         # Dashboard overview page
│   │   ├── systems/          # Systems management
│   │   ├── historical/       # Historical data view
│   │   ├── db-mgmt/          # Database management
│   │   ├── user-mgmt/        # User management
│   │   └── auth/             # Authentication pages
│   ├── components/           # React components
│   ├── contexts/             # React contexts (TenantContext)
│   ├── lib/                  # API client & auth
│   ├── styles/               # Global CSS
│   ├── package.json          # Node dependencies
│   └── Dockerfile            # Frontend Docker config
│
├── scripts/                    # Utility scripts
│   ├── db_init.sql           # Database initialization
│   ├── backup_database.sh    # Backup script
│   └── update.sh             # Update script
│
├── migrations/                 # SQL migrations
├── db_files/                   # Database file storage
├── docker-compose.yml          # Docker Compose config
├── SETUP_GUIDE_LOCAL.md       # 👈 START HERE!
├── README.md                   # Project overview
├── DATABASE_DOCUMENTATION.md   # Database schema docs
├── TECHNICAL_SPECIFICATIONS.md # Technical details
└── DEPLOYMENT_GUIDE.md        # Deployment instructions
```

---

## 🚀 Quick Start

### 1. Extract the ZIP
```bash
unzip SAN_Dashboard_v3_Latest.zip
cd SAN_Dashboard_v3_Latest/
```

### 2. Read the Setup Guide
Open and follow: **`SETUP_GUIDE_LOCAL.md`**

This guide includes:
- Prerequisites (Node.js, Python, PostgreSQL)
- Step-by-step installation instructions
- Environment configuration
- Database setup
- Running the application
- Troubleshooting tips

### 3. Quick Setup Summary

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Configure .env file
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
# Configure .env.local file
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Node.js** v18+ installed
- [ ] **Python** 3.10+ installed
- [ ] **PostgreSQL** v14+ installed and running
- [ ] **Git** installed (optional, for version control)
- [ ] At least 2GB free disk space
- [ ] Ports 3000 and 8000 available

---

## 🎯 Key Features

### Dashboard Overview
- 📊 **KPI Cards**: Total capacity, used capacity, savings
- 📈 **Capacity Forecasting**: Predict pool exhaustion
- 🌳 **Treemap Visualization**: Hierarchical capacity view
- 🚨 **Critical Alerts**: Real-time pool monitoring
- 💡 **Intelligent Recommendations**: Automated suggestions

### Tenant Management
- 🏢 **Multi-tenant Support**: Filter by tenant organization
- 👥 **User Management**: Role-based access control
- 🔐 **Secure Authentication**: JWT-based auth system

### Data Management
- 📤 **Excel Upload**: Import storage data from Excel files
- 📊 **Historical Tracking**: Track capacity over time
- 🔄 **Automated Processing**: Background data processing

### Comparison Table (NEW!)
- **Tenant-level Organization**: View data by tenant
- **Simple Average**: Average of pool utilization percentages
- **Weighted Average**: Capacity-weighted utilization
- **Multi-system Support**: See systems per tenant

---

## 📚 Documentation Files

| File | Description |
|------|-------------|
| `SETUP_GUIDE_LOCAL.md` | Complete local setup instructions |
| `README.md` | Project overview and quick reference |
| `DATABASE_DOCUMENTATION.md` | Database schema and models |
| `TECHNICAL_SPECIFICATIONS.md` | Technical architecture details |
| `DEPLOYMENT_GUIDE.md` | Production deployment guide |
| `DASHBOARD_CHART_BLOCKS.md` | Chart documentation |
| `QUICK_REFERENCE.md` | Quick command reference |

---

## 🆘 Getting Help

### Common Issues

**"Module not found" errors:**
- Run `npm install` in frontend directory
- Run `pip install -r requirements.txt` in backend directory

**"Database connection failed":**
- Ensure PostgreSQL is running
- Check DATABASE_URL in backend/.env
- Verify database exists: `psql -U postgres -l`

**"Port already in use":**
- Kill existing process on port 3000 or 8000
- Or use different ports in configuration

### Support Resources

1. **Read SETUP_GUIDE_LOCAL.md** - Comprehensive setup instructions
2. **Check Browser Console** - Look for frontend errors
3. **Check Backend Terminal** - Look for API errors
4. **Verify Environment Variables** - Ensure all .env files are correct

---

## 🔄 Updating

To update to the latest version:

```bash
# Backup your database first!
cd backend
python scripts/backup_database.py

# Pull latest changes (if using git)
git pull origin main

# Update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Run migrations
cd backend && alembic upgrade head

# Restart services
```

---

## 🛡️ Security Notes

**For Development:**
- Default credentials are weak - change them!
- `.env` files are excluded from git
- Use different secrets for each environment

**For Production:**
- Change all default passwords
- Use strong SECRET_KEY values
- Enable HTTPS
- Use environment-specific configurations
- Regular security updates

---

## 📊 Sample Data

The package includes a sample Excel file in `backend/test_upload.xlsx` for testing.

**Required Excel Sheets:**
- Storage_Systems
- Storage_Pools
- Capacity_Volumes
- Inventory_Hosts
- Capacity_Hosts
- Inventory_Disks
- Capacity_Disks
- Departments

---

## 🎉 What's Next?

After successful setup:

1. ✅ Upload your storage data via Database Management
2. ✅ Create tenant organizations
3. ✅ Invite team members
4. ✅ Configure tenant-pool mappings
5. ✅ Explore the dashboard and analytics

---

## 📝 Version History

### v6.2.0 (Dec 23, 2024) - Current Release
- Fixed comparison table to show tenant-level breakdown
- Enhanced tenant data organization
- Added debug logging for treemap

### v6.1.0
- Added tenant filtering capabilities
- Enhanced dropdown performance

### v6.0.0
- Multi-tenant support
- Enhanced security features

### v5.0.0
- Initial stable release
- Core dashboard functionality

---

**🚀 Ready to Start? Open `SETUP_GUIDE_LOCAL.md` and follow the instructions!**

---

**Package Created**: December 23, 2024
**Maintained By**: SAN Dashboard Development Team
**License**: See LICENSE file for details
