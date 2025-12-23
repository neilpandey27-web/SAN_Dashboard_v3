# 📦 SAN Dashboard v6.4.0 - Tenant Hierarchy Implementation

**Package:** `SAN_Dashboard_TENANT_HIERARCHY_Dec23_2024.zip` (339 KB)  
**Date:** December 23, 2024  
**Commit:** 11ea219  
**Location:** `/home/user/webapp/SAN_Dashboard_TENANT_HIERARCHY_Dec23_2024.zip`

---

## ✅ WHAT'S BEEN IMPLEMENTED

### New Treemap Hierarchy (4 Levels):

```
All Storage (Root)
  ↓
Storage Systems (AGNB-R1, AGNB-R2, FlashSystem900, etc.)
  ↓
Tenants (Production Tenant, Marketing, UNKNOWN, etc.) - PER SYSTEM
  ↓
Pools (Pool1, Pool2, Pool3, etc.) - LEAF NODES
```

### Visual Example:

```
┌──────────────────────────────────────────────────────────────────┐
│                        All Storage                               │
│  ┌────────────────────────────────┐  ┌─────────────────────┐    │
│  │      AGNB-R1 (System)          │  │   AGNB-R2 (System)  │    │
│  │  ┌──────────────────────────┐  │  │  ┌────────────────┐ │    │
│  │  │  Production Tenant       │  │  │  │ Dev Tenant     │ │    │
│  │  │  ┌──────┐  ┌──────┐      │  │  │  │  ┌──────┐     │ │    │
│  │  │  │Pool1 │  │Pool2 │      │  │  │  │  │Pool3 │     │ │    │
│  │  │  └──────┘  └──────┘      │  │  │  │  └──────┘     │ │    │
│  │  └──────────────────────────┘  │  │  └────────────────┘ │    │
│  │  ┌──────────────────────────┐  │  │                     │    │
│  │  │  UNKNOWN Tenant          │  │  │                     │    │
│  │  │  ┌──────┐               │  │  │                     │    │
│  │  │  │Pool4 │               │  │  │                     │    │
│  │  │  └──────┘               │  │  │                     │    │
│  │  └──────────────────────────┘  │  │                     │    │
│  └────────────────────────────────┘  └─────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 KEY FEATURES

### 1. **Tenant Integration**
- ✅ Joins `capacity_volumes` + `tenant_pool_mappings` + `tenants` tables
- ✅ Auto-creates UNKNOWN tenant if missing
- ✅ Unmapped pools automatically assigned to UNKNOWN tenant (per-system)
- ✅ One-to-many relationship: 1 Pool → 1 Tenant, 1 Tenant → Many Pools

### 2. **Two Chart Types (Independent)**

#### A. Treemap Visualization
- **Uses:** Weighted Average ONLY
- **Hierarchy:** All Storage → System → Tenant (per-system) → Pool
- **Tenant Scope:** Per-system (Tenant X in System A separate from Tenant X in System B)
- **Purpose:** Show storage breakdown by physical system, then by tenant within each system

#### B. Comparison Table
- **Uses:** Both Simple Average AND Weighted Average
- **Grouping:** By Tenant ACROSS ALL SYSTEMS
- **Tenant Scope:** Global (Tenant X shows ALL its pools from ALL systems combined)
- **Purpose:** Compare tenants' total storage usage regardless of which system

### 3. **Calculations**

**Pool Level:**
```
pool_utilization = (used_capacity_gib / provisioned_capacity_gib) × 100
```

**Tenant Level (Per-System for Treemap):**
```
tenant_used = SUM(volumes in pools mapped to this tenant in this system)
tenant_capacity = SUM(provisioned capacity for those volumes)
tenant_util = (tenant_used / tenant_capacity) × 100
```

**Tenant Level (Cross-System for Comparison Table):**
```
Simple Avg = (Pool1_util + Pool2_util + ... + PoolN_util) / N
Weighted Avg = (Total Used across all pools) / (Total Capacity across all pools) × 100
```

**System Level:**
```
system_util = (sum used in system / sum capacity in system) × 100
```

### 4. **UNKNOWN Tenant Handling**
- **Per-system grouping:** Each system has its own UNKNOWN tenant node
- **Auto-assignment:** Unmapped pools automatically go to UNKNOWN
- **Failsafe:** If UNKNOWN tenant doesn't exist, it's auto-created
- **Real database record:** UNKNOWN is stored in the `tenants` table

### 5. **Empty Tenants**
- **Hidden from treemap:** Only show tenants that have mapped pools with capacity > 0
- **Cleaner visualization:** No empty/placeholder nodes

---

## 📊 DATA FLOW

### Backend Query:
```sql
SELECT 
    volume.*,
    tenant.name as tenant_name,
    tenant.id as tenant_id
FROM capacity_volumes volume
LEFT JOIN tenant_pool_mappings mapping 
    ON mapping.pool_name = volume.pool_name 
    AND mapping.storage_system = volume.storage_system
LEFT JOIN tenants tenant 
    ON tenant.id = mapping.tenant_id
