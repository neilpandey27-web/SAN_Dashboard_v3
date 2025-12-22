-- Migration: Add used_capacity_gib column to capacity_disks table
-- Date: 2025-12-06
-- Description: Add calculated field used_capacity_gib = capacity_gib - available_capacity_gib

-- Add the column
ALTER TABLE capacity_disks 
ADD COLUMN IF NOT EXISTS used_capacity_gib FLOAT NULL;

-- Add comment to document that this is a calculated field
COMMENT ON COLUMN capacity_disks.used_capacity_gib IS 'Calculated field: capacity_gib - available_capacity_gib';

-- Optional: Calculate values for existing records
UPDATE capacity_disks 
SET used_capacity_gib = capacity_gib - available_capacity_gib
WHERE capacity_gib IS NOT NULL 
  AND available_capacity_gib IS NOT NULL;
