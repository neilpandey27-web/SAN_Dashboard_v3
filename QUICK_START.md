# SAN Dashboard v3 - FINAL PACKAGE
**Version:** 6.3.0 (All Fixes Applied)  
**Date:** December 23, 2024  
**Package:** `SAN_Dashboard_v3_FINAL_Dec23_2024.zip`

---

## ✅ CRITICAL FIXES INCLUDED

### 1. **Comparison Table Structure** - ✅ FIXED
- **Changed From:** System-based organization
- **Changed To:** Tenant-based organization
- **Table Columns:**
  ```
  Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %
  ```
- **Data Source:** `capacity_volumes` table (aggregated)
- **Location:** `frontend/app/overview/page.tsx` (lines 815-964)
- **Commit:** f683be6

### 2. **Treemap Data Source** - ✅ FIXED
- **Changed From:** `storage_pools` table
- **Changed To:** `capacity_volumes` table
- **Implementation:** Volumes aggregated by pool → system → hierarchy
- **Location:** `backend/app/utils/processing.py` (get_treemap_data function)
- **Commit:** 61ff8a2

---

## 🚀 QUICK START

### Prerequisites
- **Node.js:** v18+ (v20+ recommended)
- **Python:** 3.10+
- **PostgreSQL:** v14+

### Installation Steps

1. **Extract the ZIP file:**
   ```bash
   unzip SAN_Dashboard_v3_FINAL_Dec23_2024.zip -d san-dashboard
   cd san-dashboard
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Database:**
   Create `.env` in `backend/` directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/san_dashboard
   SECRET_KEY=your-secret-key-here
   POSTGRES_USER=san_admin
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=san_dashboard
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

4. **Initialize Database:**
   ```bash
   # From backend/ directory
   python import_data.py  # Run this once to set up tables
   ```

5. **Start Backend Server:**
   ```bash
   # From backend/ directory, with venv activated
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Backend will be available at: `http://localhost:8000`

6. **Setup Frontend:**
   ```bash
   # Open a new terminal
   cd frontend
   npm install
   ```

7. **Configure Frontend API:**
   Create `.env.local` in `frontend/` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

8. **Start Frontend Server:**
   ```bash
   # From frontend/ directory
   npm run dev
   ```
   Frontend will be available at: `http://localhost:3000`

---

## 📊 WHAT'S FIXED

### Comparison Table
**Before (WRONG):**
```
System | Tenant → Pools | Simple Avg % | Weighted Avg %
```

**After (CORRECT):**
```
Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %
```

**Example Output:**
| Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg % |
|--------|---------|------------|--------------|----------------|
| Tenant_A | AGNB-R1, AGNB-R2 | Pool1, Pool2, Pool3 | 65.4% | 68.2% |
| Tenant_B | AGNB-R3 | Pool4, Pool5 | 72.1% | 70.5% |

### Treemap Data Flow
**Before (WRONG):**
- Queried: `storage_pools` table directly
- Issue: Aggregated at pool level, missing volume-level detail

**After (CORRECT):**
- Queries: `capacity_volumes` table
- Aggregates: Volumes → Pools → Systems → All Storage
- Hierarchy: All Storage → Storage Systems → Pools
- Calculation: Uses actual volume capacities for accurate utilization

---

## 📂 DATA SOURCES (FINAL)

### 1. Comparison Table
- **Base Table:** `capacity_volumes`
- **Aggregation Flow:**
  ```
  capacity_volumes
    → GROUP BY pool_name, storage_system
    → Calculate pool metrics
    → GROUP BY tenant_name (from pool name pattern)
    → Calculate tenant-level averages
  ```
- **Backend Function:** `get_treemap_data()` in `backend/app/utils/processing.py:854`
- **API Endpoint:** `/data/overview/enhanced`
- **Frontend Processing:** `frontend/app/overview/page.tsx:888-990`

### 2. Treemap Chart
- **Base Table:** `capacity_volumes`
- **Data Field:** `treemap_data.weighted_average`
- **Aggregation Flow:**
  ```
  capacity_volumes
    → SUM capacities by pool_name
    → SUM capacities by storage_system
    → Create hierarchy: All Storage → Systems → Pools
  ```
- **Backend Function:** `get_treemap_data()` in `backend/app/utils/processing.py:854`
- **API Endpoint:** `/data/overview/enhanced`
- **Frontend Component:** `frontend/app/overview/page.tsx:755`

---

## 🔍 VERIFY THE FIXES

### 1. Check Comparison Table
After starting the app, navigate to:
```
http://localhost:3000/overview
```
Scroll to: **"📊 Comparison Table (Below Treemap): Tenant-Level Breakdown"**

