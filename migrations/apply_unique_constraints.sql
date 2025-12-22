-- Migration: Apply Unique Constraints for Name + Storage System
-- Date: 2025-11-30
-- Purpose: Ensure capacity_disks and inventory_disks have proper unique constraints

-- ===================================================================
-- 1. DROP old constraints if they exist (cleanup)
-- ===================================================================

-- Drop old constraints from previous versions
ALTER TABLE IF EXISTS capacity_disks 
    DROP CONSTRAINT IF EXISTS uq_cap_disk_report_system_pool;

ALTER TABLE IF EXISTS inventory_disks 
    DROP CONSTRAINT IF EXISTS uq_inv_disk_report_name_system;

-- ===================================================================
-- 2. CREATE new unique constraints: Name + Storage System
-- ===================================================================

-- InventoryDisk: Name + Storage System unique constraint
-- Note: NULL names are allowed and won't violate uniqueness (NULL != NULL in SQL)
ALTER TABLE inventory_disks 
    DROP CONSTRAINT IF EXISTS uq_inv_disk_name_system;

ALTER TABLE inventory_disks 
    ADD CONSTRAINT uq_inv_disk_name_system 
    UNIQUE (name, storage_system_name);

-- CapacityDisk: Name + Storage System unique constraint
-- Note: NULL names are allowed and won't violate uniqueness (NULL != NULL in SQL)
ALTER TABLE capacity_disks 
    DROP CONSTRAINT IF EXISTS uq_cap_disk_name_system;

ALTER TABLE capacity_disks 
    ADD CONSTRAINT uq_cap_disk_name_system 
    UNIQUE (name, storage_system_name);

-- ===================================================================
-- 3. VERIFY constraints
-- ===================================================================

-- Show all constraints on capacity_disks
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'capacity_disks'::regclass
ORDER BY conname;

-- Show all constraints on inventory_disks
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'inventory_disks'::regclass
ORDER BY conname;

-- ===================================================================
-- Migration Notes:
-- ===================================================================
-- 
-- UNIQUE CONSTRAINT BEHAVIOR WITH NULL:
-- - PostgreSQL treats NULL != NULL, so multiple rows with NULL names are allowed
-- - Only rows with non-NULL names must be unique per storage system
-- 
-- EXAMPLE VALID DATA:
-- Row 1: (name=NULL, storage_system='V7K-R3')  ✓ Valid
-- Row 2: (name=NULL, storage_system='V7K-R3')  ✓ Valid (NULL names can repeat)
-- Row 3: (name='Disk01', storage_system='V7K-R3')  ✓ Valid
-- Row 4: (name='Disk01', storage_system='V7K-R4')  ✓ Valid (different system)
-- Row 5: (name='Disk01', storage_system='V7K-R3')  ✗ VIOLATES constraint (duplicate)
-- 
-- APPLICATION ON MAC:
-- From: /Users/nileshpandey/Documents/SAN/SAN_DASH_v2
-- 
-- Method 1: Fresh Start (RECOMMENDED - Easiest)
-- $ docker-compose down -v
-- $ docker-compose up -d
-- (This will recreate the database with updated schema automatically)
-- 
-- Method 2: Apply Migration Manually (Keep existing data)
-- $ docker-compose exec db psql -U postgres -d storage_insights -f /docker-entrypoint-initdb.d/migrations/apply_unique_constraints.sql
--
-- Or from Mac terminal:
-- $ docker cp migrations/apply_unique_constraints.sql storage_insights_db:/tmp/
-- $ docker-compose exec db psql -U postgres -d storage_insights -f /tmp/apply_unique_constraints.sql
-- ===================================================================
