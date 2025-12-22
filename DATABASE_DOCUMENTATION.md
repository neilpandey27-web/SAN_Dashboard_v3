# 🗄️ Database Documentation

**Version:** 2.0.0  
**Last Updated:** December 11, 2025

---

## 📋 Table of Contents

1. [Database Overview](#database-overview)
2. [Data Persistence Explained](#data-persistence-explained)
3. [Docker and Database Persistence](#docker-and-database-persistence)
4. [Database Initialization](#database-initialization)
5. [Database Schema](#database-schema)
6. [Data Export and Backup](#data-export-and-backup)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Database Overview

### **Supported Databases**

- **PostgreSQL 15+** (Production, Docker)
- **SQLite 3** (Development, Local testing)

### **Database Location**

**Docker Environment**:
```
Container: /app/db_files/storage_insights.db (SQLite)
        or postgresql://postgres:postgres@db:5432/storage_insights (PostgreSQL)
Host: ./db_files/storage_insights.db (SQLite, mounted volume)
```

**Local Environment**:
```
SQLite: ./db_files/storage_insights.db
PostgreSQL: localhost:5432/storage_insights
```

---

## 📊 Data Persistence Explained

### **Key Question: What Happens to My Data?**

**Short Answer**: Your uploaded data is **PERSISTENT** and stored in the database file, NOT hardcoded in the backend.

### **Two Types of Data**

#### **1. Default/Initial Data (Hardcoded in Backend)**

Seeded automatically on first run from `backend/app/db/database.py`:

- ✅ **6 Default Tenants**: BTC, HMC, ISST, HST, PERFORMANCE, UNKNOWN
- ✅ **1 Admin User**: admin@company.com / admin123

**Source Code**:
```python
# Lines 70-98 in backend/app/db/database.py
def seed_data(db: Session):
    # Only runs if database is empty
    if db.query(Tenant).count() == 0:
        tenants = [
            {"name": "BTC", "full_name": "BTC Team"},
            {"name": "HMC", "full_name": "HMC Team"},
            {"name": "ISST", "full_name": "ISST Team"},
            {"name": "HST", "full_name": "HST Team"},
            {"name": "PERFORMANCE", "full_name": "Performance Team"},
            {"name": "UNKNOWN", "full_name": "Unknown Team"}
        ]
        # Create tenants...
    
    if db.query(User).filter(User.email == "admin@company.com").count() == 0:
        # Create admin user...
```

#### **2. Your Storage Data (From Excel Uploads)**

**NOT hardcoded** - stored in database file:

- ✅ **Storage Systems**
- ✅ **Storage Pools**
- ✅ **Capacity Volumes**
- ✅ **Capacity Disks**
- ✅ **Capacity Hosts**
- ✅ **Departments**
- ✅ **All custom data you upload**

**Data Flow**:
```
Excel File Upload → Backend Processing → Database File
                                          (PERSISTENT!)
```

### **Complete Flow Explanation**

#### **Scenario 1: Fresh Installation - First Time Ever**

```
Step 1: Start the application
─────────────────────────────────────────
$ docker compose up -d

Status: No database file exists yet

                    ⬇️

Step 2: Backend creates database
─────────────────────────────────────────
📁 Creates: db_files/storage_insights.db (empty)

Tables created:
• storage_systems (0 rows)
• storage_pools (0 rows)
• capacity_volumes (0 rows)
• tenants (0 rows) ← About to be seeded
• users (0 rows) ← About to be seeded
• ... all other tables (0 rows)

                    ⬇️

Step 3: Backend seeds INITIAL data (from hardcoded values)
─────────────────────────────────────────
📝 Source: backend/app/db/database.py

Inserts into database:
✅ 6 tenants (BTC, HMC, ISST, HST, PERFORMANCE, UNKNOWN) ← FROM CODE
✅ 1 admin user (admin) ← FROM CODE

Result:
• tenants (6 rows) ✅
• users (1 row) ✅
• All storage tables still (0 rows) ❌

                    ⬇️

Step 4: You login and upload Excel file
─────────────────────────────────────────
📤 Upload: storage_insights_export.xlsx

Backend processes the file:
• Reads Excel sheets
• Parses data
• Inserts into database ← WRITTEN TO DATABASE FILE

NOT hardcoded in backend code! ✅
Data goes to: db_files/storage_insights.db

                    ⬇️

Step 5: Database now has your data
─────────────────────────────────────────
📁 File: db_files/storage_insights.db

Tables now contain:
• tenants (3 rows) ← From backend seed
• users (1 row) ← From backend seed
• storage_systems (100 rows) ← From YOUR Excel upload
• storage_pools (500 rows) ← From YOUR Excel upload
• capacity_volumes (2000 rows) ← From YOUR Excel upload
• ... etc.

All YOUR data is in the DATABASE FILE,
NOT in the backend code! ✅
```

#### **Scenario 2: Restart Application (Database Already Exists)**

```
Step 1: Restart the application
─────────────────────────────────────────
$ docker compose restart

Status: db_files/storage_insights.db EXISTS
Contains:
• 3 tenants
• 1 admin user
• 100 storage systems ← YOUR data from Excel
• 500 storage pools ← YOUR data from Excel

                    ⬇️

Step 2: Backend starts and checks database
─────────────────────────────────────────
📁 Opens: db_files/storage_insights.db

Backend seed function runs:
• Checks for tenants → Already exist (3 rows)
• Checks for admin user → Already exists (1 row)
• Skips seeding (does NOT overwrite) ✅

Code logic:
```python
existing = db.query(Tenant).filter(Tenant.name == name).first()
if not existing:  # ← This condition is FALSE
    # Skip creating tenant
```

                    ⬇️

Step 3: Your data is completely safe
─────────────────────────────────────────
📁 File: db_files/storage_insights.db

ALL data preserved:
✅ 3 tenants (unchanged)
✅ 1 admin user (unchanged)
✅ 100 storage systems (YOUR data - unchanged)
✅ 500 storage pools (YOUR data - unchanged)
✅ 2000 volumes (YOUR data - unchanged)

Nothing is lost! ✅
Nothing is hardcoded in backend! ✅
```

---

## 🐳 Docker and Database Persistence

### **Key Concept: Docker Volumes**

**Question**: "Does the database disappear when I turn down Docker?"

**Answer**: **NO! Database is PERSISTENT** ✅

The database file lives on **YOUR computer's hard drive**, not inside Docker containers.

```yaml
# In docker-compose.yml:
volumes:
  - ./db_files:/app/db_files  # Host directory mapped to container
```

**What this means**:
- **Your Computer**: `./db_files/storage_insights.db` (the REAL file)
- **Docker Container**: `/app/db_files/storage_insights.db` (just a link to your file)

**When you stop Docker**:
- ✅ Container is deleted
- ✅ Database file stays on your computer

### **Visual Diagram**

```
┌─────────────────────────────────────────────────────────┐
│                   YOUR COMPUTER'S HARD DRIVE             │
│                                                          │
│  /home/user/webapp/db_files/storage_insights.db         │
│  ┌────────────────────────────────────────────┐        │
│  │  THIS FILE ALWAYS STAYS HERE!              │        │
│  │  Docker cannot delete it!                  │        │
│  └────────────────────────────────────────────┘        │
│                      ⬆️ ⬇️                               │
│            (Docker mounts this folder)                   │
│                      ⬆️ ⬇️                               │
│  ┌────────────────────────────────────────────┐        │
│  │  Docker Container (temporary)              │        │
│  │  - Reads from storage_insights.db          │        │
│  │  - Writes to storage_insights.db           │        │
│  │  - When stopped: Container deleted         │        │
│  │  - Database file stays on disk! ✅         │        │
│  └────────────────────────────────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### **Complete Lifecycle**

#### **Stage 1: Fresh Installation (Before First Run)**
```
Your Computer: webapp/db_files/
  ├── .gitkeep
  └── README.md
  (No storage_insights.db yet) ❌

Status: Database is MISSING
```

#### **Stage 2: First Time Running Docker**
```bash
docker compose up -d
```

```
What happens:
1. Docker starts containers
2. Backend checks for database
3. No database found → Creates NEW database
4. Seeds 3 tenants + 1 admin
5. Database file written to YOUR COMPUTER

Your Computer: webapp/db_files/
  ├── .gitkeep
  ├── README.md
  └── storage_insights.db ✅ (NEW!)

Status: Database EXISTS on your computer
```

#### **Stage 3: You Upload Excel Files**
```
Your Computer: webapp/db_files/
  └── storage_insights.db ✅ (Now contains your data!)

Status: Database has your uploaded data
```

#### **Stage 4: You Stop Docker**
```bash
docker compose down
```

```
What happens:
1. Docker stops containers
2. Containers are REMOVED
3. Database file stays on your computer ✅

Your Computer: webapp/db_files/
  └── storage_insights.db ✅ (STILL HERE!)

Status: Database is SAFE
```

#### **Stage 5: You Start Docker Again**
```bash
docker compose up -d
```

```
What happens:
1. Docker starts containers
2. Backend finds existing database
3. Opens it and reads your data
4. No seeding needed

Your Computer: webapp/db_files/
  └── storage_insights.db ✅ (All your data intact!)

Status: All your data is accessible
```

#### **Stage 6: Repeat Stop/Start Forever**
```bash
# You can do this 1000 times
docker compose down
docker compose up -d
docker compose down
docker compose up -d
# ... repeat forever

# Database file: ALWAYS SAFE ✅
# Your data: NEVER DELETED ✅
```

### **Only Way to Delete Database**

The **ONLY** way database gets deleted:

```bash
# Manual deletion (YOU have to do this intentionally)
rm -f db_files/storage_insights.db

# Or Docker volumes removal (with -v flag)
docker compose down -v  # ⚠️ This deletes volumes!
```

**Regular `docker compose down` does NOT delete database!** ✅

---

## 🔧 Database Initialization

### **Automatic Initialization**

The application automatically:
1. Creates database file if it doesn't exist
2. Creates all required tables
3. Seeds default data (3 tenants + 1 admin)
4. Sets up indexes and constraints

### **Seed Data Details**

**Location**: `backend/app/db/database.py` (lines 70-98)

**What gets seeded**:

1. **Tenants**:
   ```python
   AIX (AIX Team)
   ISST (ISST Team)
   HST (HST Team)
   ```

2. **Admin User**:
   ```python
   Email: admin@company.com
   Password: admin123
   Role: Admin
   Approved: Yes
   ```

**Important**: Seeding only happens once when database is empty. Existing data is never overwritten.

---

## 📐 Database Schema

### **Core Tables**

#### **Storage Systems** (`storage_systems`)
Primary storage system information:
- `id`, `name`, `vendor`, `type`, `model`
- Capacity fields: `raw_capacity_gb`, `usable_capacity_gib`, `available_capacity_gib`
- Compression: `total_compression_ratio`, `data_reduction_ratio`
- Counts: `pools`, `volumes`, `managed_disks`

#### **Storage Pools** (`storage_pools`)
Pool-level data:
- `id`, `name`, `storage_system`, `status`
- Capacity: `usable_capacity_gib`, `available_capacity_gib`, `utilization_pct`
- Configuration: `tier`, `raid_level`, `compression_enabled`

#### **Capacity Volumes** (`capacity_volumes`)
Volume-level data:
- `id`, `name`, `storage_system`, `pool`, `status`
- Capacity: `capacity_gib`, `used_capacity_gib`, `available_capacity_gib`
- Type: `thin_provisioned`, `raid_level`, `virtual_disk_type`

#### **Capacity Disks** (`capacity_disks`)
Physical disk information:
- `id`, `name`, `storage_system`, `status`
- Physical: `capacity_gib`, `class`, `raid_level`
- Health: `condition`, `last_data_collection`

#### **Capacity Hosts** (`capacity_hosts`)
Host system data:
- `id`, `name`, `status`, `applications`
- Capacity: `block_capacity_gib`, `total_provisioned_gib`

#### **Departments** (`departments`)
Department mappings:
- `id`, `name`, `cost_center`
- Aggregation: Used for cost allocation

### **Calculated Fields**

Many fields are calculated from imported data:

**Pool Utilization**:
```python
utilization_pct = (used_capacity_gib / usable_capacity_gib) × 100
```

**Data Reduction**:
```python
data_reduction_gib = written_capacity_gib - used_capacity_gib
```

**Volume Written Percentage**:
```python
written_capacity_pct = (written_capacity_gib / real_capacity_gib) × 100
```

### **Unique Constraints**

To prevent duplicates:
- `storage_systems`: Unique on `(name, report_date)`
- `storage_pools`: Unique on `(name, storage_system, report_date)`
- `capacity_volumes`: Unique on `(name, storage_system, report_date)`
- `capacity_disks`: Unique on `(name, storage_system, report_date)`
- `capacity_hosts`: Unique on `(name, report_date)`

**Behavior**: When uploading duplicate data, the system:
1. Checks for existing record with same unique key
2. If found: Updates the existing record
3. If not found: Inserts new record

---

## 💾 Data Export and Backup

### **Export Database Data**

**Via UI**:
1. Navigate to Database Management → Tables
2. Select any table
3. Click "Data" view
4. Click "Download CSV" button

**Via Command Line (SQLite)**:
```bash
# Export specific table to CSV
sqlite3 db_files/storage_insights.db \
  "SELECT * FROM storage_systems;" \
  -header -csv > storage_systems.csv

# Export all tables
for table in storage_systems storage_pools capacity_volumes; do
  sqlite3 db_files/storage_insights.db \
    "SELECT * FROM $table;" \
    -header -csv > ${table}.csv
done
```

**Via Command Line (PostgreSQL)**:
```bash
# Docker environment
docker compose exec db pg_dump -U postgres storage_insights > backup.sql

# Export specific table
docker compose exec db psql -U postgres storage_insights \
  -c "COPY storage_systems TO STDOUT WITH CSV HEADER" > storage_systems.csv

# Local PostgreSQL
pg_dump -U postgres storage_insights > backup.sql
```

### **Backup Database**

#### **Full Database Backup (SQLite)**
```bash
# Simple file copy
cp db_files/storage_insights.db db_files/storage_insights.db.backup

# With timestamp
cp db_files/storage_insights.db \
   db_files/storage_insights_$(date +%Y%m%d_%H%M%S).db

# Compressed backup
tar -czf db_backup_$(date +%Y%m%d).tar.gz db_files/storage_insights.db
```

#### **Full Database Backup (PostgreSQL)**
```bash
# Docker environment
docker compose exec db pg_dump -U postgres storage_insights > backup.sql

# With compression
docker compose exec db pg_dump -U postgres storage_insights | gzip > backup.sql.gz

# Local PostgreSQL
pg_dump -U postgres storage_insights > backup.sql
```

### **Restore Database**

#### **Restore SQLite**
```bash
# Stop application
docker compose down

# Restore from backup
cp db_files/storage_insights.db.backup db_files/storage_insights.db

# Start application
docker compose up -d
```

#### **Restore PostgreSQL**
```bash
# Docker environment
docker compose exec -T db psql -U postgres storage_insights < backup.sql

# Or drop and recreate database first
docker compose exec db dropdb -U postgres storage_insights
docker compose exec db createdb -U postgres storage_insights
docker compose exec -T db psql -U postgres storage_insights < backup.sql

# Local PostgreSQL
psql -U postgres storage_insights < backup.sql
```

---

## 🔧 Troubleshooting

### **1. Database File Missing**

**Symptom**: Application shows "No data" or "Database not found"

**Check**:
```bash
ls -la db_files/storage_insights.db
```

**Solution**:
- Database is auto-created on first run
- If manually deleted, restart application to recreate:
  ```bash
  docker compose restart backend
  ```

### **2. Database Locked (SQLite)**

**Symptom**: `OperationalError: database is locked`

**Cause**: Multiple processes trying to write simultaneously

**Solution**:
```bash
# Check for processes using database
lsof db_files/storage_insights.db

# Kill blocking processes
kill -9 <PID>

# Restart application
docker compose restart backend
```

### **3. Connection Refused (PostgreSQL)**

**Symptom**: `could not connect to server`

**Check**:
```bash
# Docker
docker compose ps db

# Local
pg_isready -h localhost -p 5432
```

**Solution**:
```bash
# Docker: Restart database
docker compose restart db

# Local: Start PostgreSQL
# Linux
sudo systemctl start postgresql

# Mac
brew services start postgresql@15
```

### **4. Data Not Persisting**

**Symptom**: Data disappears after Docker restart

**Check Volume Mapping**:
```bash
docker compose config | grep -A 5 volumes
```

**Should see**:
```yaml
volumes:
  - ./db_files:/app/db_files
```

**Solution**: Ensure `docker-compose.yml` has correct volume mapping

### **5. Corrupted Database**

**Symptom**: Errors when querying data

**Check (SQLite)**:
```bash
sqlite3 db_files/storage_insights.db "PRAGMA integrity_check;"
```

**Solution**:
1. Restore from backup
2. If no backup, export salvageable data:
   ```bash
   sqlite3 db_files/storage_insights.db .dump > salvage.sql
   ```
3. Create new database and import

### **6. Wrong Database Used**

**Symptom**: Changes not reflected or old data appears

**Check Active Database**:
```bash
# Check environment variable
docker compose exec backend env | grep DATABASE_URL

# Or check config file
docker compose exec backend cat /app/.env
```

**Expected**:
```
# Docker (SQLite)
DATABASE_URL=sqlite:///./db_files/storage_insights.db

# Docker (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@db:5432/storage_insights
```

---

## 📚 Related Documentation

- `DEPLOYMENT_GUIDE.md` - Setup and deployment instructions
- `FIXES_AND_UPDATES.md` - Recent fixes and updates
- `TECHNICAL_SPECIFICATIONS.md` - Features and technical details
- `README.md` - Project overview

---

## 🆘 Support

For database issues:

1. **Check database file exists**:
   ```bash
   ls -la db_files/storage_insights.db
   ```

2. **Check database logs**:
   ```bash
   docker compose logs backend | grep -i database
   ```

3. **Test database connection**:
   ```bash
   docker compose exec backend python -c "from app.db.database import engine; print(engine.url)"
   ```

4. **Verify data**:
   ```bash
   # SQLite
   sqlite3 db_files/storage_insights.db "SELECT COUNT(*) FROM storage_systems;"
   
   # PostgreSQL
   docker compose exec db psql -U postgres storage_insights \
     -c "SELECT COUNT(*) FROM storage_systems;"
   ```

---

**Status**: ✅ Complete database documentation covering persistence, schemas, backups, and troubleshooting

**Last Updated**: December 11, 2025
