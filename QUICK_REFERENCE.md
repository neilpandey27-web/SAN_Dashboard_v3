# OneIT SAN Analytics - Quick Reference Cheat Sheet

**Version:** 2.0.0 | **Date:** December 11, 2025

---

## 🚀 One-Command Start

```bash
cd /home/user/webapp/webapp && docker compose up -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000  
- API Docs: http://localhost:8000/api/docs

**Login:**
- Email: `admin@company.com`
- Password: `admin123`

---

## 📊 Architecture at a Glance

```
Browser → Next.js (3000) → FastAPI (8000) → PostgreSQL (5432)
         React 18         Python 3.11      Postgres 15
```

---

## 📁 Directory Map

```
webapp/
├── backend/           # Python FastAPI app (141MB)
│   ├── app/          # Source code
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # Next.js app (964KB)
│   ├── app/          # Pages (App Router)
│   ├── components/   # React components
│   ├── package.json
│   └── Dockerfile
├── db_files/          # SQLite (dev) / empty (prod uses volume)
├── docker-compose.yml # ⭐ Main orchestration file
└── README.md          # Start here
```

---

## 🐳 Docker Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f
docker compose logs backend -f
docker compose logs frontend -f

# Rebuild
docker compose build --no-cache
docker compose up -d

# Restart single service
docker compose restart backend

# Shell access
docker compose exec backend /bin/bash
docker compose exec frontend /bin/sh

# Database access
docker compose exec db psql -U postgres -d storage_insights

# Remove everything (DESTRUCTIVE!)
docker compose down -v
```

---

## 🗄️ Database Tables

### Storage Tables (Data from Excel)
1. **storage_systems** (~28 rows/report)
2. **storage_pools** (~87 rows/report)
3. **capacity_volumes** (~60,584 rows/report) ⚠️ Large!
4. **capacity_disks** (~70 rows/report)
5. **capacity_hosts** (~2,388 rows/report)

### Application Tables
6. **users** - Authentication
7. **tenants** - Multi-tenant isolation
8. **alerts** - Capacity warnings
9. **upload_logs** - Upload audit trail
10. **tenant_pool_mappings** - Tenant filtering
11. **host_tenant_mappings** - Host filtering

---

## 📤 Excel Upload Format

**Required Sheets:**
1. Storage_Systems
2. Storage_Pools
3. Capacity_Volumes
4. Capacity_Hosts
5. Capacity_Disks
6. Departments
7. Inventory_Hosts (merged with Capacity_Hosts)
8. Inventory_Disks (merged with Capacity_Disks)

**Key Columns (Example - Storage_Systems):**
- Storage system (name)
- Report date
- Raw capacity (GB)
- Usable capacity (GiB)
- Available capacity (GiB)
- Compression ratio
- Pools, Volumes, Managed disks (counts)

---

## 🔑 API Endpoints Quick Reference

### Authentication
```
POST   /api/v1/auth/login       - Get JWT token
POST   /api/v1/auth/signup      - Register new user
GET    /api/v1/auth/me          - Get current user
```

### Data Management
```
POST   /api/v1/data/upload              - Upload Excel (admin)
GET    /api/v1/data/enhanced-overview   - Dashboard data
GET    /api/v1/data/systems             - Storage systems
GET    /api/v1/data/systems/{name}/pools - Pools for system
GET    /api/v1/data/pools/{name}/volumes - Volumes for pool
GET    /api/v1/data/tables              - List all tables
GET    /api/v1/data/tables/{name}/data  - Table data
GET    /api/v1/data/upload-logs         - Upload history
```

### Alerts
```
GET    /api/v1/alerts/          - List alerts
POST   /api/v1/alerts/          - Create alert
PUT    /api/v1/alerts/{id}      - Update alert
DELETE /api/v1/alerts/{id}      - Delete alert
```

### Users (Admin Only)
```
GET    /api/v1/users/           - List users
POST   /api/v1/users/approve/{id} - Approve user
DELETE /api/v1/users/{id}       - Delete user
```

---

## 🎨 Frontend Pages

```
/                    → Redirects to /overview
/auth/login          → Login page
/overview            → Dashboard (KPIs, treemaps)
/historical          → Historical trends
/systems             → Storage systems (3-level drill-down)
/db-mgmt             → Database management (upload + tables)
/user-mgmt           → User management (admin only)
/reports             → Report generation
```

---

## 🔐 Authentication Flow

```
1. POST /api/v1/auth/login
   { email, password }
   
2. Response:
   { 
     access_token: "eyJ...",
     token_type: "bearer",
     user: { id, email, role }
   }
   
3. Frontend stores token in localStorage
   
4. All requests include header:
   Authorization: Bearer eyJ...
```

---

## ⚙️ Environment Variables

### Backend (.env)
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/storage_insights
SECRET_KEY=change-me-in-production
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker Override
```bash
# In docker-compose.yml
NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
```

---

## 🐛 Troubleshooting Quick Fixes

