-- Create Tenant-Pool Mappings for Your Environment
-- Based on debug_treemap.py output

-- ============================================================================
-- STEP 1: Create Tenants
-- ============================================================================

INSERT INTO tenants (name, description) VALUES 
  ('ISST', 'Infrastructure & Storage Services Team'),
  ('HST', 'Host Services Team'),
  ('HMC', 'Hardware Management Console'),
  ('AIX', 'AIX Systems'),
  ('Linux', 'Linux Systems'),
  ('BTC', 'Business Technology Center'),
  ('PSP', 'Platform Services'),
  ('NVME', 'NVMe Test Environment'),
  ('Reserve', 'Reserved/Spare Capacity')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- STEP 2: Map Pools to Tenants
-- Based on pool name patterns from your data
-- ============================================================================

-- ISST Tenant (Infrastructure & Storage Services)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'ISST'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE 'ISST%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- HST Tenant (Host Services Team)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'HST'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE 'HST%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- HMC Tenant (Hardware Management Console)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'HMC'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE 'HMC%' OR pool LIKE '%HMC%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- BTC Tenant (Business Technology Center)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'BTC'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE 'BTC%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- PSP Tenant (Platform Services)
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'PSP'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE 'PSP%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- Linux Tenant
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'Linux'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE '%Linux%' OR pool LIKE '%LINUX%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- AIX Tenant
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'AIX'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE '%AIX%' AND pool NOT LIKE 'ISST%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- NVME Test Tenant
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'NVME'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE '%NVME%' OR pool LIKE '%NVMe%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- Reserve Tenant
INSERT INTO tenant_pool_mappings (tenant_id, pool_name, storage_system)
SELECT 
  (SELECT id FROM tenants WHERE name = 'Reserve'),
  pool,
  storage_system_name
FROM capacity_volumes
WHERE pool LIKE '%Reserve%' OR pool LIKE '%reserve%'
GROUP BY pool, storage_system_name
ON CONFLICT DO NOTHING;

-- ============================================================================
-- STEP 3: Verify Mappings
-- ============================================================================

-- Check how many pools are mapped
SELECT 
  t.name as tenant_name,
  COUNT(*) as pool_count
FROM tenant_pool_mappings tpm
JOIN tenants t ON t.id = tpm.tenant_id
GROUP BY t.name
ORDER BY pool_count DESC;

-- Check unmapped pools (will still show as UNKNOWN)
SELECT DISTINCT 
  cv.pool,
  cv.storage_system_name,
  COUNT(*) as volume_count
FROM capacity_volumes cv
LEFT JOIN tenant_pool_mappings tpm 
  ON tpm.pool_name = cv.pool 
  AND tpm.storage_system = cv.storage_system_name
WHERE tpm.id IS NULL
GROUP BY cv.pool, cv.storage_system_name
ORDER BY volume_count DESC
LIMIT 20;

-- ============================================================================
-- NOTES:
-- - Pools like 'mdiskgrp0', 'V7K_R4_Flash', 'FS92K_HA2_REG_20TB' will remain 
--   as UNKNOWN until you manually assign them
-- - You can create additional tenants and mappings based on your org structure
-- ============================================================================
