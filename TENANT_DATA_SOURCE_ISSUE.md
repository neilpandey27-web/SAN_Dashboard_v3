# ⚠️ TENANT DATA SOURCE ISSUE

## Question
> "Are Tenant-Pool Mappings and Tenants table also being used for these charts to pull the tenant relationship for storage systems and pools?"

## Answer: **NO** ❌

The current implementation is **NOT using the actual tenant tables** from the database. Instead, it's using **hardcoded pattern matching** in the frontend.

---

## 🔍 Current Implementation (INCORRECT)

### What's Happening Now

**Backend (`backend/app/utils/processing.py`):**
```python
# Line 869-872: Queries capacity_volumes
volumes = db.query(CapacityVolume).filter(
    CapacityVolume.report_date == report_date
).all()

# ❌ NO JOIN with TenantPoolMapping
# ❌ NO JOIN with Tenant table
# ❌ NO tenant_name in the response
```

**Frontend (`frontend/app/overview/page.tsx`):**
```javascript
// Lines 907-924: HARDCODED pattern matching
let tenant = 'UNKNOWN';

// Try to infer tenant from pool name patterns
if (pool.name.match(/Pool[1-5]/)) {
    if (pool.name === 'Pool1' || pool.name === 'Pool2' || pool.name === 'Pool5') {
        tenant = 'Tenant X';  // ❌ HARDCODED
    } else if (pool.name === 'Pool3') {
        tenant = 'Tenant Y';  // ❌ HARDCODED
    } else if (pool.name === 'Pool4') {
        tenant = 'UNKNOWN';   // ❌ HARDCODED
    }
}
```

**Comment in Code:**
```javascript
// Line 890: "Since we don't have tenant data in treemap_data, we'll infer from pool/system names"
// Line 909: "TODO: Backend should include tenant_name in treemap_data"
```

---

## 📊 Database Tables (AVAILABLE BUT NOT USED)

### Tables That EXIST in Database

#### 1. `tenants` Table
```sql
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. `tenant_pool_mappings` Table
```sql
CREATE TABLE tenant_pool_mappings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    pool_name VARCHAR(255) NOT NULL,
    storage_system VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(pool_name, storage_system)
);
```

**Purpose:** Maps pools to tenants (e.g., "Pool1 on AGNB-R1 belongs to Tenant X")

---

## ❌ Problems with Current Implementation

### 1. **Hardcoded Tenant Names**
- Tenant names are hardcoded in frontend: "Tenant X", "Tenant Y", "Tenant Z"
- Not using actual tenant data from `tenants` table
- Cannot add/modify tenants without code changes

### 2. **Pattern Matching Logic**
- Uses pool name patterns (`Pool1`, `Pool2`, etc.) to guess tenant
- Fragile: breaks if pool names change
- Not scalable: what if you have 100 pools?

### 3. **Inaccurate Data**
- Pattern matching may assign wrong tenant
- No validation against actual tenant-pool mappings
- "UNKNOWN" tenant for pools that don't match pattern

### 4. **Data Inconsistency**
- Frontend has tenant logic (presentation layer)
- Backend doesn't know about tenant assignments (data layer)
- Violates separation of concerns

---

## ✅ CORRECT Implementation (RECOMMENDED)

### What Should Happen

**Backend (`backend/app/utils/processing.py`):**
```python
def get_treemap_data(db: Session, report_date: date) -> Dict[str, List[Dict]]:
    """
    Get hierarchical data for treemap visualization with tenant information.
    """
    # Query capacity_volumes and JOIN with tenant_pool_mappings
    query = db.query(
        CapacityVolume,
        Tenant.name.label('tenant_name')
    ).outerjoin(
        TenantPoolMapping,
        and_(
            TenantPoolMapping.pool_name == CapacityVolume.pool,
            TenantPoolMapping.storage_system == CapacityVolume.storage_system
        )
    ).outerjoin(
        Tenant,
        Tenant.id == TenantPoolMapping.tenant_id
    ).filter(
        CapacityVolume.report_date == report_date
    )
    
    volumes = query.all()
    
    # Aggregate by pool and include tenant_name
    for vol, tenant_name in volumes:
        pool_data[key] = {
            'pool': vol.pool,
            'system': vol.storage_system,
            'tenant_name': tenant_name or 'UNKNOWN',  # ✅ From database
            'provisioned': provisioned,
            'used': used,
            'available': available
        }
    
    # Return data with tenant_name included
    return {
        'simple_average': [...],  # Each item includes 'tenant_name'
        'weighted_average': [...]  # Each item includes 'tenant_name'
    }
