# 🔍 TREEMAP HIERARCHY DIAGNOSTIC

## The Issue You Reported

Your screenshot shows the treemap is **NOT following the 4-level hierarchy** we agreed on:
- ❌ Current: Appears to show pools directly under "All Storage"
- ✅ Expected: All Storage → Systems → Tenants → Pools

---

## 🧪 Run This Diagnostic Script

To see exactly what data is being generated, run this command in your Docker environment:

```bash
docker-compose exec backend python debug_treemap.py
```

This will show you:
1. ✅ Sample volumes from your database
2. ✅ Unique storage systems
3. ✅ Sample pools
4. ✅ The actual treemap hierarchy being generated
5. ✅ Node counts at each level (Root/Systems/Tenants/Pools)

---

## 📊 Expected Output

The script should show something like:

```
WEIGHTED AVERAGE HIERARCHY (for treemap)
================================================================================

📊 Node counts by level:
   Root (All Storage): 1
   Systems: 3
   Tenants: 5
   Pools: 20

🌳 Root Node:
   • All Storage
     Parent: ''
     Capacity: 1000.00 GiB

🏢 System Nodes:
   • FlashSystem900
     Parent: 'All Storage'
     Capacity: 500.00 GiB
   • DS8900
     Parent: 'All Storage'
     Capacity: 300.00 GiB

👥 Tenant Nodes:
   • FlashSystem900|Engineering
     Parent: 'FlashSystem900'
     Capacity: 250.00 GiB
     Pools: 5
   • FlashSystem900|UNKNOWN
     Parent: 'FlashSystem900'
     Capacity: 250.00 GiB
     Pools: 3

💾 Pool Nodes:
   • Pool1
     Parent: 'FlashSystem900|Engineering'
     Capacity: 50.00 GiB
   • Pool2
     Parent: 'FlashSystem900|Engineering'
     Capacity: 50.00 GiB
```

---

## 🔍 Possible Causes Based on Your Screenshot

### 1. Empty or Null Storage System Names
If `storage_system_name` is empty/null in your volumes, all pools will appear under a generic system.

**Check**: Run the diagnostic and look at "SAMPLE VOLUMES" section. Do you see valid system names?

### 2. All Pools Mapped to One System
If all your volumes belong to one storage system, you won't see multiple system boxes.

**Check**: Look at "UNIQUE STORAGE SYSTEMS" count in diagnostic output.

### 3. No Tenant Mappings
If you see many `UNKNOWN` tenant nodes, it means `tenant_pool_mappings` table is empty.

**Check**: Look at "Tenant Nodes" in diagnostic. Are they all UNKNOWN?

---

## 🛠️ How to Fix Each Scenario

### Scenario A: Empty System Names
**Problem**: Volumes have null/empty `storage_system_name`

**Fix**:
```sql
-- Check if system names are empty
SELECT COUNT(*), storage_system_name 
FROM capacity_volumes 
GROUP BY storage_system_name;

-- If you see NULL or empty strings, you need to populate them
-- This should be done during data import from Excel
```

### Scenario B: Need to Create Tenant Mappings
**Problem**: All tenants show as "UNKNOWN"

**Fix - Option 1** (SQL):
```sql
-- Create tenants
INSERT INTO tenants (name, description) VALUES 
  ('Engineering', 'Engineering Department'),
  ('Marketing', 'Marketing Department'),
  ('Finance', 'Finance Department');

-- Get your actual pool names first
SELECT DISTINCT pool, storage_system_name FROM capacity_volumes LIMIT 20;

-- Then map pools to tenants (replace pool names with your actual ones)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system) 
SELECT 
  1 as tenant_id,  -- Engineering
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool IN ('Pool1', 'Pool2', 'Pool3')  -- Your actual pool names
GROUP BY pool, storage_system_name;
```

**Fix - Option 2** (CSV Upload via UI):
1. Export your pools: `SELECT DISTINCT pool, storage_system_name FROM capacity_volumes;`
2. Create CSV: `tenant_mappings.csv`
   ```csv
   tenant_name,pool_name,storage_system
   Engineering,Pool1,FlashSystem900
   Engineering,Pool2,FlashSystem900
   Marketing,Pool3,DS8900
   ```
3. Upload via Database Management page

### Scenario C: System Names Are Inconsistent
**Problem**: System names vary (e.g., "FlashSystem900", "Flash System 900", "FS900")

**Check**:
```sql
SELECT DISTINCT storage_system_name FROM capacity_volumes;
```

**Fix**: Normalize system names during import or update:
```sql
UPDATE capacity_volumes 
SET storage_system_name = 'FlashSystem900'
WHERE storage_system_name LIKE '%Flash%900%';
```

---

## 📋 Verification Checklist

Run the diagnostic script and check:

- [ ] **Root node**: Should be 1 (All Storage)
- [ ] **System nodes**: Should match your actual storage systems (2-10 typically)
- [ ] **Tenant nodes**: Should be > 0 (if you have tenant mappings)
- [ ] **Pool nodes**: Should match total unique pools in your data
- [ ] **Parent relationships**: Each node should have correct parent
  - Root parent: `''` (empty string)
  - System parent: `'All Storage'`
  - Tenant parent: System name (e.g., `'FlashSystem900'`)
  - Pool parent: Unique tenant name (e.g., `'FlashSystem900|Engineering'`)

---

## 🎯 Most Likely Scenario

Based on your screenshot showing many pools, **the most likely issue is**:

**All your volumes belong to ONE storage system** or **system names are empty/inconsistent**.

When all pools belong to one system, the treemap will look "flat" because:
```
All Storage (big box)
  └── SingleSystem (fills entire space)
        ├── Tenant1 (section)
        ├── Tenant2 (section)
        └── UNKNOWN (large section with many pools)
```

This would look like pools are directly under "All Storage" when actually they're:
```
All Storage → [SingleSystem] → Tenants → Pools
```

But visually, if there's only ONE system, it takes up 100% of space, making it hard to see the hierarchy.

---

## 🚀 Action Items

1. **Run the diagnostic script**:
   ```bash
   docker-compose exec backend python debug_treemap.py
   ```

2. **Share the output** with me so I can see:
   - How many unique storage systems you have
   - How many tenant nodes are created
   - Whether parent relationships are correct

3. **Based on output**, we'll either:
   - Fix system name population
   - Create tenant mappings
   - Adjust visualization if you only have 1 system

---

## 💡 Quick Test

If you want to quickly test with sample data that has proper hierarchy:

```bash
# Create a test volume with explicit system name
docker-compose exec db psql -U admin -d san_dashboard -c "
INSERT INTO capacity_volumes (
  report_date, name, storage_system_id, storage_system_name, pool,
  provisioned_capacity_gib, used_capacity_gib, available_capacity_gib
) 
SELECT 
  CURRENT_DATE,
  'TestVolume_' || generate_series,
  1,
  CASE 
    WHEN generate_series % 2 = 0 THEN 'TestSystemA'
    ELSE 'TestSystemB'
  END,
  'TestPool' || (generate_series % 5),
  100,
  60,
  40
FROM generate_series(1, 20);
"

# Refresh dashboard and check treemap
```

---

**Next Step**: Run the diagnostic script and share the output. That will tell us exactly what's wrong with the hierarchy! 🔍
