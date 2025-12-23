# 🔍 DEBUG SCRIPT - Quick Start Guide

## 📦 Package Download

**File**: `/home/user/webapp/SAN_Dashboard_WITH_DEBUG_Dec23_2024.zip`  
**Size**: 464 KB  
**Includes**: `backend/debug_treemap.py` script

---

## 🚀 How to Use the Debug Script

### Step 1: Deploy the Application
```bash
# Extract package
unzip SAN_Dashboard_WITH_DEBUG_Dec23_2024.zip
cd SAN_Dashboard_WITH_DEBUG_Dec23_2024

# Start Docker
docker-compose down -v
docker-compose build
docker-compose up -d

# Import your data
docker-compose exec backend python import_data.py
```

### Step 2: Run the Debug Script
```bash
# Execute the diagnostic
docker-compose exec backend python debug_treemap.py
```

This will output detailed information about your treemap hierarchy!

---

## 📊 What the Script Shows

### 1. Sample Volumes
```
SAMPLE VOLUMES (First 10)
================================================================================

1. Volume: vol_001
   Storage System: 'FlashSystem900'
   Pool: 'Pool1'
   Capacity: 50.00 GiB
   Used: 30.00 GiB
```

**Check**: Are storage system names populated? Or empty/null?

### 2. Unique Storage Systems
```
UNIQUE STORAGE SYSTEMS (3 total)
================================================================================
  • FlashSystem900: 5 pools, 150 volumes
  • DS8900: 3 pools, 80 volumes
  • StorageVault: 2 pools, 50 volumes
```

**Check**: 
- How many systems do you have?
- If only 1, the treemap will look "flat"
- System names should be consistent

### 3. Sample Pools
```
SAMPLE POOLS (First 20)
================================================================================
  • Pool: 'Pool1' on System: 'FlashSystem900' (30 volumes)
  • Pool: 'Pool2' on System: 'FlashSystem900' (25 volumes)
  • Pool: 'Pool3' on System: 'DS8900' (20 volumes)
```

**Check**: Are pools properly associated with systems?

### 4. Hierarchy Node Counts
```
TESTING get_treemap_data() FUNCTION
================================================================================

✅ Function returned:
   Simple average entries: 5
   Weighted average entries: 23

WEIGHTED AVERAGE HIERARCHY (for treemap)
================================================================================

📊 Node counts by level:
   Root (All Storage): 1
   Systems: 3
   Tenants: 5
   Pools: 14
```

**Expected**:
- ✅ Root: Always 1
- ✅ Systems: Should match your actual storage systems (2-10)
- ✅ Tenants: Depends on tenant mappings (0 = all UNKNOWN)
- ✅ Pools: Should match total unique pools

### 5. Detailed Node Structure
```
🌳 Root Node:
   • All Storage
     Parent: ''
     Capacity: 1000.00 GiB

🏢 System Nodes:
   • FlashSystem900
     Parent: 'All Storage'
     Capacity: 600.00 GiB

👥 Tenant Nodes (first 10):
   • FlashSystem900|Engineering
     Parent: 'FlashSystem900'
     Capacity: 300.00 GiB
     Pools: 3
   • FlashSystem900|UNKNOWN
     Parent: 'FlashSystem900'
     Capacity: 300.00 GiB
     Pools: 2

💾 Pool Nodes (first 10):
   • Pool1
     Parent: 'FlashSystem900|Engineering'
     Capacity: 100.00 GiB
```

**Check Parent Relationships**:
- ✅ Root parent: `''` (empty string)
- ✅ System parent: `'All Storage'`
- ✅ Tenant parent: System name (e.g., `'FlashSystem900'`)
- ✅ Pool parent: `SystemName|TenantName` (e.g., `'FlashSystem900|Engineering'`)

---

## 🎯 Common Issues and Fixes

### Issue 1: Only 1 Storage System
**Symptom**: Debug shows only 1 system

**Impact**: Treemap looks "flat" because one system fills 100% of space

**Fix**: This is actually OK! But visually less impressive. The hierarchy still exists:
```
All Storage (root)
  └── YourSystem (100% of space)
        ├── Tenant A (section)
        ├── Tenant B (section)  
        └── UNKNOWN (section)
              ├── Pool1
              ├── Pool2
              └── ...
```

**Workaround**: Add more diverse test data or wait for real multi-system data.

### Issue 2: All Tenants Show as UNKNOWN
**Symptom**: Debug shows many `UNKNOWN` tenant nodes

**Cause**: No tenant-pool mappings in database

**Fix**: Create tenant mappings (see below)

### Issue 3: Empty System Names
**Symptom**: Debug shows system names as empty, null, or "Unknown System"

**Cause**: `storage_system_name` column not populated during import

**Fix**: Check your import_data.py or Excel upload to ensure system names are included

---

## 🛠️ Create Tenant Mappings

### Option 1: SQL (Fastest)
```bash
# Connect to database
docker-compose exec db psql -U admin -d san_dashboard

# Create tenants
INSERT INTO tenants (name, description) VALUES 
  ('Engineering', 'Engineering Department'),
  ('Marketing', 'Marketing Department'),
  ('Finance', 'Finance Department');

# First, see your actual pool names
SELECT DISTINCT pool, storage_system_name FROM capacity_volumes LIMIT 20;

# Then create mappings (use your actual pool names from above)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system) 
VALUES 
  (1, 'Pool1', 'FlashSystem900'),  -- Replace with your actual pool names
  (1, 'Pool2', 'FlashSystem900'),
  (2, 'Pool3', 'DS8900'),
  (3, 'Pool4', 'DS8900');

# Exit
\q
```

### Option 2: CSV Upload (via UI)
1. **Export your pools**:
   ```bash
   docker-compose exec db psql -U admin -d san_dashboard -c \
     "COPY (SELECT DISTINCT pool, storage_system_name FROM capacity_volumes) TO STDOUT WITH CSV HEADER" \
     > my_pools.csv
   ```

2. **Create mappings file**: `tenant_mappings.csv`
   ```csv
   tenant_name,pool_name,storage_system
   Engineering,Pool1,FlashSystem900
   Engineering,Pool2,FlashSystem900
   Marketing,Pool3,DS8900
   Finance,Pool4,DS8900
   ```

3. **Upload via UI**: Database Management → CSV Upload

---

## 🔄 After Creating Tenant Mappings

1. **Refresh the page** in browser (Ctrl+Shift+R / Cmd+Shift+R)
2. **Run debug script again**:
   ```bash
   docker-compose exec backend python debug_treemap.py
   ```
3. **Check Tenant Nodes section** - should now show real tenant names instead of UNKNOWN

---

## 📤 Share Debug Output With Me

If you're still having issues, please run:

```bash
docker-compose exec backend python debug_treemap.py > debug_output.txt
```

Then share the `debug_output.txt` file or paste the relevant sections so I can help diagnose the exact issue!

---

## 🎯 Expected Results After Fixes

Once your data is properly structured, the debug script should show:
- ✅ Multiple storage systems (or at least 1 with a proper name)
- ✅ Tenant nodes with real names (not just UNKNOWN)
- ✅ Correct parent-child relationships at all levels
- ✅ Pool counts that match your actual data

And the treemap should display the full 4-level hierarchy! 🎉

---

**Package**: `/home/user/webapp/SAN_Dashboard_WITH_DEBUG_Dec23_2024.zip` (464 KB)  
**GitHub**: https://github.com/neilpandey27-web/SAN_Dashboard_v3 (Commit `f68324e`)  
**Status**: ✅ Ready to download and diagnose
