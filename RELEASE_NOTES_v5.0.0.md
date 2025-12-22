# Release Notes - Version 5.0.0

**Release Date:** December 18, 2024  
**Download Link:** https://www.genspark.ai/api/files/s/9ue4IyIY

---

## 🎯 Overview

Version 5.0.0 introduces major improvements to capacity calculations, FlashSystem support, and database schema updates. This release focuses on providing more accurate provisioned capacity reporting and automated preprocessing for FlashSystem storage arrays.

---

## ✨ Major Features

### 1. FlashSystem Preprocessing Support

**NEW:** Automatic calculation of `available_capacity_gib` for FlashSystem volumes during Excel upload.

- **Applies to storage systems:** A9K-A1, A9KR-R1, A9KR-R2
- **Formula:** `available_capacity_gib = provisioned_capacity_gib - used_capacity_gib`
- **When it runs:** During Excel file upload preprocessing (before database insertion)
- **Effect:** Fills blank/null `available_capacity_gib` fields automatically for FlashSystem volumes

**Why this matters:**
- FlashSystem arrays often have blank `available_capacity_gib` in source data
- Manual calculation is error-prone and time-consuming
- Automated preprocessing ensures accurate capacity reporting

### 2. Enhanced Capacity Calculations

**UPDATED:** Total Capacity and Used Capacity now calculated from `capacity_volumes` table.

**Before v5.0.0:**
```sql
-- Total Capacity from storage_systems
SELECT SUM(usable_capacity_gib) FROM storage_systems

-- Used Capacity calculated as:
total_capacity - total_available
```

**After v5.0.0:**
```sql
-- Total Provisioned Capacity from capacity_volumes
SELECT ROUND(SUM(provisioned_capacity_gib) / 1024, 2) 
FROM capacity_volumes

-- Used Provisioned Capacity from capacity_volumes
SELECT ROUND(SUM(used_capacity_gib) / 1024, 2) 
FROM capacity_volumes
```

**Benefits:**
- ✅ More accurate granular capacity reporting
- ✅ Based on actual volume allocation (provisioned capacity)
- ✅ Better visibility into storage utilization
- ✅ Values rounded to 2 decimal places for consistency

### 3. Database Schema Update

**BREAKING CHANGE:** Column renamed in `capacity_volumes` table.

```sql
-- Old column name
capacity_gib

-- New column name  
provisioned_capacity_gib
```

**Migration included:** `migrations/v5.0.0_rename_capacity_column.sql`

**Why the change:**
- Better naming convention distinguishes provisioned vs physical capacity
- Aligns with industry terminology
- Reduces confusion about what the value represents

### 4. Chart Title Updates

**UPDATED:** Chart block titles in Overview dashboard.

| Old Title | New Title |
|-----------|-----------|
| 📦 Total Capacity | 📦 Total Provisioned Capacity |
| 💾 Used Capacity | 💾 Used Provisioned Capacity |

**Rationale:** Titles now accurately reflect that values represent provisioned (allocated) capacity, not physical storage capacity.

---

## 🔧 Technical Changes

### Backend Changes

#### `app/api/v1/data.py`
- Updated `get_enhanced_overview()` to query `capacity_volumes` table
- Changed Total Capacity calculation to use `SUM(provisioned_capacity_gib)`
- Changed Used Capacity calculation to use `SUM(used_capacity_gib)`
- Updated all API responses to use new column name
- Added rounding to 2 decimal places for both metrics

#### `app/utils/processing.py`
- **NEW FUNCTION:** `calculate_flashsystem_available_capacity(df)`
  - Identifies FlashSystem volumes by storage_system_name
  - Calculates available_capacity_gib for volumes with null values
  - Only updates records where available_capacity_gib is blank
- Added column mapping: `capacity_gib` → `provisioned_capacity_gib` for CapacityVolume
- Ensures backward compatibility with Excel files using old column name

#### `app/db/models.py`
- Renamed field: `capacity_gib` → `provisioned_capacity_gib` in CapacityVolume model
- Model now matches database schema

### Frontend Changes

#### `frontend/app/overview/page.tsx`
- Updated chart block titles to reflect provisioned capacity
- No functional changes to data display or calculations

### Database Changes

#### Migration Script
File: `migrations/v5.0.0_rename_capacity_column.sql`

```sql
ALTER TABLE capacity_volumes 
RENAME COLUMN capacity_gib TO provisioned_capacity_gib;
```

**To apply migration:**
```bash
cd backend
sqlite3 storage_insights.db < ../migrations/v5.0.0_rename_capacity_column.sql
```

---

## 📋 Upgrade Instructions

### Prerequisites
- Backup your database before upgrading
- Ensure no users are actively using the system
- Have SQLite command-line tools installed

### Step-by-Step Upgrade

1. **Stop the application**
   ```bash
   pm2 stop all
   ```

2. **Backup your database**
   ```bash
   cp backend/storage_insights.db backend/storage_insights.db.backup.$(date +%Y%m%d)
   ```

