#!/usr/bin/env python3
"""
Quick test script to check treemap data structure.
Run this from the backend directory to see what data is being generated.
"""

import sys
from datetime import date
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.utils.processing import get_treemap_data, gib_to_tb
from app.db.models import StoragePool

def test_treemap():
    db = SessionLocal()
    try:
        # Get latest report date
        latest_pool = db.query(StoragePool).order_by(StoragePool.report_date.desc()).first()
        
        if not latest_pool:
            print("❌ No pools found in database")
            return
        
        report_date = latest_pool.report_date
        print(f"📅 Using report date: {report_date}")
        print()
        
        # Get all pools for this date
        all_pools = db.query(StoragePool).filter(
            StoragePool.report_date == report_date
        ).all()
        
        print(f"📊 Total pools in database: {len(all_pools)}")
        
        # Calculate total capacity
        total_capacity_gib = sum(p.usable_capacity_gib or 0 for p in all_pools)
        total_capacity_tb = gib_to_tb(total_capacity_gib)
        print(f"💾 Total capacity: {total_capacity_tb:.2f} TB")
        print()
        
        # Show capacity distribution
        print("📈 Capacity distribution:")
        sorted_pools = sorted(all_pools, key=lambda p: p.usable_capacity_gib or 0, reverse=True)
        for i, pool in enumerate(sorted_pools[:10]):
            cap_tb = gib_to_tb(pool.usable_capacity_gib or 0)
            pct_of_total = (pool.usable_capacity_gib or 0) / total_capacity_gib * 100 if total_capacity_gib > 0 else 0
            print(f"  {i+1}. {pool.name[:30]:30s} - {cap_tb:8.2f} TB ({pct_of_total:5.1f}%)")
        
        if len(sorted_pools) > 10:
            print(f"  ... and {len(sorted_pools) - 10} more pools")
        print()
        
        # Test the treemap function
        print("🔍 Testing get_treemap_data()...")
        treemap_data = get_treemap_data(db, report_date)
        
        print(f"✅ Treemap data generated: {len(treemap_data)} items")
        print()
        
        # Analyze treemap structure
        root_nodes = [d for d in treemap_data if d['storage_system'] == '']
        system_nodes = [d for d in treemap_data if d['storage_system'] == 'All Storage']
        pool_nodes = [d for d in treemap_data if d['storage_system'] != '' and d['storage_system'] != 'All Storage']
        
        print(f"📦 Treemap structure:")
        print(f"  - Root nodes: {len(root_nodes)}")
        print(f"  - System nodes: {len(system_nodes)}")
        print(f"  - Pool nodes: {len(pool_nodes)}")
        print()
        
        if root_nodes:
            print(f"🌳 Root: {root_nodes[0]}")
        
        if system_nodes:
            print(f"\n🖥️  Systems ({len(system_nodes)}):")
            for sys in system_nodes:
                print(f"  - {sys['name']}")
        
        if pool_nodes:
            print(f"\n💿 Sample pools ({min(5, len(pool_nodes))} of {len(pool_nodes)}):")
            for pool in pool_nodes[:5]:
                print(f"  - {pool['name'][:40]:40s} ({pool['storage_system']}) - {pool['capacity_tb']:.2f} TB @ {pool['utilization_pct']:.0f}%")
        
        # Check for issues
        print("\n⚠️  Potential issues:")
        if len(treemap_data) == 0:
            print("  ❌ EMPTY: Treemap data is empty!")
        elif len(pool_nodes) == 0:
            print("  ❌ NO POOLS: All pools were filtered out!")
        elif len(pool_nodes) < len(all_pools) / 2:
            print(f"  ⚠️  HEAVY FILTERING: {len(all_pools) - len(pool_nodes)} pools were aggregated")
        else:
            print("  ✅ Data looks OK")
        
        # Check 1% threshold
        threshold_gib = total_capacity_gib * 0.01
        threshold_tb = gib_to_tb(threshold_gib)
        pools_above_threshold = sum(1 for p in all_pools if (p.usable_capacity_gib or 0) >= threshold_gib)
        print(f"\n📏 1% threshold: {threshold_tb:.2f} TB")
        print(f"  - Pools above threshold: {pools_above_threshold}")
        print(f"  - Pools below threshold: {len(all_pools) - pools_above_threshold}")
        
    finally:
        db.close()

if __name__ == '__main__':
    print("=" * 80)
    print("TREEMAP DATA TEST")
    print("=" * 80)
    print()
    test_treemap()
    print()
    print("=" * 80)