WHERE volume.report_date = ?
```

### Data Structure:
```python
hierarchy = {
    'System A': {
        'Tenant X': {
            'Pool1': {'provisioned': 1000, 'used': 800, 'volume_count': 50},
            'Pool2': {'provisioned': 500, 'used': 100, 'volume_count': 25}
        },
        'UNKNOWN': {
            'Pool4': {'provisioned': 200, 'used': 100, 'volume_count': 10}
        }
    },
    'System B': {
        'Tenant X': {
            'Pool5': {'provisioned': 2000, 'used': 1200, 'volume_count': 100}
        }
    }
}
```

---

## 🚀 QUICK START - DOCKER

### Prerequisites:
- Docker & Docker Compose installed
- At least 4GB RAM available

### Step 1: Extract Package
```bash
unzip SAN_Dashboard_TENANT_HIERARCHY_Dec23_2024.zip -d san-dashboard
cd san-dashboard
```

### Step 2: Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Services:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

### Step 3: Initialize Database
```bash
# Wait for services to be healthy (~30 seconds)
sleep 30

# Create database tables
docker-compose exec backend python import_data.py
```

### Step 4: Access Dashboard
```
http://localhost:3000
```

**Default Credentials:**
- Username: `admin@example.com`
- Password: Check `backend/import_data.py` for default password

### Step 5: Upload Data

1. **Go to Database Management** tab
2. **Upload Excel file** with `Capacity_Volumes` sheet
3. **Upload Tenant-Pool Mappings CSV** (optional but recommended)
4. **Refresh Overview** page to see treemap and comparison table

---

## 📋 MANUAL SETUP (WITHOUT DOCKER)

### Prerequisites:
- Node.js v18+
- Python 3.10+
- PostgreSQL v14+

### Step 1: Setup Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Database
Create `.env` file in `backend/` directory:
```env
DATABASE_URL=postgresql://san_admin:your_password@localhost:5432/san_dashboard
SECRET_KEY=your-secret-key-here
POSTGRES_USER=san_admin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=san_dashboard
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Step 3: Create Database
```bash
createdb san_dashboard
```

### Step 4: Initialize Tables
```bash
cd backend
python import_data.py
```

### Step 5: Start Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000

### Step 6: Setup Frontend
```bash
cd frontend
npm install
```

Create `.env.local` in `frontend/` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 7: Start Frontend
```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:3000

---

## 🔍 VERIFICATION STEPS

### 1. Check Treemap Hierarchy
- Navigate to http://localhost:3000/overview
- Scroll to "Capacity Treemap - Weighted Average"
- **Verify:**
  - ✅ 4 levels visible: All Storage → Systems → Tenants → Pools
  - ✅ Tenants appear under each system
  - ✅ Clicking a system shows its tenants
  - ✅ Clicking a tenant shows its pools
  - ✅ UNKNOWN tenant visible if unmapped pools exist

### 2. Check Comparison Table
- Scroll to "📊 Comparison Table"
- **Verify:**
  - ✅ First column: Tenant names
  - ✅ Second column: Systems (comma-separated)
  - ✅ Third column: Pool names
  - ✅ Fourth column: Simple Avg % with color badges
  - ✅ Fifth column: Weighted Avg % with color badges
  - ✅ Tenants sorted alphabetically (UNKNOWN last)

### 3. Check Tenant Data
**Open browser console (F12):**
```javascript
// Should see treemap_data logged
treemap_data: {
  weighted_average: [...],  // For treemap
  simple_average: [...]     // For comparison table
}
```

**Expected simple_average structure:**
```javascript
[
  {
    tenant_name: "Production Tenant",
    systems: "System A, System B",
    pools: ["SystemA:Pool1", "SystemA:Pool2", "SystemB:Pool5"],
    simple_avg_utilization: 53.3,
    weighted_avg_utilization: 60.0
  }
]
```

---

## 📂 DATABASE SCHEMA

### Tables Used:

#### 1. `capacity_volumes` (Base Table)
```sql
- id
- report_date
- volume_name
- pool_name  ← JOIN KEY
- storage_system  ← JOIN KEY
- provisioned_capacity_gib
- used_capacity_gib
- available_capacity_gib
```

#### 2. `tenant_pool_mappings` (Relationship Table)
```sql
- id
- tenant_id  ← FK to tenants.id
- pool_name  ← JOIN KEY
- storage_system  ← JOIN KEY
- created_at
```

#### 3. `tenants` (Lookup Table)
```sql
- id
- name  (e.g., "Production Tenant", "UNKNOWN")
- description
- created_at
```

---

## 🧪 TESTING SCENARIOS

### Scenario 1: Upload Excel Only (No Mappings)
**Expected Result:**
- Treemap shows: All Storage → Systems → UNKNOWN Tenant → All Pools
- Comparison Table shows: UNKNOWN tenant with all pools
- Banner message: "ℹ️ Unmapped pools detected in System A: 5 pools"

### Scenario 2: Upload Excel + Tenant-Pool CSV
**Expected Result:**
- Treemap shows: All Storage → Systems → Multiple Tenants → Pools
- Comparison Table shows: Each tenant with its pools across systems
- Only unmapped pools go to UNKNOWN

### Scenario 3: Tenant Across Multiple Systems
**Given:**
- Tenant "Production" has Pool1 in System A
- Tenant "Production" has Pool5 in System B

**Treemap Result:**
```
All Storage
├── System A
│   └── Production → Pool1
└── System B
    └── Production → Pool5
