# 📊 Data Flow for Comparison Table Chart

## Overview
The **"Simple Average vs Weighted Average Comparison"** table is fed by the **`treemap_data`** object from the backend.

---

## 🔄 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DATABASE TABLE: storage_pools                               │
├─────────────────────────────────────────────────────────────────┤
│ Columns:                                                        │
│ - id, name, storage_system_name                                 │
│ - usable_capacity_gib, used_capacity_gib, available_capacity_gib│
│ - utilization_pct                                               │
│ - report_date                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. BACKEND FUNCTION: get_treemap_data()                        │
│    Location: backend/app/utils/processing.py:854               │
├─────────────────────────────────────────────────────────────────┤
│ Query:                                                          │
│   pools = db.query(StoragePool)                                 │
│         .filter(StoragePool.report_date == report_date)         │
│         .all()                                                  │
│                                                                 │
│ Processing:                                                     │
│ - Groups pools by storage_system_name                           │
│ - Calculates simple_average (avg of utilization_pct)           │
│ - Calculates weighted_average (used/total capacity)            │
│                                                                 │
│ Returns:                                                        │
│   {                                                             │
│     'simple_average': [                                         │
│       {name, storage_system, total_capacity_gib,                │
│        used_capacity_gib, available_capacity_gib,               │
│        utilization_pct},                                        │
│       ...                                                       │
│     ],                                                          │
│     'weighted_average': [...]                                   │
│   }                                                             │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. API ENDPOINT: /data/overview/enhanced                       │
│    Location: backend/app/api/v1/data.py:675                    │
├─────────────────────────────────────────────────────────────────┤
│ Function: get_enhanced_overview()                               │
│                                                                 │
│ Calls:                                                          │
│   treemap_data = get_treemap_data(db, report_date)             │
│                                                                 │
│ Response includes:                                              │
│   {                                                             │
│     "kpis": {...},                                              │
│     "alerts": {...},                                            │
│     "treemap_data": {                                           │
│       "simple_average": [...],                                  │
│       "weighted_average": [...]                                 │
│     },                                                          │
│     ...                                                         │
│   }                                                             │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. FRONTEND API CLIENT: dataAPI.getEnhancedOverview()          │
│    Location: frontend/lib/api.ts:84                            │
├─────────────────────────────────────────────────────────────────┤
│ HTTP GET: /data/overview/enhanced                               │
│ Params: { report_date, tenant }                                 │
│                                                                 │
│ Returns response with treemap_data                              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. REACT COMPONENT: OverviewPage                               │
│    Location: frontend/app/overview/page.tsx:74                 │
├─────────────────────────────────────────────────────────────────┤
│ State Management:                                               │
│   const [data, setData] = useState<OverviewData | null>(null); │
│                                                                 │
│ Data Fetch:                                                     │
│   const response = await dataAPI.getEnhancedOverview(           │
│     undefined,           // reportDate                          │
│     selectedTenant || undefined  // tenant filter               │
│   );                                                            │
│   setData(response.data);                                       │
│                                                                 │
│ Stores in state:                                                │
│   data.treemap_data = {                                         │
│     simple_average: [...],                                      │
│     weighted_average: [...]                                     │
│   }                                                             │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. COMPARISON TABLE RENDER                                     │
│    Location: frontend/app/overview/page.tsx:825                │
├─────────────────────────────────────────────────────────────────┤
│ Accesses data:                                                  │
│   treemap_data.simple_average                                   │
│   treemap_data.weighted_average                                 │
│                                                                 │
│ Processing Logic (lines 888-990):                              │
│ 1. Groups pools by TENANT (inferred from pool names)           │
│ 2. For each tenant:                                             │
│    - Collects systems (Set of storage_system names)            │
│    - Collects pools (array of pool names)                      │
│    - Calculates simple_avg (avg of utilizations)               │
│    - Calculates weighted_avg (total_used / total_capacity)     │
│                                                                 │
│ Renders table with columns:                                    │
│   - Tenant                                                      │
│   - Systems (comma-separated)                                   │
│   - Pool Names (comma-separated)                                │
│   - Simple Avg % (with color badge)                            │
│   - Weighted Avg % (with color badge)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Structure Example

### Database Table: `storage_pools`
```sql
id | name   | storage_system_name | usable_capacity_gib | used_capacity_gib | utilization_pct | report_date
---+--------+---------------------+---------------------+-------------------+-----------------+------------
1  | Pool1  | System A            | 1000                | 800               | 80.0            | 2024-12-23
2  | Pool2  | System A            | 500                 | 250               | 50.0            | 2024-12-23
3  | Pool3  | System B            | 2000                | 1600              | 80.0            | 2024-12-23
```

