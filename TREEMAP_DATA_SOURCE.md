# 🌳 Treemap Chart - Data Source Documentation

## Overview
The **Capacity Treemap** chart uses the **SAME data source** as the Comparison Table: **`treemap_data.weighted_average`** from the backend.

---

## 📊 Data Source

### Primary Source
- **Data Object**: `treemap_data.weighted_average`
- **Origin**: Backend function `get_treemap_data()` in `backend/app/utils/processing.py:854`
- **Database Table**: `storage_pools`

### Data Structure
```typescript
treemap_data: {
  simple_average: TreemapNode[];
  weighted_average: TreemapNode[];  // ← Used by Treemap Chart
}

interface TreemapNode {
  name: string;                    // Pool name or System name or "All Storage"
  storage_system: string;          // Parent node name (for hierarchy)
  total_capacity_gib: number;
  used_capacity_gib: number;
  available_capacity_gib: number;
  utilization_pct: number;
}
```

---

## 🔄 Complete Data Flow (Treemap Chart)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DATABASE: storage_pools table                               │
├─────────────────────────────────────────────────────────────────┤
│ Contains:                                                       │
│ - Pool names (Pool1, Pool2, etc.)                              │
│ - Storage system names (System A, System B, etc.)              │
│ - Capacity metrics (usable, used, available in GiB)            │
│ - Utilization percentages                                       │
│ - Report dates                                                  │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. BACKEND: get_treemap_data()                                 │
│    Location: backend/app/utils/processing.py:854               │
├─────────────────────────────────────────────────────────────────┤
│ Weighted Average Calculation:                                   │
│                                                                 │
│ Step 1: Query all pools                                        │
│   pools = db.query(StoragePool)                                │
│          .filter(report_date == date)                          │
│          .all()                                                │
│                                                                 │
│ Step 2: Calculate totals                                       │
│   total_capacity = sum(p.usable_capacity_gib)                  │
│   total_used = sum(p.used_capacity_gib)                        │
│   total_available = sum(p.available_capacity_gib)              │
│                                                                 │
│ Step 3: Build hierarchy                                        │
│   Root Node:                                                    │
│     - name: "All Storage"                                       │
│     - storage_system: ""  (empty = root)                       │
│     - utilization: (total_used / total_capacity) * 100         │
│                                                                 │
│   System Nodes:                                                 │
│     - name: "System A", "System B", etc.                        │
│     - storage_system: "All Storage"  (parent)                  │
│     - utilization: (system_used / system_capacity) * 100       │
│                                                                 │
│   Pool Nodes:                                                   │
│     - name: "Pool1", "Pool2", etc.                              │
│     - storage_system: "System A" or "System B"  (parent)       │
│     - utilization: pool.utilization_pct                        │
│                                                                 │
│ Returns: weighted_average array with all nodes                 │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. API: /data/overview/enhanced                                │
│    Returns treemap_data in response                            │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. FRONTEND: OverviewPage Component                            │
│    Location: frontend/app/overview/page.tsx:755                │
├─────────────────────────────────────────────────────────────────┤
│ Plotly Treemap Configuration:                                   │
│                                                                 │
│ data={[                                                         │
│   {                                                             │
│     type: 'treemap',                                            │
│     labels: treemap_data.weighted_average.map(d => d.name),     │
│     parents: treemap_data.weighted_average.map(d => d.storage_system),│
│     values: treemap_data.weighted_average.map(d => d.total_capacity_gib),│
│     marker: {                                                   │
│       colors: treemap_data.weighted_average.map(d => d.utilization_pct),│
│       colorscale: 'RdYlGn_r',  // Red-Yellow-Green reversed    │
│       cmid: 50,                                                 │
│       cmin: 0,                                                  │
│       cmax: 100                                                 │
│     },                                                          │
│     ...                                                         │
│   }                                                             │
│ ]}                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Hierarchy Structure

The treemap creates a **3-level hierarchy**:

```
All Storage (Root)
├── System A (Level 1)
│   ├── Pool1 (Level 2)
│   ├── Pool2 (Level 2)
│   └── Pool5 (Level 2)
└── System B (Level 1)
    ├── Pool3 (Level 2)
    ├── Pool6 (Level 2)
    └── Pool7 (Level 2)
```

### How Plotly Builds the Hierarchy

Plotly uses the `labels` and `parents` arrays to build the tree:

```javascript
labels:  ["All Storage", "System A", "Pool1", "Pool2", "System B", "Pool3"]
parents: ["",           "All Storage", "System A", "System A", "All Storage", "System B"]
```

- **Root nodes** have `parent = ""` (empty string)
- **System nodes** have `parent = "All Storage"`
- **Pool nodes** have `parent = "System A"` or `"System B"` etc.

---

## 🎨 Visual Mapping

### Size (Box Area)
- **Represents**: `total_capacity_gib`
- **Calculation**: Larger capacity = larger box
- **Example**: A 1000 GiB pool shows bigger than a 100 GiB pool

### Color
- **Represents**: `utilization_pct`
- **Color Scale**: Red-Yellow-Green (reversed)
  - 🟢 **Green** (0-50%): Low utilization, plenty of space
  - 🟡 **Yellow** (50-75%): Moderate utilization
  - 🟠 **Orange** (75-90%): High utilization
  - 🔴 **Red** (90-100%): Critical, almost full

### Text Labels
Shows on each box:
```
Pool Name
123.5 TiB
85%
```

