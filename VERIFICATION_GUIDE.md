# 🔍 VERIFICATION GUIDE

## How to Verify Both Fixes

### 1️⃣ Verify Comparison Table Fix

**Step 1: Start the application**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Step 2: Open browser**
```
http://localhost:3000/overview
```

**Step 3: Scroll to "📊 Comparison Table"**

**Expected Table Structure:**
```
┌─────────────┬──────────────────┬───────────────────────┬──────────────┬────────────────┐
│   Tenant    │     Systems      │     Pool Names        │ Simple Avg % │ Weighted Avg % │
├─────────────┼──────────────────┼───────────────────────┼──────────────┼────────────────┤
│  Tenant_A   │ AGNB-R1, AGNB-R2 │ Pool1, Pool2, Pool3   │    65.4%     │     68.2%      │
│  Tenant_B   │ AGNB-R3          │ Pool4, Pool5          │    72.1%     │     70.5%      │
│  UNKNOWN    │ AGNB-R4          │ Pool6                 │    80.0%     │     82.1%      │
└─────────────┴──────────────────┴───────────────────────┴──────────────┴────────────────┘
```

**❌ WRONG (Old Code):**
```
┌───────────┬────────────────────┬──────────────┬────────────────┐
│  System   │   Tenant → Pools   │ Simple Avg % │ Weighted Avg % │
├───────────┼────────────────────┼──────────────┼────────────────┤
│  AGNB-R1  │ Tenant_A: Pool1... │    65.4%     │     68.2%      │
│  AGNB-R2  │ Tenant_A: Pool2... │    72.1%     │     70.5%      │
└───────────┴────────────────────┴──────────────┴────────────────┘
```

**✅ CORRECT (New Code):**
- First column: **Tenant names** (Tenant_A, Tenant_B, etc.)
- Second column: **Systems** (comma-separated)
- Third column: **Pool Names** (comma-separated)
- Fourth column: **Simple Avg %**
- Fifth column: **Weighted Avg %**

---

### 2️⃣ Verify Treemap Data Source Fix

**Step 1: Open browser console**
```
Press F12 → Console tab
```

**Step 2: Look for debug output**
```javascript
Treemap Data: {
  count: 42,
  sample: [
    {
      name: "Pool1",
      storage_system: "AGNB-R1",
      total_capacity_gib: 5000,
      used_capacity_gib: 3250,
      utilization_pct: 65.0
    },
    ...
  ]
}
```

**Step 3: Check the treemap chart**
- Should display hierarchical boxes
- Should NOT be blank
- Should show: All Storage → Systems → Pools

**Step 4: Verify backend is using capacity_volumes**

**Backend Log Check:**
```bash
# In backend terminal, you should see:
INFO:     Started server process
INFO:     GET /data/overview/enhanced
```

**Database Query Verification:**
```sql
-- Connect to database
psql -U san_admin -d san_dashboard

-- Check that capacity_volumes table has data
SELECT COUNT(*) FROM capacity_volumes;
-- Should return: count > 0

-- Check that treemap is built from volumes
SELECT 
  pool_name,
  storage_system,
  SUM(provisioned_capacity_gib) as total_capacity,
  SUM(used_capacity_gib) as used_capacity
FROM capacity_volumes
WHERE report_date = (SELECT MAX(report_date) FROM capacity_volumes)
GROUP BY pool_name, storage_system
ORDER BY total_capacity DESC
LIMIT 5;
```

**Code Verification:**
```bash
# Check backend code
cd /home/user/webapp
grep -A 5 "CapacityVolume" backend/app/utils/processing.py

# Should show:
# volumes = session.query(CapacityVolume)...
# (NOT: pools = session.query(StoragePool)...)
```

---

## 📊 Data Flow Verification

### Comparison Table Data Flow
```
1. Database: capacity_volumes table
   └─ Columns: pool_name, storage_system, provisioned_capacity_gib, used_capacity_gib

2. Backend: backend/app/utils/processing.py → get_treemap_data()
   └─ Query: SELECT * FROM capacity_volumes WHERE report_date = ?
   └─ Aggregation: 
      - SUM capacities by pool_name
      - SUM capacities by storage_system
      - Calculate utilization_pct

3. API: /data/overview/enhanced
   └─ Returns: treemap_data { simple_average: [...], weighted_average: [...] }

4. Frontend: frontend/app/overview/page.tsx
   └─ Process: Group by tenant (infer from pool name)
   └─ Display: Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %
```