**Expected:**
- First column: **Tenant names** (not System names)
- Second column: **Systems** (comma-separated list)
- Third column: **Pool Names** (comma-separated list)
- Fourth column: **Simple Avg %**
- Fifth column: **Weighted Avg %**

### 2. Check Treemap
On the same page, check: **"Capacity Treemap - Weighted Average"**

**Expected:**
- Hierarchical boxes showing: All Storage → Systems → Pools
- Box sizes represent total capacity
- Colors represent utilization (Green → Yellow → Red)
- Hover to see detailed metrics

### 3. Verify Data Source
Open browser console (F12) and check for:
```javascript
Treemap Data: { count: X, sample: [...] }
```
If count > 0, data is loading correctly from `capacity_volumes`.

---

## 🛠️ TROUBLESHOOTING

### Comparison Table Still Shows Wrong Structure
**Problem:** First column shows "AGNB-R1" (system names) instead of tenant names

**Solution:**
1. **Hard refresh browser:** Ctrl + Shift + R (or Cmd + Shift + R on Mac)
2. **Clear Next.js cache:**
   ```bash
   cd frontend
   rm -rf .next
   npm run dev
   ```
3. **Verify you're using the correct package:** Check that you extracted `SAN_Dashboard_v3_FINAL_Dec23_2024.zip`

### Treemap Is Blank
**Problem:** Treemap shows "No treemap data available"

**Debugging Steps:**
1. **Check console for data:**
   - Open browser console (F12)
   - Look for: `Treemap Data: { count: X, ... }`
   - If count = 0, no data from backend

2. **Verify database has data:**
   ```bash
   # Connect to PostgreSQL
   psql -U san_admin -d san_dashboard
   
   # Check capacity_volumes table
   SELECT COUNT(*) FROM capacity_volumes;
   ```

3. **Check backend logs:**
   ```bash
   # Backend terminal should show
   INFO: GET /data/overview/enhanced
   ```

4. **Upload sample data:**
   - Navigate to: `http://localhost:3000/db-mgmt`
   - Upload an Excel file with `Capacity_Volumes` sheet
   - Wait for upload to complete
   - Refresh overview page

### Backend Won't Start
**Common issues:**
1. **PostgreSQL not running:** 
   ```bash
   sudo systemctl start postgresql  # Linux
   brew services start postgresql   # Mac
   ```

2. **Database doesn't exist:**
   ```bash
   createdb san_dashboard
   ```

3. **Port 8000 already in use:**
   ```bash
   lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
   ```

### Frontend Won't Start
**Common issues:**
1. **Port 3000 already in use:**
   ```bash
   lsof -ti:3000 | xargs kill -9  # Kill process on port 3000
   ```

2. **Node modules corrupted:**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

---

## 📝 IMPORTANT NOTES

1. **Data Upload Required:** 
   - Before viewing the dashboard, upload an Excel file via Database Management page
   - Excel must have `Capacity_Volumes` sheet (case-sensitive)
   - Example columns: `pool_name`, `storage_system`, `capacity_gib`, `used_capacity_gib`, etc.

2. **Tenant Inference:**
   - Current version infers tenants from pool names using pattern matching
   - For production, backend should join with `tenant_pool_mappings` table
   - See: `backend/app/db/models.py` (TenantPoolMapping model)

3. **Default Credentials:**
   - Username: `admin@example.com`
   - Password: Check `backend/import_data.py` for default admin password
   - **Change immediately after first login!**

---

## 📚 DOCUMENTATION

All documentation is included in the package:
- `README.md` - Main documentation
- `SETUP_GUIDE_LOCAL.md` - Detailed setup guide
- `DATABASE_DOCUMENTATION.md` - Database schema
- `TECHNICAL_SPECIFICATIONS.md` - Technical details
- `DASHBOARD_CHART_BLOCKS.md` - Chart specifications

---

## ✅ VERIFICATION CHECKLIST

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Database connected successfully
- [ ] Excel file uploaded (with Capacity_Volumes sheet)
- [ ] Comparison table shows: **Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %**
- [ ] Treemap displays hierarchical boxes (not blank)
- [ ] Console shows: `Treemap Data: { count: > 0, ... }`

---

## 🆘 SUPPORT

If issues persist:
1. Check browser console for errors (F12)
2. Check backend terminal for error logs
3. Verify all environment variables are set correctly
4. Ensure PostgreSQL is running and accessible
5. Confirm you're using the FINAL package: `SAN_Dashboard_v3_FINAL_Dec23_2024.zip`

---

**Package Location:** `/home/user/webapp/SAN_Dashboard_v3_FINAL_Dec23_2024.zip`  
**Commits Included:** f683be6 (frontend fix) + 61ff8a2 (backend fix)