### Hover Information
When you hover over a box:
```
System: System A
Pool: Pool1
Total: 1000.00 TiB
Used: 850.00 TiB
Available: 150.00 TiB
Utilization: 85.0%
```

---

## 📋 Example Data Flow

### Database Query Result
```sql
SELECT 
  name,           -- "Pool1", "Pool2", etc.
  storage_system_name,  -- "System A", "System B"
  usable_capacity_gib,  -- 1000, 500, etc.
  used_capacity_gib,    -- 800, 250, etc.
  available_capacity_gib, -- 200, 250, etc.
  utilization_pct      -- 80.0, 50.0, etc.
FROM storage_pools
WHERE report_date = '2024-12-23'
```

### Backend Processing (weighted_average)
```python
# Build hierarchy
weighted_result = [
  {
    'name': 'All Storage',
    'storage_system': '',  # Root
    'total_capacity_gib': 3500,
    'used_capacity_gib': 2650,
    'available_capacity_gib': 850,
    'utilization_pct': 75.7  # (2650/3500)*100
  },
  {
    'name': 'System A',
    'storage_system': 'All Storage',  # Parent: All Storage
    'total_capacity_gib': 1500,
    'used_capacity_gib': 1050,
    'available_capacity_gib': 450,
    'utilization_pct': 70.0  # (1050/1500)*100
  },
  {
    'name': 'Pool1',
    'storage_system': 'System A',  # Parent: System A
    'total_capacity_gib': 1000,
    'used_capacity_gib': 800,
    'available_capacity_gib': 200,
    'utilization_pct': 80.0
  },
  {
    'name': 'Pool2',
    'storage_system': 'System A',  # Parent: System A
    'total_capacity_gib': 500,
    'used_capacity_gib': 250,
    'available_capacity_gib': 250,
    'utilization_pct': 50.0
  }
]
```

### Frontend Rendering
Plotly receives this data and creates:
- **1 large box** for "All Storage" (entire chart area)
- **2 medium boxes** for "System A" and "System B" (subdivisions)
- **Multiple small boxes** for each pool within systems
- **Colors** based on utilization_pct
- **Interactive drill-down** via pathbar at top

---

## 🔍 Key Differences: Treemap vs Comparison Table

Both use the **same data source** (`treemap_data`), but:

### Treemap Chart
- **Uses**: `treemap_data.weighted_average`
- **Display**: Hierarchical visual boxes
- **Purpose**: See capacity distribution and utilization at a glance
- **Interaction**: Drill-down by clicking, hover for details
- **Grouping**: All Storage → Systems → Pools (3 levels)

### Comparison Table
- **Uses**: Both `simple_average` AND `weighted_average`
- **Display**: Tabular rows and columns
- **Purpose**: Compare calculation methods per tenant
- **Interaction**: Sort, scroll, read exact numbers
- **Grouping**: By Tenant (frontend regrouping)

---

## 🚨 Why Treemap Might Be Blank

If the treemap is showing blank, possible causes:

1. **No Data**: `treemap_data.weighted_average` is empty or null
2. **Invalid Hierarchy**: Parent-child relationships broken
3. **Zero Capacities**: All `total_capacity_gib` values are 0
4. **Frontend Error**: JavaScript error in rendering

### Debug Steps:
```javascript
// Check browser console for this debug output (line 747-753):
console.log('Treemap Data:', {
  count: treemap_data.weighted_average.length,
  sample: treemap_data.weighted_average.slice(0, 3)
});
```

Expected output:
```javascript
Treemap Data: {
  count: 15,  // Should be > 0
  sample: [
    {name: "All Storage", storage_system: "", ...},
    {name: "System A", storage_system: "All Storage", ...},
    {name: "Pool1", storage_system: "System A", ...}
  ]
}
```

If `count: 0` → No data from backend
If parent-child mismatch → Hierarchy broken

---

## 📊 Database Schema

The treemap ultimately depends on these `storage_pools` columns:

```sql
CREATE TABLE storage_pools (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,              -- Pool name (Pool1, Pool2, etc.)
  storage_system_name VARCHAR(255) NOT NULL,  -- System name (System A, System B)
  usable_capacity_gib FLOAT,               -- Total capacity
  used_capacity_gib FLOAT,                 -- Used capacity
  available_capacity_gib FLOAT,            -- Available capacity
  utilization_pct FLOAT,                   -- Calculated: (used/usable)*100
  report_date DATE NOT NULL,               -- Data snapshot date
  ...
);
```

---

## 🎯 Summary

| Aspect | Details |
|--------|---------|
| **Data Source** | `treemap_data.weighted_average` from backend |
| **Backend Function** | `get_treemap_data()` in `processing.py:854` |
| **Database Table** | `storage_pools` |
| **API Endpoint** | `/data/overview/enhanced` |
| **Frontend Component** | `OverviewPage` at `page.tsx:755` |
| **Visualization Library** | Plotly.js (react-plotly.js) |
| **Chart Type** | Hierarchical Treemap (3 levels) |
| **Size Represents** | Total capacity (GiB/TiB/PiB) |
| **Color Represents** | Utilization percentage (0-100%) |
| **Hierarchy** | All Storage → Systems → Pools |

---

**File**: TREEMAP_DATA_SOURCE.md  
**Location**: /home/user/webapp/TREEMAP_DATA_SOURCE.md  
**Last Updated**: December 23, 2024
