# Storage Insights Dashboard - Chart Blocks Reference

**Version:** 5.1.0  
**Last Updated:** December 18, 2024

This document provides a comprehensive reference for all chart blocks in the Overview Dashboard, including their data sources, calculation formulas, and display logic.

---

## 📊 Overview Dashboard - Chart Blocks

### 1. KPI Cards (Top Row)

#### 1.1 Total Provisioned Capacity
**Chart Block Title:** 📦 Total Provisioned Capacity

**Primary Table:** `capacity_volumes`

**Key Fields:**
- `provisioned_capacity_gib`

**Calculation Formula:**
```sql
SELECT ROUND(SUM(provisioned_capacity_gib) / 1024, 2) AS total_capacity_tib
FROM capacity_volumes
WHERE report_date = (SELECT MAX(report_date) FROM capacity_volumes)
```

**Display Logic:**
- Aggregates all provisioned capacity from volumes
- Converts GiB to TiB (divide by 1024)
- Rounds to 2 decimal places
- Shows single total value across all volumes
- Unit switcher available (GiB/TiB/PiB)

**Backend Code:**
```python
total_provisioned_capacity_gib = sum(v.provisioned_capacity_gib or 0 for v in volumes)
kpis["total_capacity_tb"] = round(gib_to_tb(total_provisioned_capacity_gib), 2)
```

---

#### 1.2 Used Provisioned Capacity
**Chart Block Title:** 💾 Used Provisioned Capacity

**Primary Table:** `capacity_volumes`

**Key Fields:**
- `used_capacity_gib`

**Calculation Formula:**
```sql
SELECT ROUND(SUM(used_capacity_gib) / 1024, 2) AS total_used_tib
FROM capacity_volumes
WHERE report_date = (SELECT MAX(report_date) FROM capacity_volumes)
```

**Display Logic:**
- Aggregates all used capacity from volumes
- Converts GiB to TiB (divide by 1024)
- Rounds to 2 decimal places
- Shows single total value across all volumes
- Unit switcher available (GiB/TiB/PiB)

**Backend Code:**
```python
total_used_provisioned_gib = sum(v.used_capacity_gib or 0 for v in volumes)
kpis["total_used_tb"] = round(gib_to_tb(total_used_provisioned_gib), 2)
```

---

#### 1.3 Unused Provisioned Capacity
**Chart Block Title:** 📊 Unused Provisioned Capacity

**Primary Table:** `capacity_volumes`

**Key Fields:**
- `available_capacity_gib`

**Calculation Formula:**
```sql
SELECT ROUND(SUM(available_capacity_gib) / 1024, 2) AS total_available_tib
FROM capacity_volumes
WHERE report_date = (SELECT MAX(report_date) FROM capacity_volumes)
```

**Display Logic:**
- Aggregates all available capacity from volumes
- Converts GiB to TiB (divide by 1024)
- Rounds to 2 decimal places
- Shows single total value across all volumes
- Shows percentage free: (available / total) * 100
- Unit switcher available (GiB/TiB/PiB)

**Backend Code:**
```python
total_available_provisioned_gib = sum(v.available_capacity_gib or 0 for v in volumes)
kpis["total_available_tb"] = round(gib_to_tb(total_available_provisioned_gib), 2)
```

---

#### 1.4 Total Savings
**Chart Block Title:** 💰 Total Savings

**Primary Table:** `storage_systems`

**Key Fields:**
- `data_reduction_gib`

**Calculation Formula:**
```sql
SELECT ROUND(SUM(data_reduction_gib) / 1024, 2) AS total_savings_tib
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
```

**Display Logic:**
- Aggregates data reduction savings from all storage systems
- Represents compression + deduplication savings
- Converts GiB to TiB (divide by 1024)
- Shows single total value
- Unit switcher available (GiB/TiB/PiB)

**Backend Code:**
```python
total_savings_gib = sum(s.data_reduction_gib or 0 for s in systems)
kpis["total_savings_tb"] = gib_to_tb(total_savings_gib)
```

---

### 2. Resource Count Cards (Second Row - Left Side)

#### 2.1 Storage Systems
**Chart Block Title:** 🏢 Storage Systems

**Primary Table:** `storage_systems`

**Key Fields:**
- `COUNT(DISTINCT name)`

**Calculation Formula:**
```sql
SELECT COUNT(DISTINCT name) AS num_systems
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
```

