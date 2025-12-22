-- Migration v5.0.0: Rename capacity_gib to provisioned_capacity_gib in capacity_volumes table
-- This migration renames the column to better reflect that it represents provisioned (not physical) capacity

-- Rename the column
ALTER TABLE capacity_volumes RENAME COLUMN capacity_gib TO provisioned_capacity_gib;

-- Note: SQLite doesn't support renaming columns directly in older versions
-- If this fails, you may need to recreate the table or use a different approach
-- The model has been updated to use provisioned_capacity_gib