```

**Frontend (`frontend/app/overview/page.tsx`):**
```javascript
// Lines 902-937: Use tenant_name from backend
treemap_data.simple_average.forEach((pool) => {
    if (!pool.storage_system || pool.storage_system === '' || pool.name === 'All Storage') {
        return;
    }
    
    // ✅ Use tenant_name from backend (no pattern matching)
    const tenant = pool.tenant_name || 'UNKNOWN';
    
    if (!tenantMap.has(tenant)) {
        tenantMap.set(tenant, {
            systems: new Set<string>(),
            pools: [],
            utilizations: [],
            used_capacity: 0,
            total_capacity: 0
        });
    }
    
    const tenantData = tenantMap.get(tenant)!;
    tenantData.systems.add(pool.storage_system);
    tenantData.pools.push(pool.name);
    // ... rest of the logic
});
```

---

## 📋 Required Changes

### Step 1: Update Backend (HIGH PRIORITY)

**File:** `backend/app/utils/processing.py`

**Changes:**
1. Add imports:
   ```python
   from app.db.models import TenantPoolMapping, Tenant
   from sqlalchemy import and_
   ```

2. Modify `get_treemap_data()` function:
   - Add JOIN with `TenantPoolMapping`
   - Add JOIN with `Tenant`
   - Include `tenant_name` in pool data
   - Include `tenant_name` in return value

### Step 2: Update Frontend (MEDIUM PRIORITY)

**File:** `frontend/app/overview/page.tsx`

**Changes:**
1. Remove hardcoded pattern matching (lines 912-924)
2. Use `pool.tenant_name` from backend response
3. Remove TODO comment (line 909)

### Step 3: Ensure Data Exists (CRITICAL)

**Database Setup:**
1. Verify `tenants` table has data:
   ```sql
   SELECT * FROM tenants;
   ```

2. Verify `tenant_pool_mappings` table has data:
   ```sql
   SELECT * FROM tenant_pool_mappings;
   ```

3. If empty, populate with actual mappings:
   ```sql
   -- Insert tenants
   INSERT INTO tenants (name, description) VALUES
   ('Tenant X', 'Production Tenant'),
   ('Tenant Y', 'Development Tenant'),
   ('Tenant Z', 'Staging Tenant');
   
   -- Insert pool mappings
   INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system) VALUES
   (1, 'Pool1', 'AGNB-R1'),
   (1, 'Pool2', 'AGNB-R1'),
   (2, 'Pool3', 'AGNB-R2'),
   (3, 'Pool4', 'AGNB-R3');
   ```

---

## 🎯 Benefits of Correct Implementation

### 1. **Data-Driven**
- Tenant assignments come from database
- Can be managed via admin interface
- No code changes needed to add/modify tenants

### 2. **Accurate**
- Uses actual tenant-pool mappings
- No guessing or pattern matching
- Validated data from single source of truth

### 3. **Scalable**
- Works with any number of tenants/pools
- No hardcoded logic
- Easy to maintain and extend

### 4. **Consistent**
- Same tenant data across all charts
- Backend owns the logic (proper separation)
- Frontend just displays what backend provides

---

## 📊 Data Flow Comparison

### Current Flow (WRONG)
```
capacity_volumes
  ↓
Backend: Aggregate by pool (NO tenant info)
  ↓
API Response: { pool_name, system, capacity, utilization }
  ↓
Frontend: Pattern match pool name → Guess tenant
  ↓
Display: Tenant X, Tenant Y, Tenant Z (hardcoded)
```

### Correct Flow (RECOMMENDED)
```
capacity_volumes
  ↓ JOIN
tenant_pool_mappings
  ↓ JOIN
tenants
  ↓
Backend: Aggregate by pool WITH tenant_name
  ↓
API Response: { pool_name, system, capacity, utilization, tenant_name }
  ↓
Frontend: Use tenant_name from response
  ↓
Display: Actual tenant names from database
```

---

## 🚀 Implementation Priority

**Priority: HIGH** 🔴

This should be fixed BEFORE production deployment because:
1. Current implementation uses fake/hardcoded tenant names
2. Tenant assignments may be incorrect
3. Not using existing database relationships
4. Violates data integrity principles

---

## 🔧 Quick Fix Steps

```bash
# 1. Update backend function
cd /home/user/webapp
nano backend/app/utils/processing.py
# - Add JOINs with TenantPoolMapping and Tenant
# - Include tenant_name in response

# 2. Update frontend component
nano frontend/app/overview/page.tsx
# - Remove hardcoded pattern matching
# - Use pool.tenant_name from backend

# 3. Restart both servers
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# 4. Verify
# - Check API response includes tenant_name
# - Check comparison table shows correct tenants
```

---

## 📝 Summary

**Current Status:** ❌ NOT using `tenants` and `tenant_pool_mappings` tables

**Impact:** 
- Tenant names are hardcoded ("Tenant X", "Tenant Y", "Tenant Z")
- Pattern matching in frontend to guess tenants
- Inaccurate tenant assignments

**Recommendation:** 
- Update backend to JOIN with tenant tables
- Include `tenant_name` in API response
- Remove frontend pattern matching
- Use actual database tenant relationships

**Effort:** Medium (2-3 hours)
**Risk:** Low
**Benefit:** High (data accuracy, maintainability)

---

**Document Created:** December 23, 2024  
**Issue:** Tenant data not using actual database tables  
**Status:** Identified, awaiting fix