**Display Logic:**
- Count of unique storage systems
- Simple integer count

**Backend Code:**
```python
kpis["num_systems"] = len(systems)
```

---

#### 2.2 Storage Pools
**Chart Block Title:** 💿 Storage Pools

**Primary Table:** `storage_pools`

**Key Fields:**
- `COUNT(DISTINCT name)`

**Calculation Formula:**
```sql
SELECT COUNT(DISTINCT name) AS num_pools
FROM storage_pools
WHERE report_date = (SELECT MAX(report_date) FROM storage_pools)
```

**Display Logic:**
- Count of unique storage pools
- Simple integer count

**Backend Code:**
```python
kpis["num_pools"] = len(pools)
```

---

#### 2.3 Hosts
**Chart Block Title:** 🖥️ Hosts

**Primary Table:** `capacity_hosts`

**Key Fields:**
- `COUNT(DISTINCT name)`

**Calculation Formula:**
```sql
SELECT COUNT(DISTINCT name) AS num_hosts
FROM capacity_hosts
WHERE report_date = (SELECT MAX(report_date) FROM capacity_hosts)
```

**Display Logic:**
- Count of unique hosts
- Simple integer count

**Backend Code:**
```python
kpis["num_hosts"] = len(hosts)
```

---

### 3. Utilization Gauges (Second Row - Right Side)

#### 3.1 Overall Provisioned Capacity Utilization
**Chart Block Title:** Overall Provisioned Capacity Utilization

**Primary Table:** `capacity_volumes`

**Key Fields:**
- `used_capacity_gib`
- `provisioned_capacity_gib`

**Calculation Formula:**
```sql
SELECT 
    (SUM(used_capacity_gib) / SUM(provisioned_capacity_gib)) * 100 AS provisioned_utilization_pct
FROM capacity_volumes
WHERE report_date = (SELECT MAX(report_date) FROM capacity_volumes)
```

**Display Logic:**
- Calculates what percentage of provisioned capacity is actually being used
- Formula: (sum of used / sum of provisioned) * 100
- Shows as gauge chart (0-100%)
- Color coding:
  - Green (0-50%): Healthy
  - Yellow (50-75%): Warning
  - Orange (75-90%): Critical
  - Red (90-100%): Urgent
- Threshold marker at 90%

**Backend Code:**
```python
total_used_provisioned_gib = sum(v.used_capacity_gib or 0 for v in volumes)
total_provisioned_capacity_gib = sum(v.provisioned_capacity_gib or 0 for v in volumes)
provisioned_utilization_pct = calculate_utilization_pct(total_used_provisioned_gib, total_provisioned_capacity_gib)
kpis["provisioned_utilization_pct"] = round(provisioned_utilization_pct, 1)
```

---

#### 3.2 Overall Storage System Utilization
**Chart Block Title:** Overall Storage System Utilization

**Primary Table:** `storage_systems`

**Key Fields:**
- `usable_capacity_gib`
- `available_capacity_gib`

**Calculation Formula:**
```sql
SELECT 
    ((SUM(usable_capacity_gib) - SUM(available_capacity_gib)) / SUM(usable_capacity_gib)) * 100 AS system_utilization_pct
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
```

**Display Logic:**
- Calculates system-level utilization based on usable capacity
- Formula: ((usable - available) / usable) * 100
- Shows as gauge chart (0-100%)
- Same color coding as provisioned utilization
- Threshold marker at 90%

**Backend Code:**
```python
system_usable_capacity_gib = sum(s.usable_capacity_gib or 0 for s in systems)
system_available_capacity_gib = sum(s.available_capacity_gib or 0 for s in systems)
system_used_capacity_gib = system_usable_capacity_gib - system_available_capacity_gib
system_utilization_pct = calculate_utilization_pct(system_used_capacity_gib, system_usable_capacity_gib)
kpis["system_utilization_pct"] = round(system_utilization_pct, 1)
```

---

### 4. Critical Capacity Alerts

#### 4.1 Critical Capacity Alerts Section
**Chart Block Title:** 🚨 CRITICAL CAPACITY ALERTS

**Primary Table:** `storage_pools`

**Key Fields:**
- `utilization_pct`
- `name`
- `storage_system_name`