### Frontend can't reach backend
```yaml
# docker-compose.yml frontend section
environment:
  - NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### CORS errors
```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://host.docker.internal:3000",
    "http://127.0.0.1:3000"
]
```

### Database not persisting
```yaml
# docker-compose.yml
volumes:
  postgres_data:  # ← Must be defined

services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data  # ← Must be used
```

### Port already in use
```bash
# Kill process on port
sudo lsof -ti:3000 | xargs kill -9
sudo lsof -ti:8000 | xargs kill -9

# Or change ports in docker-compose.yml
ports:
  - "3001:3000"  # Use 3001 instead
```

---

## 📈 Key Metrics

### Database Scale
- Storage Systems: ~28 per report
- Storage Pools: ~87 per report
- Capacity Volumes: ~60,584 per report ⚠️
- Capacity Disks: ~70 per report
- Capacity Hosts: ~2,388 per report

### Performance
- Upload processing: 10-60 seconds (depends on file size)
- Dashboard load: < 2 seconds (with 60k volumes)
- Page navigation: < 1 second

### Capacity
- Max file upload: 50MB
- Database size: ~500MB with full data
- Docker images: ~1.5GB total

---

## 🔧 Default Credentials

**Admin Account:**
```
Email: admin@company.com
Password: admin123
Role: admin
```

**Default Tenants:**
- BTC
- HMC
- ISST
- HST
- PERFORMANCE
- UNKNOWN

⚠️ **Change admin password in production!**

---

## 📚 Documentation Files

1. **README.md** - Project overview (start here)
2. **DEPLOYMENT_GUIDE.md** - Complete setup guide
3. **DATABASE_DOCUMENTATION.md** - Database details
4. **TECHNICAL_SPECIFICATIONS.md** - Features & APIs
5. **FIXES_AND_UPDATES.md** - Recent changes
6. **DOCUMENTATION_INDEX.md** - Navigation guide
7. **CODEBASE_ANALYSIS.md** - This analysis (comprehensive)
8. **QUICK_REFERENCE.md** - This cheat sheet

---

## 🎯 Common Tasks

### First-Time Setup
```bash
cd webapp
docker compose up -d
# Wait 30 seconds for DB initialization
# Open http://localhost:3000
# Login as admin@company.com / admin123
# Go to Database Management
# Upload Excel file
```

### Upload Data
```
1. Login as admin
2. Navigate to "Database Management"
3. Click "Upload Excel File"
4. Select your .xlsx file
5. Wait for processing
6. Check "Upload History" for results
```

### View Dashboard
```
1. Navigate to "Overview"
2. View KPIs (capacity, utilization)
3. Explore treemaps (interactive)
4. Check alerts (if any)
```

### Drill Down
```
1. Navigate to "Storage Systems"
2. Click on a system name
3. View pools for that system
4. Click on a pool name
5. View volumes for that pool
```

### Export Data
```
1. Navigate to "Database Management"
2. Select a table from dropdown
3. Click "Data" tab
4. Click "Download CSV" button
```

---

## 🆘 Emergency Commands

### Container won't start
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs -f
```

### Database is corrupted
```bash
# CAUTION: Deletes all data!
docker compose down -v
docker compose up -d
# Re-upload Excel data
```

### Frontend shows blank page
```bash
# Check browser console (F12)
# Check frontend logs
docker compose logs frontend

# Common issue: API URL wrong
# Fix in docker-compose.yml:
# NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
```

### Backend crashes on upload
```bash
# Check logs
docker compose logs backend

# Common causes:
# 1. Invalid Excel format
# 2. Missing required columns
# 3. Database connection lost
# 4. Out of memory (large file)
```

---

## 📞 Getting Help

1. **Check logs first:** `docker compose logs -f`
2. **Review documentation:** Start with README.md
3. **Check API docs:** http://localhost:8000/api/docs
4. **Browser console:** F12 for frontend errors
5. **Database state:** `docker compose exec db psql -U postgres -d storage_insights`

---

## ✅ Health Check

```bash
# Verify all services running
docker compose ps

# Should show:
# storage_insights_db       running (healthy)
# storage_insights_backend  running
# storage_insights_frontend running

# Quick test
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

curl http://localhost:3000
# Should return HTML
```

---

## 🎓 Learning Path

1. **Day 1:** Read README.md, start Docker, login, explore UI
2. **Day 2:** Upload sample Excel, view dashboard, explore drill-down
3. **Day 3:** Read DEPLOYMENT_GUIDE.md, understand Docker setup
4. **Day 4:** Read DATABASE_DOCUMENTATION.md, explore schema
5. **Day 5:** Read TECHNICAL_SPECIFICATIONS.md, understand APIs
6. **Day 6:** Read CODEBASE_ANALYSIS.md (this file), deep dive

---

**End of Quick Reference**

For comprehensive details, see:
- **Setup:** DEPLOYMENT_GUIDE.md
- **Database:** DATABASE_DOCUMENTATION.md  
- **Features:** TECHNICAL_SPECIFICATIONS.md
- **Analysis:** CODEBASE_ANALYSIS.md

**Status:** ✅ Production-ready, well-documented, Docker-optimized