### Backend Response: `treemap_data.simple_average`
```json
[
  {
    "name": "All Storage",
    "storage_system": "",
    "total_capacity_gib": 3500,
    "used_capacity_gib": 2650,
    "available_capacity_gib": 850,
    "utilization_pct": 70.0
  },
  {
    "name": "System A",
    "storage_system": "All Storage",
    "total_capacity_gib": 1500,
    "used_capacity_gib": 1050,
    "available_capacity_gib": 450,
    "utilization_pct": 65.0
  },
  {
    "name": "Pool1",
    "storage_system": "System A",
    "total_capacity_gib": 1000,
    "used_capacity_gib": 800,
    "available_capacity_gib": 200,
    "utilization_pct": 80.0
  },
  {
    "name": "Pool2",
    "storage_system": "System A",
    "total_capacity_gib": 500,
    "used_capacity_gib": 250,
    "available_capacity_gib": 250,
    "utilization_pct": 50.0
  }
]
```

### Frontend Processing: Tenant Grouping
The frontend code takes the pool nodes (those with `storage_system` != '') and groups them by tenant:

```javascript
// Lines 888-990 in page.tsx
const tenantMap = new Map();

treemap_data.simple_average.forEach((pool) => {
  if (pool.storage_system && pool.storage_system !== '') {
    // Skip root and system nodes, process only pools
    
    // Infer tenant from pool name
    let tenant = inferTenantFromPoolName(pool.name);
    
    // Group by tenant
    tenantMap.get(tenant).systems.add(pool.storage_system);
    tenantMap.get(tenant).pools.push(pool.name);
    tenantMap.get(tenant).utilizations.push(pool.utilization_pct);
  }
});

// Calculate averages
for (const [tenant, data] of tenantMap) {
  simple_avg = data.utilizations.reduce((a,b) => a+b) / data.utilizations.length;
  weighted_avg = (data.used_capacity / data.total_capacity) * 100;
}
```

### Final Table Render
```
| Tenant   | Systems         | Pool Names       | Simple Avg % | Weighted Avg % |
|----------|-----------------|------------------|--------------|----------------|
| Tenant X | System A, B     | Pool1, Pool2, 5  | 61.7%        | 65.2%          |
| Tenant Y | System A        | Pool3            | 48.0%        | 48.0%          |
```

---

## 🔍 Key Points

1. **Primary Data Source**: `storage_pools` database table
2. **Aggregation Logic**: Backend groups by `storage_system_name`, Frontend re-groups by tenant
3. **Calculation Methods**:
   - **Simple Average**: `SUM(utilization_pct) / COUNT(pools)`
   - **Weighted Average**: `(SUM(used_capacity) / SUM(total_capacity)) * 100`
4. **Tenant Inference**: Frontend infers tenant from pool names (Pool1-5 → Tenant X, etc.)
5. **Data Flow**: Database → Backend Processing → API → Frontend State → Table Render

---

## 🚨 Important Note

**The tenant grouping is currently done on the FRONTEND** using pool name pattern matching. For production, this should be moved to the backend where actual tenant-pool mappings exist in the `tenant_pool_mappings` table.

### Recommended Improvement:
The backend should join `storage_pools` with `tenant_pool_mappings` and include `tenant_name` in the treemap_data response:

```python
# In backend/app/utils/processing.py
def get_treemap_data_with_tenants(db: Session, report_date: date):
    # Join pools with tenant mappings
    query = db.query(StoragePool, TenantPoolMapping.tenant_id, Tenant.name)\
        .outerjoin(TenantPoolMapping, 
                   and_(StoragePool.name == TenantPoolMapping.pool_name,
                        StoragePool.storage_system_name == TenantPoolMapping.storage_system))\
        .outerjoin(Tenant, TenantPoolMapping.tenant_id == Tenant.id)\
        .filter(StoragePool.report_date == report_date)
    
    # Include tenant_name in response
    result.append({
        'name': pool.name,
        'storage_system': pool.storage_system_name,
        'tenant_name': tenant_name or 'UNKNOWN',  # ← ADD THIS
        ...
    })
```

This would eliminate the need for frontend pattern matching and provide accurate tenant assignments.

---

**File**: DATA_FLOW_COMPARISON_TABLE.md  
**Location**: /home/user/webapp/DATA_FLOW_COMPARISON_TABLE.md  
**Last Updated**: December 23, 2024