**Calculation Formula:**
```sql
-- Critical Pools (> 80% utilization)
SELECT name, storage_system_name, utilization_pct
FROM storage_pools
WHERE report_date = (SELECT MAX(report_date) FROM storage_pools)
  AND utilization_pct > 80
ORDER BY utilization_pct DESC

-- Warning Pools (70-80% utilization)
SELECT name, storage_system_name, utilization_pct
FROM storage_pools
WHERE report_date = (SELECT MAX(report_date) FROM storage_pools)
  AND utilization_pct > 70 AND utilization_pct <= 80
ORDER BY utilization_pct DESC
```

**Display Logic:**
- Shows three counts:
  - Critical: Pools > 80% full
  - Warning: Pools 70-80% full
  - Urgent: Pools full in < 30 days
- Lists top 5 critical and warning pools
- Calculates "days until full" based on growth rate
- Color-coded alerts (red for critical, yellow for warning)

---

### 5. Capacity Forecasting

#### 5.1 Capacity Forecasting Chart
**Chart Block Title:** 📈 CAPACITY FORECASTING

**Primary Table:** `storage_pools`

**Key Fields:**
- `name`
- `storage_system_name`
- `utilization_pct`

**Calculation Formula:**
- Projects top 5 pools by utilization over 12 months
- Growth rate based on current utilization:
  - ≥95%: 2% per month
  - ≥80%: 1.5% per month
  - <80%: 1% per month

**Display Logic:**
- Line chart showing utilization projections
- X-axis: Months ahead (0-12)
- Y-axis: Utilization % (0-110%)
- Reference lines:
  - Yellow dashed: 70% (Warning)
  - Orange dashed: 80% (Critical)
  - Red dashed: 100% (Full)

**Backend Code:**
```python
for pool in top_pools:
    util = pool.utilization_pct or 0
    growth_rate = 0.02 if util >= 95 else 0.015 if util >= 80 else 0.01
    for month in range(13):
        projected = min(100, util + (growth_rate * 100 * month))
        projections.append(round(projected, 1))
```

---

### 6. Top Systems by Capacity

#### 6.1 Top 10 Systems by Capacity
**Chart Block Title:** Top 10 Systems by Capacity

**Primary Table:** `storage_systems`

**Key Fields:**
- `name`
- `usable_capacity_gib`
- `available_capacity_gib`

**Calculation Formula:**
```sql
SELECT 
    name,
    usable_capacity_gib / 1024 AS capacity_tb,
    (usable_capacity_gib - available_capacity_gib) / 1024 AS used_tb,
    available_capacity_gib / 1024 AS available_tb
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
ORDER BY usable_capacity_gib DESC
LIMIT 10
```

**Display Logic:**
- Stacked bar chart
- Green bars: Used capacity
- Blue bars: Available capacity
- X-axis: System names (angled 45°)
- Y-axis: Capacity in TiB (or selected unit)

---

### 7. System Utilization Distribution

#### 7.1 System Utilization Distribution
**Chart Block Title:** System Utilization Distribution

**Primary Table:** `storage_systems`

**Key Fields:**
- `usable_capacity_gib`
- `available_capacity_gib`

**Calculation Formula:**
```sql
-- Group systems into 10% bins (0-10%, 10-20%, etc.)
SELECT 
    CASE 
        WHEN ((usable_capacity_gib - available_capacity_gib) / usable_capacity_gib * 100) < 10 THEN '0-10%'
        WHEN ((usable_capacity_gib - available_capacity_gib) / usable_capacity_gib * 100) < 20 THEN '10-20%'
        -- ... and so on
    END AS utilization_bin,
    COUNT(*) AS system_count
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
GROUP BY utilization_bin
```

**Display Logic:**
- Bar chart showing distribution
- X-axis: Utilization ranges (0-10%, 10-20%, ..., 90-100%)
- Y-axis: Number of systems in each range
- Helps identify over/under-utilized systems

---

### 8. Capacity Treemap

#### 8.1 Capacity Treemap - Weighted Average
**Chart Block Title:** 🌳 Capacity Treemap - Weighted Average

**Primary Table:** `storage_pools`

**Key Fields:**
- `name`
- `storage_system_name`
- `usable_capacity_gib`
- `used_capacity_gib`
- `available_capacity_gib`
- `utilization_pct`

**Calculation Formula:**
```sql
-- Weighted Average Utilization by System
SELECT 
    storage_system_name,
    name AS pool_name,
    usable_capacity_gib,
    used_capacity_gib,
    available_capacity_gib,
    (SUM(used_capacity_gib) / SUM(usable_capacity_gib)) * 100 AS weighted_avg_utilization
FROM storage_pools
WHERE report_date = (SELECT MAX(report_date) FROM storage_pools)
GROUP BY storage_system_name, name
```