3. **Download v5.0.0**
   ```bash
   wget https://www.genspark.ai/api/files/s/9ue4IyIY -O webapp-v5.0.0.tar.gz
   tar -xzf webapp-v5.0.0.tar.gz
   ```

4. **Apply database migration**
   ```bash
   cd webapp/backend
   sqlite3 storage_insights.db < ../migrations/v5.0.0_rename_capacity_column.sql
   ```

5. **Install dependencies (if needed)**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

6. **Restart application**
   ```bash
   cd backend
   pm2 start ecosystem.config.cjs
   
   cd ../frontend
   pm2 start ecosystem.config.cjs
   ```

7. **Verify upgrade**
   - Check Overview dashboard shows new chart titles
   - Upload test data to verify FlashSystem preprocessing
   - Check logs for any errors: `pm2 logs`

### Rollback Instructions

If you need to rollback:

1. Stop the application
2. Restore database backup:
   ```bash
   cp backend/storage_insights.db.backup.YYYYMMDD backend/storage_insights.db
   ```
3. Checkout previous version from git
4. Restart application

---

## ⚠️ Breaking Changes

### 1. Database Schema Change
- **Column renamed:** `capacity_gib` → `provisioned_capacity_gib`
- **Impact:** Existing data preserved, but column name changes
- **Action required:** Run migration script before using v5.0.0
- **API impact:** Any custom integrations referencing `capacity_gib` will break

### 2. Chart Title Changes
- **Old titles removed:** "Total Capacity" and "Used Capacity"
- **Impact:** Reports and documentation referencing old titles need updates
- **Action required:** Update any external documentation or reports

### 3. Capacity Calculation Method Changed
- **Old method:** Based on `storage_systems` aggregation
- **New method:** Based on `capacity_volumes` aggregation
- **Impact:** Values may differ slightly from previous versions
- **Note:** New method is more accurate (volume-level granularity)

---

## 🐛 Bug Fixes

- Fixed: FlashSystem volumes with blank available_capacity_gib now calculated automatically
- Fixed: Total Capacity now accurately reflects provisioned volumes (not system-level estimates)
- Fixed: Used Capacity calculation now based on actual volume usage data

---

## 📊 Testing Recommendations

After upgrading, test the following scenarios:

### 1. FlashSystem Data Upload
```
✓ Upload Excel with FlashSystem volumes (A9K-A1, A9KR-R1, A9KR-R2)
✓ Verify available_capacity_gib is calculated for blank fields
✓ Check logs for preprocessing messages
```

### 2. Overview Dashboard
```
✓ Verify "Total Provisioned Capacity" displays correct value
✓ Verify "Used Provisioned Capacity" displays correct value
✓ Compare values with previous version (should be similar but more accurate)
✓ Check that unit switcher (GiB/TiB/PiB) works correctly
```

### 3. API Endpoints
```
✓ GET /api/v1/data/overview/enhanced returns provisioned_capacity_gib
✓ Volume details show provisioned_capacity_gib instead of capacity_gib
✓ All capacity calculations work correctly
```

### 4. Database Integrity
```
✓ Run query: SELECT provisioned_capacity_gib FROM capacity_volumes LIMIT 10
✓ Verify column exists and contains data
✓ Check for any NULL values that shouldn't be NULL
```

---

## 📝 Known Issues

None at this time.

---

## 🔮 Future Enhancements

Planned for future releases:

1. **Physical vs Provisioned Capacity Comparison**
   - Show both provisioned and physical capacity side-by-side
   - Calculate over-provisioning ratio
   - Add trend analysis

2. **Additional Storage System Support**
   - Extend preprocessing logic to other storage system types
   - Auto-detect storage system capabilities
   - Custom preprocessing rules per vendor

3. **Enhanced FlashSystem Analytics**
   - FlashSystem-specific metrics and dashboards
   - Compression ratio analysis
   - Performance correlation with capacity

---

## 💬 Support

If you encounter issues with v5.0.0:

1. Check logs: `pm2 logs` for both backend and frontend
2. Verify migration was applied: `sqlite3 storage_insights.db "PRAGMA table_info(capacity_volumes)"`
3. Review VERSION_v5.0.0.txt for detailed technical information
4. Contact support with error logs and steps to reproduce

---

## 📦 Download

**Direct Download Link:** https://www.genspark.ai/api/files/s/9ue4IyIY

**Package Size:** ~416 MB (compressed)

**Package Contents:**
- Complete source code (backend + frontend)
- Database migration scripts
- Version documentation
- Configuration files
- Documentation updates

**Git Tag:** `v5.0.0`

---

## 🙏 Acknowledgments

This release includes improvements based on:
- User feedback on FlashSystem capacity reporting
- Better alignment with storage industry terminology
- Enhanced accuracy requirements for capacity planning

---

**Previous Version:** v4.2.0  
**Next Version:** TBD

---

*For technical specifications and detailed API documentation, see VERSION_v5.0.0.txt*
