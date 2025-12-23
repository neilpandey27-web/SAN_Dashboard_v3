#!/usr/bin/env python3
"""
Debug script to check treemap data structure.
Run this after importing data to see the hierarchy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import CapacityVolume
from datetime import date, datetime
from sqlalchemy import func

db = SessionLocal()

# Get latest report date
latest = db.query(func.max(CapacityVolume.report_date)).scalar()
if not latest:
    print("❌ No data in capacity_volumes table")
    sys.exit(1)

print(f"📅 Latest report date: {latest}")
print()

# Get sample volumes
volumes = db.query(CapacityVolume).filter(
    CapacityVolume.report_date == latest
).limit(10).all()

print("=" * 80)
print("SAMPLE VOLUMES (First 10)")
print("=" * 80)

for i, v in enumerate(volumes, 1):
    print(f"\n{i}. Volume: {v.name}")
    print(f"   Storage System: '{v.storage_system_name}'")
    print(f"   Pool: '{v.pool}'")
    print(f"   Capacity: {v.provisioned_capacity_gib:.2f} GiB")
    print(f"   Used: {v.used_capacity_gib:.2f} GiB" if v.used_capacity_gib else "   Used: None")

# Get unique systems
systems = db.query(CapacityVolume.storage_system_name).filter(
    CapacityVolume.report_date == latest
).distinct().all()

print("\n" + "=" * 80)
print(f"UNIQUE STORAGE SYSTEMS ({len(systems)} total)")
print("=" * 80)
for sys_name in systems:
    pool_count = db.query(CapacityVolume.pool).filter(
        CapacityVolume.report_date == latest,
        CapacityVolume.storage_system_name == sys_name[0]
    ).distinct().count()
    volume_count = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == latest,
        CapacityVolume.storage_system_name == sys_name[0]
    ).count()
    print(f"  • {sys_name[0]}: {pool_count} pools, {volume_count} volumes")

# Get unique pools
pools = db.query(
    CapacityVolume.pool, 
    CapacityVolume.storage_system_name
).filter(
    CapacityVolume.report_date == latest
).distinct().limit(20).all()

print("\n" + "=" * 80)
print(f"SAMPLE POOLS (First 20)")
print("=" * 80)
for pool_name, sys_name in pools:
    volume_count = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == latest,
        CapacityVolume.pool == pool_name,
        CapacityVolume.storage_system_name == sys_name
    ).count()
    print(f"  • Pool: '{pool_name}' on System: '{sys_name}' ({volume_count} volumes)")

# Now test the actual treemap function
print("\n" + "=" * 80)
print("TESTING get_treemap_data() FUNCTION")
print("=" * 80)

from app.utils.processing import get_treemap_data

treemap_data = get_treemap_data(db, latest)

print(f"\n✅ Function returned:")
print(f"   Simple average entries: {len(treemap_data['simple_average'])}")
print(f"   Weighted average entries: {len(treemap_data['weighted_average'])}")

print("\n" + "=" * 80)
print("WEIGHTED AVERAGE HIERARCHY (for treemap)")
print("=" * 80)

# Group by level
root_nodes = [n for n in treemap_data['weighted_average'] if n['storage_system'] == '']
system_nodes = [n for n in treemap_data['weighted_average'] if n['storage_system'] == 'All Storage']
tenant_nodes = [n for n in treemap_data['weighted_average'] if '|' in n['name'] and n['storage_system'] != 'All Storage']
pool_nodes = [n for n in treemap_data['weighted_average'] if '|' not in n['name'] and n['storage_system'] != '' and n['storage_system'] != 'All Storage']

print(f"\n📊 Node counts by level:")
print(f"   Root (All Storage): {len(root_nodes)}")
print(f"   Systems: {len(system_nodes)}")
print(f"   Tenants: {len(tenant_nodes)}")
print(f"   Pools: {len(pool_nodes)}")

if root_nodes:
    print(f"\n🌳 Root Node:")
    for node in root_nodes:
        print(f"   • {node['name']}")
        print(f"     Parent: '{node['storage_system']}'")
        print(f"     Capacity: {node['total_capacity_gib']:.2f} GiB")

if system_nodes:
    print(f"\n🏢 System Nodes:")
    for node in system_nodes[:5]:
        print(f"   • {node['name']}")
        print(f"     Parent: '{node['storage_system']}'")
        print(f"     Capacity: {node['total_capacity_gib']:.2f} GiB")

if tenant_nodes:
    print(f"\n👥 Tenant Nodes (first 10):")
    for node in tenant_nodes[:10]:
        print(f"   • {node['name']}")
        print(f"     Parent: '{node['storage_system']}'")
        print(f"     Capacity: {node['total_capacity_gib']:.2f} GiB")
        print(f"     Pools: {node.get('pool_count', '?')}")

if pool_nodes:
    print(f"\n💾 Pool Nodes (first 10):")
    for node in pool_nodes[:10]:
        print(f"   • {node['name']}")
        print(f"     Parent: '{node['storage_system']}'")
        print(f"     Capacity: {node['total_capacity_gib']:.2f} GiB")

db.close()

print("\n" + "=" * 80)
print("✅ Debug complete!")
print("=" * 80)