**Display Logic:**
- Hierarchical treemap visualization
- Parent nodes: Storage systems
- Child nodes: Storage pools
- Size: Proportional to pool capacity
- Color: Based on utilization % (green → yellow → orange → red)
- Interactive: Click to drill down, hover for details

---

### 9. Simple vs Weighted Average Comparison

#### 9.1 Simple Average vs Weighted Average Comparison
**Chart Block Title:** 📊 Simple Average vs Weighted Average Comparison

**Primary Table:** `storage_pools`

**Key Fields:**
- `storage_system_name`
- `name`
- `utilization_pct`
- `usable_capacity_gib`
- `used_capacity_gib`

**Calculation Formulas:**

**Simple Average:**
```sql
-- Average of all pool utilization percentages
SELECT 
    storage_system_name,
    AVG(utilization_pct) AS simple_avg_utilization
FROM storage_pools
WHERE report_date = (SELECT MAX(report_date) FROM storage_pools)
GROUP BY storage_system_name
```

**Weighted Average:**
```sql
-- Total used / Total capacity
SELECT 
    storage_system_name,
    (SUM(used_capacity_gib) / SUM(usable_capacity_gib)) * 100 AS weighted_avg_utilization
FROM storage_pools
WHERE report_date = (SELECT MAX(report_date) FROM storage_pools)
GROUP BY storage_system_name
```

**Display Logic:**
- Table format showing both metrics side by side
- Each row: Storage system
- Columns: Pool names, Simple Average %, Weighted Average %
- Color-coded badges (green/yellow/red)
- Tooltips explain calculation methods

---

### 10. Top 20 Hosts by Consumption

#### 10.1 Top 20 Hosts by Consumption
**Chart Block Title:** Top 20 Hosts by Consumption

**Primary Table:** `capacity_hosts`

**Key Fields:**
- `name`
- `used_san_capacity_gib`

**Calculation Formula:**
```sql
SELECT 
    name,
    used_san_capacity_gib / 1024 AS used_capacity_tb
FROM capacity_hosts
WHERE report_date = (SELECT MAX(report_date) FROM capacity_hosts)
ORDER BY used_san_capacity_gib DESC
LIMIT 20
```

**Display Logic:**
- Bar chart
- X-axis: Host names (angled 45°)
- Y-axis: Used capacity in TB
- Red bars for emphasis
- Helps identify top consumers

---

### 11. Storage Efficiency & Savings

#### 11.1 Storage Efficiency & Savings
**Chart Block Title:** 💰 Storage Efficiency & Savings

**Primary Table:** `storage_systems`

**Key Fields:**
- `name`
- `data_reduction_gib`

**Calculation Formula:**
```sql
SELECT 
    name,
    data_reduction_gib / 1024 AS savings_tb,
    total_compression_ratio
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
  AND data_reduction_gib > 0
ORDER BY data_reduction_gib DESC
LIMIT 10
```

**Display Logic:**
- Bar chart showing top 10 systems by savings
- X-axis: System names
- Y-axis: Capacity savings in TB
- Green bars (positive savings)
- Values labeled on bars

---

### 12. Capacity by Storage Type

#### 12.1 Capacity by Storage Type
**Chart Block Title:** 📊 Capacity by Storage Type

**Primary Table:** `storage_systems`

**Key Fields:**
- `type`
- `usable_capacity_gib`

**Calculation Formula:**
```sql
SELECT 
    type,
    SUM(usable_capacity_gib) / 1024 AS capacity_tb
FROM storage_systems
WHERE report_date = (SELECT MAX(report_date) FROM storage_systems)
GROUP BY type
```

**Display Logic:**
- Donut chart (pie chart with hole)
- Shows distribution by storage type (FlashSystem, SAN, NAS, etc.)
- Percentages and labels shown
- Legend on right side

---

### 13. Intelligent Recommendations

#### 13.1 Intelligent Recommendations
**Chart Block Title:** 💡 INTELLIGENT RECOMMENDATIONS

**Primary Tables:** `storage_pools`, `storage_systems`

**Key Fields:** Various (depends on recommendation type)

**Calculation Logic:**