### Treemap Data Flow
```
1. Database: capacity_volumes table (✅ FIXED - was storage_pools)
   └─ Base table for aggregations

2. Backend: backend/app/utils/processing.py → get_treemap_data()
   └─ Query: SELECT * FROM capacity_volumes WHERE report_date = ?
   └─ Aggregation: Volumes → Pools → Systems → All Storage

3. API: /data/overview/enhanced
   └─ Returns: treemap_data.weighted_average

4. Frontend: frontend/app/overview/page.tsx
   └─ Render: Plotly treemap with hierarchy
```

---

## 🧪 Test Cases

### Test Case 1: Comparison Table Structure
```
Input: Navigate to /overview page
Expected: Table shows "Tenant" as first column header
Actual: [To be verified by user]
Status: [PASS/FAIL]
```

### Test Case 2: Comparison Table Data
```
Input: Check first row of table
Expected: First cell shows tenant name (e.g., "Tenant_A")
Actual: [To be verified by user]
Status: [PASS/FAIL]
```

### Test Case 3: Treemap Displays Data
```
Input: Scroll to treemap chart
Expected: Hierarchical boxes visible (not blank)
Actual: [To be verified by user]
Status: [PASS/FAIL]
```

### Test Case 4: Treemap Data Source
```
Input: Check browser console
Expected: "Treemap Data: { count: > 0, ... }"
Actual: [To be verified by user]
Status: [PASS/FAIL]
```

### Test Case 5: Backend Using capacity_volumes
```
Input: grep "CapacityVolume" backend/app/utils/processing.py
Expected: Found in get_treemap_data function
Actual: [To be verified by developer]
Status: [PASS/FAIL]
```

---

## 🐛 Common Issues & Fixes

### Issue 1: "Table still shows System in first column"
**Cause:** Browser cached old version
**Fix:**
```bash
# Hard refresh
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)

# Or clear Next.js cache
cd frontend
rm -rf .next
npm run dev
```

### Issue 2: "Treemap is blank"
**Cause:** No data uploaded to capacity_volumes table
**Fix:**
```bash
# 1. Upload Excel file via Database Management page
# 2. Ensure Excel has "Capacity_Volumes" sheet (exact name)
# 3. Refresh overview page
```

### Issue 3: "Console shows count: 0"
**Cause:** Backend not querying capacity_volumes correctly
**Fix:**
```bash
# 1. Check backend code
cd /home/user/webapp
grep -n "capacity_volumes" backend/app/utils/processing.py

# 2. Restart backend
cd backend
# Ctrl+C to stop
uvicorn app.main:app --reload
```

### Issue 4: "Backend shows 'StoragePool' in logs"
**Cause:** Running old version of code
**Fix:**
```bash
# 1. Verify you extracted the FINAL package
ls -lh SAN_Dashboard_v3_FINAL_Dec23_2024.zip

# 2. Re-extract if needed
unzip -o SAN_Dashboard_v3_FINAL_Dec23_2024.zip

# 3. Restart backend
```

---

## ✅ Success Criteria

**All fixes are working correctly when:**

- [x] Comparison table first column shows: **Tenant names**
- [x] Comparison table columns are: `Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %`
- [x] Treemap displays: **Hierarchical boxes** (not blank)
- [x] Console shows: `Treemap Data: { count: > 0, ... }`
- [x] Backend code uses: `CapacityVolume` (not `StoragePool`)
- [x] Database has data in: `capacity_volumes` table

---

## 📸 Screenshot Reference

**Correct Comparison Table:**
```
Your screenshot should match this structure:
┌─────────────┬──────────────────┬───────────────────────┬──────────────┬────────────────┐
│   Tenant    │     Systems      │     Pool Names        │ Simple Avg % │ Weighted Avg % │
└─────────────┴──────────────────┴───────────────────────┴──────────────┴────────────────┘
```

**NOT this (old structure):**
```
┌───────────┬────────────────────┬──────────────┬────────────────┐
│  System   │   Tenant → Pools   │ Simple Avg % │ Weighted Avg % │
└───────────┴────────────────────┴──────────────┴────────────────┘
```

---

## 🔧 Developer Verification

For developers who want to verify the code changes:

### Frontend Changes (Comparison Table)
```bash
cd /home/user/webapp
git show f683be6:frontend/app/overview/page.tsx | grep -A 10 "Comparison Table"
```

### Backend Changes (Treemap Data Source)
```bash
cd /home/user/webapp
git show 61ff8a2:backend/app/utils/processing.py | grep -A 5 "get_treemap_data"
```

### Final Package
```bash
cd /home/user/webapp
ls -lh SAN_Dashboard_v3_FINAL_Dec23_2024.zip
unzip -l SAN_Dashboard_v3_FINAL_Dec23_2024.zip | head -20
```

---

**Verification Date:** December 23, 2024  
**Package Version:** 6.3.0  
**Commits:** f683be6 (frontend) + 61ff8a2 (backend) + 346d5a4 (release)