```

**Comparison Table Result:**
```
| Production | System A, System B | Pool1, Pool5 | 53% | 60% |
```

---

## 🐛 TROUBLESHOOTING

### Issue 1: Treemap is Blank
**Possible Causes:**
1. No data uploaded
2. No volumes in `capacity_volumes` table
3. Invalid report_date

**Solution:**
```bash
# Check if data exists
docker-compose exec backend python -c "
from app.db.database import SessionLocal
from app.db.models import CapacityVolume
db = SessionLocal()
count = db.query(CapacityVolume).count()
print(f'Volume count: {count}')
"

# If count = 0, upload Excel file via Database Management
```

### Issue 2: All Pools Show as UNKNOWN
**Possible Causes:**
1. Tenant-Pool mappings not uploaded
2. Incorrect pool names or systems in mappings

**Solution:**
```bash
# Check mappings
docker-compose exec backend python -c "
from app.db.database import SessionLocal
from app.db.models import TenantPoolMapping
db = SessionLocal()
count = db.query(TenantPoolMapping).count()
print(f'Mapping count: {count}')
"

# If count = 0, upload Tenant-Pool CSV
```

### Issue 3: Comparison Table Shows Wrong Structure
**Possible Cause:** Browser cached old frontend code

**Solution:**
```bash
# Hard refresh browser
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)

# Or clear Next.js cache
docker-compose exec frontend rm -rf .next
docker-compose restart frontend
```

### Issue 4: UNKNOWN Tenant Not Created
**Solution:**
```bash
# Manually create UNKNOWN tenant
docker-compose exec backend python -c "
from app.db.database import SessionLocal
from app.db.models import Tenant
db = SessionLocal()
unknown = Tenant(name='UNKNOWN', description='Catch-all for unmapped pools')
db.add(unknown)
db.commit()
print('UNKNOWN tenant created')
"
```

---

## 📄 FILES MODIFIED

### Backend:
- **`backend/app/utils/processing.py`**
  - Updated `get_treemap_data()` function
  - Added joins with `tenant_pool_mappings` and `tenants`
  - Implemented 4-level hierarchy
  - Auto-create UNKNOWN tenant
  - Calculate per-system and cross-system aggregations

### Frontend:
- **`frontend/app/overview/page.tsx`**
  - Removed hardcoded tenant pattern matching
  - Updated comparison table to use backend `simple_average` data
  - Display tenant-level grouping across systems

---

## 🎨 UI FEATURES

### Treemap Hover Tooltip:
```
System: AGNB-R1
Tenant: Production Tenant
Pool: Pool1
Total Capacity: 20 TB
Used: 13 TB
Available: 7 TB
Utilization: 65%
Volume Count: 250 volumes
```

### Comparison Table Color Coding:
- 🔴 **Red:** >80% utilization (Critical)
- 🟡 **Yellow:** 70-80% utilization (Warning)
- 🟢 **Green:** ≤70% utilization (Good)

---

## 📦 PACKAGE CONTENTS

```
SAN_Dashboard_TENANT_HIERARCHY_Dec23_2024.zip (339 KB)
├── backend/
│   ├── app/
│   │   ├── api/v1/data.py
│   │   ├── utils/processing.py  ✅ UPDATED
│   │   ├── db/models.py
│   │   └── ...
│   ├── requirements.txt
│   └── import_data.py
├── frontend/
│   ├── app/overview/page.tsx  ✅ UPDATED
│   ├── lib/api.ts
│   ├── package.json
│   └── ...
├── docker-compose.yml
├── README.md
├── TENANT_HIERARCHY_IMPLEMENTATION.md  ✅ THIS FILE
└── ...
```

---

## ✅ CHECKLIST

Before reporting issues:

- [ ] Extracted ZIP file
- [ ] Started Docker containers OR set up manually
- [ ] Database initialized with `import_data.py`
- [ ] Uploaded Excel file with Capacity_Volumes sheet
- [ ] (Optional) Uploaded Tenant-Pool mappings CSV
- [ ] Hard refreshed browser (Ctrl + Shift + R)
- [ ] Checked treemap shows 4-level hierarchy
- [ ] Checked comparison table shows tenant grouping
- [ ] Verified console shows no errors

---

## 📞 SUPPORT

**Package Location:** `/home/user/webapp/SAN_Dashboard_TENANT_HIERARCHY_Dec23_2024.zip`  
**Commit:** 11ea219  
**Date:** December 23, 2024  
**Version:** 6.4.0

**Key Changes:**
1. ✅ Treemap hierarchy: All Storage → System → Tenant → Pool
2. ✅ Tenant integration with database tables
3. ✅ UNKNOWN tenant auto-creation
4. ✅ Per-system tenant grouping in treemap
5. ✅ Cross-system tenant grouping in comparison table
6. ✅ No more hardcoded tenant names

**Ready for download and local testing with Docker!** 🚀