**Urgent Capacity:**
```sql
-- Pools that will be full in < 30 days
SELECT name, storage_system_name, utilization_pct
FROM storage_pools
WHERE days_until_full < 30 AND utilization_pct > 80
```

**Efficiency Opportunity:**
```sql
-- Systems with < 30% utilization
SELECT name, available_capacity_gib
FROM storage_systems
WHERE ((usable_capacity_gib - available_capacity_gib) / usable_capacity_gib * 100) < 30
```

**Savings Achievement:**
```sql
-- Total savings percentage
SELECT 
    (SUM(data_reduction_gib) / SUM(usable_capacity_gib) * 100) AS savings_pct
FROM storage_systems
```

**Display Logic:**
- Color-coded alert cards
- Red: Urgent actions required
- Blue: Informational recommendations
- Green: Positive achievements
- Each recommendation includes:
  - Title
  - Message
  - Detailed action items

---

## 📋 Summary Table

| Chart Block | Primary Table | Key Calculation | Output Type |
|-------------|---------------|-----------------|-------------|
| Total Provisioned Capacity | capacity_volumes | SUM(provisioned_capacity_gib) / 1024 | Single Value (TiB) |
| Used Provisioned Capacity | capacity_volumes | SUM(used_capacity_gib) / 1024 | Single Value (TiB) |
| Unused Provisioned Capacity | capacity_volumes | SUM(available_capacity_gib) / 1024 | Single Value (TiB) |
| Total Savings | storage_systems | SUM(data_reduction_gib) / 1024 | Single Value (TiB) |
| Storage Systems | storage_systems | COUNT(DISTINCT name) | Integer |
| Storage Pools | storage_pools | COUNT(DISTINCT name) | Integer |
| Hosts | capacity_hosts | COUNT(DISTINCT name) | Integer |
| Overall Provisioned Capacity Utilization | capacity_volumes | (SUM(used) / SUM(provisioned)) * 100 | Gauge (%) |
| Overall Storage System Utilization | storage_systems | ((usable - available) / usable) * 100 | Gauge (%) |
| Critical Alerts | storage_pools | WHERE utilization_pct > threshold | List |
| Capacity Forecasting | storage_pools | Projected growth over 12 months | Line Chart |
| Top Systems | storage_systems | ORDER BY capacity DESC LIMIT 10 | Stacked Bar |
| Utilization Distribution | storage_systems | GROUP BY utilization bins | Bar Chart |
| Capacity Treemap | storage_pools | Hierarchical by system/pool | Treemap |
| Simple vs Weighted | storage_pools | AVG vs SUM(used)/SUM(total) | Table |
| Top Hosts | capacity_hosts | ORDER BY used DESC LIMIT 20 | Bar Chart |
| Savings | storage_systems | ORDER BY savings DESC LIMIT 10 | Bar Chart |
| Storage Types | storage_systems | GROUP BY type | Donut Chart |
| Recommendations | Multiple | Various alert conditions | Alert Cards |

---

## 🔑 Key Notes

### Calculation Methods

**Volume-Based (Provisioned):**
- More granular
- Based on actual volume allocations
- Better for capacity planning
- Used for: Total, Used, Unused Provisioned Capacity

**System-Based (Physical):**
- System-level aggregation
- Based on physical storage capacity
- Better for hardware planning
- Used for: Storage System Utilization, Savings

### Unit Conversions

All capacity values support unit switching:
- **GiB**: Gibibytes (1024-based)
- **TiB**: Tebibytes (1024 GiB)
- **PiB**: Pebibytes (1024 TiB)

Conversion formulas:
```python
def gib_to_tib(gib): return gib / 1024
def gib_to_pib(gib): return gib / (1024 * 1024)
```

### Utilization Calculations

Two methods used in dashboard:

1. **Provisioned Utilization**: `(used / provisioned) * 100`
   - Based on volume-level data
   - Shows how much of allocated capacity is used

2. **System Utilization**: `((usable - available) / usable) * 100`
   - Based on system-level data
   - Shows overall storage system fill rate

---

## 📌 Version History

- **v5.1.0** (Dec 18, 2024): Added two utilization gauges, renamed Available to Unused Provisioned Capacity
- **v5.0.0** (Dec 18, 2024): Updated to use capacity_volumes for Total/Used Capacity, FlashSystem preprocessing
- **v4.x** (Earlier): Original dashboard with system-based calculations

---

**Document maintained by:** Storage Insights Development Team  
**For questions or updates:** See main documentation
