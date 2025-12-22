"""
Data management API endpoints: upload, overview, systems, historical.
"""
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import (
    User, StorageSystem, StoragePool, CapacityVolume,
    CapacityHost, CapacityDisk, Department,
    Alert, UploadLog, UserActivityLog,
    TenantPoolMapping, Tenant, UserTenant, HostTenantMapping, MdiskSystemMapping
)
from app.db.schemas import (
    UploadResponse, OverviewData, KPIData, AlertSummary,
    StorageSystemOut, StorageSystemListItem, HistoricalQuery
)
from app.core.security import get_current_user, get_current_admin_user, get_user_tenant_ids
from app.core.config import settings
from app.utils.processing import (
    validate_excel_file, process_dataframe, calculate_pool_utilization,
    calculate_disk_used_capacity, clean_column_name,
    insert_data_with_duplicate_check,
    generate_alerts_from_pools, get_overview_kpis, get_top_systems_by_usage,
    get_utilization_distribution, get_forecasting_data, get_storage_types_distribution,
    get_treemap_data, gib_to_tb, calculate_utilization_pct, calculate_days_until_full,
    SHEET_MODEL_MAP
)
# v6.1.0: Import tenant filtering utilities
from app.utils.tenant_filter import get_tenant_pool_names, get_tenant_host_names, get_tenant_system_names

router = APIRouter(prefix="/data", tags=["Data Management"])


# ============================================================================
# Data Upload (Admin Only)
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_excel(
        file: UploadFile = File(...),
        report_date: Optional[date] = Query(None, description="Report date (defaults to today)"),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Upload Excel file with storage data.
    Expects 8 sheets: Storage_Systems, Storage_Pools, Capacity_Volumes,
    Inventory_Hosts, Capacity_Hosts, Inventory_Disks, Capacity_Disks, Departments.
    Admin only.
    """
    # Validate file extension
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    # Read file content
    content = await file.read()

    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
        )

    # Validate Excel structure
    is_valid, errors, dataframes = validate_excel_file(content)

    # Extract report_date from Excel file if not provided
    if not report_date:
        # Try to get report_date from first sheet with data
        for sheet_name in ['Storage_Systems', 'Storage_Pools', 'Capacity_Volumes', 'Capacity_Hosts', 'Capacity_Disks',
                           'Departments']:
            if sheet_name in dataframes and len(dataframes[sheet_name]) > 0:
                df = dataframes[sheet_name]
                # Clean column names to find report_date
                df_temp = df.copy()
                df_temp.columns = [clean_column_name(col) for col in df_temp.columns]
                if 'report_date' in df_temp.columns:
                    # Get the first non-null report_date value
                    first_date = df_temp['report_date'].dropna().iloc[0] if len(
                        df_temp['report_date'].dropna()) > 0 else None
                    if first_date:
                        from app.utils.processing import clean_datetime_value
                        report_date = clean_datetime_value(first_date)
                        break

        # If still no report_date found, use today as fallback
        if not report_date:
            report_date = date.today()

    if not is_valid:
        # Log failed upload
        upload_log = UploadLog(
            file_name=file.filename,
            user_id=current_user.id,
            rows_added=0,
            duplicates_skipped=0,
            errors="; ".join(errors),
            status="failed"
        )
        db.add(upload_log)
        db.commit()

        return UploadResponse(
            success=False,
            message="Excel validation failed",
            errors=errors
        )

    import time
    import json

    upload_start_time = time.time()

    total_rows_added = 0
    total_duplicates = 0
    processing_errors = []
    sheets_processed = []
    all_skipped_records = []

    # Define unique keys for each model
    unique_keys_map = {
        'Storage_Systems': ['report_date', 'name'],
        'Storage_Pools': ['report_date', 'name', 'storage_system_name'],
        'Capacity_Volumes': ['report_date', 'volume_name', 'storage_system_name', 'pool_name'],
        'Inventory_Hosts': ['report_date', 'name'],
        'Capacity_Hosts': ['report_date', 'name'],
        'Inventory_Disks': ['report_date', 'name', 'storage_system_name'],
        'Capacity_Disks': ['report_date', 'name', 'storage_system_name', 'pool'],
        'Departments': ['report_date', 'name'],
    }

    # Process Storage_Systems first (to get IDs for foreign keys)
    system_id_map = {}

    # Create upload log entry first to get upload_id
    temp_upload_log = UploadLog(
        file_name=file.filename,
        user_id=current_user.id,
        rows_added=0,
        duplicates_skipped=0,
        status="processing"
    )
    db.add(temp_upload_log)
    db.flush()  # Get the ID without committing
    upload_log_id = temp_upload_log.id

    try:
        # Process each sheet
        sheet_stats = {}  # Track statistics for each sheet

        for sheet_name in ['Storage_Systems', 'Storage_Pools', 'Capacity_Volumes',
                           'Inventory_Hosts', 'Capacity_Hosts', 'Inventory_Disks',
                           'Capacity_Disks', 'Departments']:

            if sheet_name not in dataframes:
                continue

            df = dataframes[sheet_name]
            model_class = SHEET_MODEL_MAP[sheet_name]

            # Track original row count
            original_rows = len(df)

            # Process dataframe
            df = process_dataframe(df, model_class, report_date)

            # Special handling for pools - calculate utilization and used capacity
            if sheet_name == 'Storage_Pools':
                df = calculate_pool_utilization(df)

            # Special handling for capacity disks - calculate used capacity
            if sheet_name == 'Capacity_Disks':
                df = calculate_disk_used_capacity(df)

            # Special handling for capacity volumes - calculate available capacity for FlashSystems
            if sheet_name == 'Capacity_Volumes':
                from app.utils.processing import calculate_flashsystem_available_capacity, calculate_overhead_used_capacity
                df = calculate_flashsystem_available_capacity(df)
                df = calculate_overhead_used_capacity(df)

            # Convert to records
            records = df.to_dict('records')

            # Add upload_id to all records
            for record in records:
                record['upload_id'] = upload_log_id

            # Handle foreign key lookups for pools, volumes, disks
            if sheet_name in ['Storage_Pools', 'Capacity_Volumes', 'Inventory_Disks', 'Capacity_Disks']:
                # First, ensure we have the system_id_map built from Storage_Systems
                if 'Storage_Systems' in sheets_processed:
                    db.flush()  # Ensure Storage_Systems are committed
                    systems = db.query(StorageSystem).filter(
                        StorageSystem.report_date == report_date
                    ).all()
                    system_id_map = {s.name: s.id for s in systems}
                else:
                    system_id_map = {}

                for record in records:
                    system_name = record.get('storage_system_name')
                    if system_name:
                        # Look up system ID from map
                        if system_name in system_id_map:
                            record['storage_system_id'] = system_id_map[system_name]
                        else:
                            # Try direct query as fallback
                            system = db.query(StorageSystem).filter(
                                StorageSystem.report_date == report_date,
                                StorageSystem.name == system_name
                            ).first()
                            if system:
                                record['storage_system_id'] = system.id
                                system_id_map[system_name] = system.id  # Add to map
                            else:
                                # Skip this record if system doesn't exist
                                print(
                                    f"Warning: Storage system '{system_name}' not found for {sheet_name} record. Skipping.")
                                record['storage_system_id'] = None  # Will be filtered out

            # Filter out records with invalid foreign keys and capture filtered records
            filtered_count = 0
            filtered_records = []
            if sheet_name in ['Storage_Pools', 'Capacity_Volumes', 'Inventory_Disks', 'Capacity_Disks']:
                valid_records = []
                for record in records:
                    if record.get('storage_system_id') is not None:
                        valid_records.append(record)
                    else:
                        # Capture filtered record with full row data
                        storage_system_name = record.get('storage_system_name', 'Unknown')
                        identifier = record.get('volume_name') or record.get('name')
                        if not identifier:
                            identifier = f"{storage_system_name}/{record.get('pool_name') or record.get('pool', 'Unknown')}"

                        # Remove storage_system_id from the record for display (it's None anyway)
                        display_record = {k: v for k, v in record.items() if k != 'storage_system_id'}

                        filtered_records.append({
                            'table': sheet_name,
                            'reason': f'missing_storage_system: {storage_system_name}',
                            'identifier': identifier,
                            'full_row': display_record
                        })

                filtered_count = len(records) - len(valid_records)
                if filtered_count > 0:
                    print(f"⚠️  {sheet_name}: Filtered {filtered_count} records (missing storage system references)")
                records = valid_records

            # Insert with duplicate check
            unique_keys = unique_keys_map.get(sheet_name, ['report_date', 'name'])
            rows_added, duplicates, skipped = insert_data_with_duplicate_check(
                db, model_class, records, unique_keys
            )

            # Track statistics
            sheet_stats[sheet_name] = {
                'original': original_rows,
                'after_processing': len(df),
                'filtered': filtered_count,
                'filtered_records': filtered_records,  # Full row data for filtered records
                'added': rows_added,
                'duplicates': duplicates,
                'skipped': len(skipped)
            }

            print(
                f"📊 {sheet_name}: {original_rows} rows → {len(df)} after processing → {filtered_count} filtered → {rows_added} added, {duplicates} duplicates")

            total_rows_added += rows_added
            total_duplicates += duplicates
            all_skipped_records.extend(skipped)
            sheets_processed.append(sheet_name)

        # Parse volume-host mappings
        if 'Capacity_Volumes' in dataframes:
            volumes_df = process_dataframe(
                dataframes['Capacity_Volumes'],
                CapacityVolume,
                report_date
            )

        # Generate alerts for pools exceeding thresholds
        alerts = generate_alerts_from_pools(db, report_date)
        for alert in alerts:
            # Check if similar alert already exists (unacknowledged)
            existing_alert = db.query(Alert).filter(
                Alert.pool_name == alert.pool_name,
                Alert.storage_system == alert.storage_system,
                Alert.acknowledged == False
            ).first()

            if not existing_alert:
                db.add(alert)

        db.commit()

        upload_duration = time.time() - upload_start_time

        # Print detailed statistics summary
        print("\n" + "=" * 80)
        print("📈 UPLOAD STATISTICS SUMMARY")
        print("=" * 80)
        total_original = sum(s['original'] for s in sheet_stats.values())
        total_filtered = sum(s['filtered'] for s in sheet_stats.values())
        total_skipped = sum(s['skipped'] for s in sheet_stats.values())

        for sheet, stats in sheet_stats.items():
            loss = stats['original'] - stats['added']
            if loss > 0:
                print(f"  {sheet}:")
                print(f"    Original: {stats['original']} → Added: {stats['added']} (Lost: {loss})")
                if stats['filtered'] > 0:
                    print(f"    ├─ Filtered (missing storage system): {stats['filtered']}")
                if stats['duplicates'] > 0:
                    print(f"    ├─ Duplicates: {stats['duplicates']}")
                if stats['skipped'] > 0:
                    print(f"    └─ Skipped (other reasons): {stats['skipped']}")

        print(f"\n  TOTALS:")
        print(f"    Total rows in Excel: {total_original}")
        print(f"    Filtered (missing storage system): {total_filtered}")
        print(f"    Duplicates: {total_duplicates}")
        print(f"    Skipped (other reasons): {total_skipped}")
        print(f"    Successfully added: {total_rows_added}")
        print(f"    Total lost: {total_original - total_rows_added}")
        print("=" * 80 + "\n")

        # Format skipped records for logging
        skipped_details = ""
        if all_skipped_records:
            skipped_by_table = {}
            for skip in all_skipped_records:
                table = skip['table']
                if table not in skipped_by_table:
                    skipped_by_table[table] = []
                skipped_by_table[table].append(
                    f"{skip['identifier']} ({skip['reason']})"
                )

            for table, skips in skipped_by_table.items():
                skipped_details += f"\n{table}: {', '.join(skips[:20])}"  # Limit to first 20
                if len(skips) > 20:
                    skipped_details += f" ... and {len(skips) - 20} more"

        # Convert datetime objects to strings for JSON serialization
        skipped_records_json = json.dumps(all_skipped_records, default=str) if all_skipped_records else None

        # Prepare statistics for storage
        upload_statistics = {
            'total_original': total_original,
            'total_filtered': total_filtered,
            'total_duplicates': total_duplicates,
            'total_skipped': total_skipped,
            'total_added': total_rows_added,
            'total_lost': total_original - total_rows_added,
            'sheets': {}
        }

        # Add per-sheet statistics
        for sheet, stats in sheet_stats.items():
            loss = stats['original'] - stats['added']
            if loss > 0 or stats['original'] > 0:  # Include all sheets with data
                upload_statistics['sheets'][sheet] = {
                    'original': stats['original'],
                    'after_processing': stats['after_processing'],
                    'filtered': stats['filtered'],
                    'filtered_records': stats.get('filtered_records', []),  # Full row data for filtered records
                    'duplicates': stats['duplicates'],
                    'skipped': stats['skipped'],
                    'added': stats['added'],
                    'lost': loss
                }

        upload_statistics_json = json.dumps(upload_statistics, default=str)

        # Update the upload log with final results
        temp_upload_log.rows_added = total_rows_added
        temp_upload_log.duplicates_skipped = total_duplicates
        temp_upload_log.errors = ("; ".join(processing_errors) if processing_errors else "") + skipped_details
        temp_upload_log.status = "success" if not processing_errors else "partial"
        temp_upload_log.upload_duration_seconds = round(upload_duration, 2)
        temp_upload_log.skipped_records_json = skipped_records_json
        temp_upload_log.upload_statistics_json = upload_statistics_json

        # Log activity
        activity = UserActivityLog(
            user_id=current_user.id,
            action="data_upload",
            details=f"Uploaded {file.filename}: {total_rows_added} rows added, {total_duplicates} duplicates skipped{skipped_details}"
        )
        db.add(activity)
        db.commit()

        return UploadResponse(
            success=True,
            message=f"Upload successful. {total_rows_added} rows added, {total_duplicates} duplicates skipped.",
            rows_added=total_rows_added,
            duplicates_skipped=total_duplicates,
            errors=processing_errors,
            sheets_processed=sheets_processed
        )

    except Exception as e:
        db.rollback()

        # Log failed upload
        upload_log = UploadLog(
            file_name=file.filename,
            user_id=current_user.id,
            rows_added=0,
            duplicates_skipped=0,
            errors=str(e),
            status="failed"
        )
        db.add(upload_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing upload: {str(e)}"
        )


@router.delete("/upload/{upload_id}")
async def delete_upload_data(
        upload_id: int,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Delete all data associated with a specific upload.
    Admin only.
    """
    # Verify upload exists
    upload_log = db.query(UploadLog).filter(UploadLog.id == upload_id).first()
    if not upload_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )

    try:
        # Delete data from all tables with this upload_id
        # IMPORTANT: Delete in reverse dependency order (children first, parents last)
        # to avoid foreign key constraint violations
        tables_to_clean = [
            # Child tables (have FK to storage_systems)
            Department,
            CapacityDisk,
            CapacityHost,
            CapacityVolume,
            StoragePool,
            # Parent table (referenced by others) - delete last
            StorageSystem,
        ]

        total_deleted = 0
        for model_class in tables_to_clean:
            deleted = db.query(model_class).filter(
                model_class.upload_id == upload_id
            ).delete(synchronize_session=False)
            total_deleted += deleted

        # Update upload log status
        upload_log.status = "deleted"

        # Log activity
        activity = UserActivityLog(
            user_id=current_user.id,
            action="data_deletion",
            details=f"Deleted data from upload_id {upload_id} ({upload_log.file_name}): {total_deleted} records removed"
        )
        db.add(activity)

        db.commit()

        return {
            "success": True,
            "message": f"Successfully deleted {total_deleted} records from upload '{upload_log.file_name}'",
            "records_deleted": total_deleted,
            "upload_id": upload_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting data: {str(e)}"
        )


# ============================================================================
# Overview Dashboard Data
# ============================================================================

@router.get("/overview")
async def get_overview_data(
        report_date: Optional[date] = Query(None, description="Report date (defaults to latest)"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get overview dashboard data.
    Filtered by user's tenant assignments.
    """
    # Get latest report date if not specified
    if not report_date:
        latest = db.query(func.max(StorageSystem.report_date)).scalar()
        if not latest:
            return {
                "kpis": None,
                "alerts": None,
                "message": "No data available"
            }
        report_date = latest

    # Get tenant IDs for filtering (admins see all)
    tenant_ids = None
    if current_user.role != "admin":
        tenant_ids = get_user_tenant_ids(current_user)

    # Get KPIs
    kpis = get_overview_kpis(db, report_date, tenant_ids)

    # Get alerts summary
    alert_query = db.query(Alert).filter(Alert.acknowledged == False)

    # Filter alerts by tenant pool mappings for non-admins
    if tenant_ids:
        pool_names = db.query(TenantPoolMapping.pool_name).filter(
            TenantPoolMapping.tenant_id.in_(tenant_ids)
        ).all()
        pool_names = [p[0] for p in pool_names]
        if pool_names:
            alert_query = alert_query.filter(Alert.pool_name.in_(pool_names))

    alerts = alert_query.all()

    critical_alerts = [a for a in alerts if a.level in ('critical', 'emergency')]
    warning_alerts = [a for a in alerts if a.level == 'warning']

    alerts_summary = {
        "critical_count": len(critical_alerts),
        "warning_count": len(warning_alerts),
        "critical_pools": [
            {
                "name": a.pool_name,
                "system": a.storage_system,
                "utilization_pct": a.utilization_pct,
                "days_until_full": a.days_until_full
            }
            for a in critical_alerts[:5]
        ],
        "warning_pools": [
            {
                "name": a.pool_name,
                "system": a.storage_system,
                "utilization_pct": a.utilization_pct,
                "days_until_full": a.days_until_full
            }
            for a in warning_alerts[:5]
        ]
    }

    # Get chart data
    top_systems = get_top_systems_by_usage(db, report_date, limit=10)
    utilization_dist = get_utilization_distribution(db, report_date)
    forecasting = get_forecasting_data(db, report_date, limit=10)
    storage_types = get_storage_types_distribution(db, report_date)
    treemap = get_treemap_data(db, report_date)

    # Get top hosts by capacity
    hosts = db.query(CapacityHost).filter(
        CapacityHost.report_date == report_date
    ).order_by(CapacityHost.san_capacity_gib.desc()).limit(10).all()

    top_hosts = [
        {
            "name": h.name,
            "capacity_tb": gib_to_tb(h.san_capacity_gib or 0),
            "used_tb": gib_to_tb(h.used_san_capacity_gib or 0)
        }
        for h in hosts
    ]

    # Calculate savings from compression
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()

    savings_data = [
        {
            "name": s.name,
            "savings_tb": gib_to_tb(s.data_reduction_gib or 0),
            "compression_ratio": s.total_compression_ratio or 1.0
        }
        for s in systems if s.data_reduction_gib and s.data_reduction_gib > 0
    ][:10]

    # Generate recommendations
    recommendations = []

    # High utilization recommendation
    high_util_pools = db.query(StoragePool).filter(
        StoragePool.report_date == report_date,
        StoragePool.utilization_pct > 85
    ).count()

    if high_util_pools > 0:
        recommendations.append({
            "type": "warning",
            "title": "High Utilization Pools",
            "message": f"{high_util_pools} pools are above 85% utilization. Consider capacity expansion.",
            "priority": "high"
        })

    # Low compression recommendation
    low_compression = [s for s in systems if s.total_compression_ratio and s.total_compression_ratio < 1.5]
    if low_compression:
        recommendations.append({
            "type": "info",
            "title": "Compression Opportunity",
            "message": f"{len(low_compression)} systems have low compression ratios. Review data deduplication settings.",
            "priority": "medium"
        })

    # Capacity planning recommendation
    critical_count = len(critical_alerts)
    if critical_count > 0:
        recommendations.append({
            "type": "critical",
            "title": "Immediate Action Required",
            "message": f"{critical_count} pools are at critical capacity levels and may fill within days.",
            "priority": "critical"
        })

    return {
        "kpis": kpis,
        "alerts": alerts_summary,
        "top_systems": top_systems,
        "utilization_distribution": utilization_dist,
        "forecasting_data": forecasting,
        "storage_types": storage_types,
        "top_hosts": top_hosts,
        "savings_data": savings_data,
        "treemap_data": treemap,
        "recommendations": recommendations,
        "report_date": report_date.isoformat()
    }


@router.get("/overview/enhanced")
async def get_overview_enhanced_alias(
        report_date: Optional[date] = Query(None, description="Report date (defaults to latest)"),
        tenant: Optional[str] = Query(None, description="Filter by tenant name (admin only)"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Enhanced overview endpoint (alias for /dashboard/overview-enhanced).
    Returns treemap data, KPIs, alerts, forecasting, and all dashboard visualizations.
    """
    return await get_enhanced_overview(report_date, tenant, current_user, db)


# ============================================================================
# Storage Systems
# ============================================================================

@router.get("/systems")
async def get_storage_systems(
        report_date: Optional[date] = Query(None),
        search: Optional[str] = Query(None),
        sort_by: str = Query("name"),
        sort_order: str = Query("asc"),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get list of storage systems with pagination and filtering."""
    # Get latest report date if not specified
    if not report_date:
        latest = db.query(func.max(StorageSystem.report_date)).scalar()
        if not latest:
            return {"items": [], "total": 0, "page": 1, "page_size": page_size}
        report_date = latest

    # Build query
    query = db.query(StorageSystem).filter(StorageSystem.report_date == report_date)

    # Apply search filter
    if search:
        query = query.filter(
            StorageSystem.name.ilike(f"%{search}%") |
            StorageSystem.type.ilike(f"%{search}%") |
            StorageSystem.model.ilike(f"%{search}%") |
            StorageSystem.location.ilike(f"%{search}%")
        )

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(StorageSystem, sort_by, StorageSystem.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    systems = query.offset(offset).limit(page_size).all()

    # Build response
    items = []
    for s in systems:
        total_cap = s.usable_capacity_gib or 0
        available = s.available_capacity_gib or 0
        used = total_cap - available
        util_pct = calculate_utilization_pct(used, total_cap)

        items.append({
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "model": s.model,
            "vendor": s.vendor,
            "capacity_tb": round(gib_to_tb(total_cap), 2),
            "used_tb": round(gib_to_tb(used), 2),
            "available_tb": round(gib_to_tb(available), 2),
            "utilization_pct": util_pct,
            "pools": s.pools or 0,
            "volumes": s.volumes or 0,
            "location": s.location,
            "ip_address": s.ip_address,
            "compression_ratio": s.total_compression_ratio,
            "last_probe": s.last_successful_probe.isoformat() if s.last_successful_probe else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/systems/{system_id}")
async def get_system_detail(
        system_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get detailed information about a storage system (admin drill-down)."""
    system = db.query(StorageSystem).filter(StorageSystem.id == system_id).first()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage system not found"
        )

    # Get associated pools
    pools = db.query(StoragePool).filter(
        StoragePool.storage_system_id == system_id
    ).all()

    pool_data = [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "parent_name": p.parent_name,
            "usable_capacity_tb": gib_to_tb(p.usable_capacity_gib or 0),
            "used_capacity_tb": gib_to_tb(p.used_capacity_gib or 0),
            "available_capacity_tb": gib_to_tb(p.available_capacity_gib or 0),
            "utilization_pct": p.utilization_pct,
            "volumes": p.volumes,
            "raid_level": p.raid_level
        }
        for p in pools
    ]

    # Get volumes count by pool
    volumes_by_pool = db.query(
        CapacityVolume.pool_name,
        func.count(CapacityVolume.id).label('count')
    ).filter(
        CapacityVolume.storage_system_id == system_id
    ).group_by(CapacityVolume.pool_name).all()

    # Build response
    total_cap = system.usable_capacity_gib or 0
    available = system.available_capacity_gib or 0
    used = total_cap - available

    return {
        "system": {
            "id": system.id,
            "name": system.name,
            "type": system.type,
            "model": system.model,
            "vendor": system.vendor,
            "serial_number": system.serial_number,
            "firmware": system.firmware,
            "location": system.location,
            "ip_address": system.ip_address,
            "capacity_tb": gib_to_tb(total_cap),
            "used_tb": gib_to_tb(used),
            "available_tb": gib_to_tb(available),
            "utilization_pct": calculate_utilization_pct(used, total_cap),
            "compression_ratio": system.total_compression_ratio,
            "data_reduction_tb": gib_to_tb(system.data_reduction_gib or 0),
            "pools_count": system.pools,
            "volumes_count": system.volumes,
            "managed_disks": system.managed_disks,
            "last_probe": system.last_successful_probe
        },
        "pools": pool_data,
        "volumes_by_pool": dict(volumes_by_pool)
    }


@router.get("/systems/{system_name}/disks")
async def get_system_disks(
        system_name: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all disks for a specific storage system."""
    disks = db.query(CapacityDisk).filter(
        CapacityDisk.storage_system_name == system_name
    ).order_by(CapacityDisk.pool, CapacityDisk.name).all()

    if not disks:
        return {"disks": [], "total": 0}

    disk_data = [
        {
            "id": d.id,
            "name": d.name,
            "pool": d.pool,
            "status": d.status,
            "mode": d.mode,
            "disk_class": d.disk_class,
            "raid_level": d.raid_level,
            "capacity_gib": d.capacity_gib,
            "available_capacity_gib": d.available_capacity_gib,
            "capacity_tb": gib_to_tb(d.capacity_gib or 0),
            "available_tb": gib_to_tb(d.available_capacity_gib or 0),
            "used_tb": gib_to_tb((d.capacity_gib or 0) - (d.available_capacity_gib or 0)),
            "utilization_pct": calculate_utilization_pct((d.capacity_gib or 0) - (d.available_capacity_gib or 0),
                                                         d.capacity_gib or 0),
            "volumes": d.volumes,
            "easy_tier": d.easy_tier,
            "drive_compression_ratio": d.drive_compression_ratio
        }
        for d in disks
    ]

    return {"disks": disk_data, "total": len(disk_data)}


@router.get("/systems/{system_name}/pools")
async def get_system_pools(
        system_name: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all pools for a specific storage system with aggregated volume counts."""
    pools = db.query(StoragePool).filter(
        StoragePool.storage_system_name == system_name
    ).order_by(StoragePool.name).all()

    if not pools:
        return {"pools": [], "total": 0}

    pool_data = []
    for p in pools:
        # Count volumes for this pool
        volume_count = db.query(func.count(CapacityVolume.id)).filter(
            CapacityVolume.pool_name == p.name,
            CapacityVolume.storage_system_name == system_name
        ).scalar() or 0

        pool_data.append({
            "id": p.id,
            "name": p.name,
            "storage_system_name": p.storage_system_name,
            "status": p.status,
            "parent_name": p.parent_name,
            "capacity_tb": round(gib_to_tb(p.usable_capacity_gib or 0), 2),
            "used_tb": round(gib_to_tb(p.used_capacity_gib or 0), 2),
            "available_tb": round(gib_to_tb(p.available_capacity_gib or 0), 2),
            "utilization_pct": p.utilization_pct,
            "volumes": volume_count,
            "drives": p.drives,
            "raid_level": p.raid_level,
            "pool_compression_ratio": p.pool_compression_ratio
        })

    return {"pools": pool_data, "total": len(pool_data)}


@router.get("/pools/{pool_name}/details")
async def get_pool_details(
        pool_name: str,
        storage_system_name: str = Query(..., description="Storage system name"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get detailed information about a specific pool."""
    pool = db.query(StoragePool).filter(
        StoragePool.name == pool_name,
        StoragePool.storage_system_name == storage_system_name
    ).first()

    if not pool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pool '{pool_name}' not found for system '{storage_system_name}'"
        )

    # Get disks in this pool
    disks = db.query(CapacityDisk).filter(
        CapacityDisk.pool == pool_name,
        CapacityDisk.storage_system_name == storage_system_name
    ).all()

    disk_count = len(disks)
    total_disk_capacity = sum((d.capacity_gib or 0) for d in disks)

    return {
        "pool": {
            "id": pool.id,
            "name": pool.name,
            "storage_system_name": pool.storage_system_name,
            "status": pool.status,
            "parent_name": pool.parent_name,
            "usable_capacity_tb": gib_to_tb(pool.usable_capacity_gib or 0),
            "used_capacity_tb": gib_to_tb(pool.used_capacity_gib or 0),
            "available_capacity_tb": gib_to_tb(pool.available_capacity_gib or 0),
            "utilization_pct": pool.utilization_pct,
            "volumes": pool.volumes,
            "drives": pool.drives,
            "raid_level": pool.raid_level,
            "pool_compression_ratio": pool.pool_compression_ratio,
            "total_compression_ratio": pool.total_compression_ratio,
            "recent_growth_tb": gib_to_tb(pool.recent_growth_gib or 0),
            "recent_fill_rate_pct": pool.recent_fill_rate_pct,
            "mapped_capacity_tb": gib_to_tb(pool.mapped_capacity_gib or 0),
            "unmapped_capacity_tb": gib_to_tb(pool.unmapped_capacity_gib or 0)
        },
        "disk_summary": {
            "total_disks": disk_count,
            "total_disk_capacity_tb": gib_to_tb(total_disk_capacity)
        }
    }


@router.get("/pools/{pool_name}/volumes")
async def get_pool_volumes(
        pool_name: str,
        storage_system_name: str = Query(..., description="Storage system name"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all volumes in a specific pool."""
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.pool_name == pool_name,
        CapacityVolume.storage_system_name == storage_system_name
    ).order_by(CapacityVolume.volume_name).all()

    volume_data = [
        {
            "id": v.id,
            "name": v.volume_name,
            "volser": v.volser,
            "storage_virtual_machine": v.storage_virtual_machine,
            "status": v.status,
            "copy_id": v.copy_id,
            "volume_id": v.volume_id,
            "capacity_tb": gib_to_tb(v.provisioned_capacity_gib or 0),
            "used_capacity_tb": gib_to_tb(v.used_capacity_gib or 0),
            "available_capacity_tb": gib_to_tb(v.available_capacity_gib or 0),
            "used_capacity_pct": v.used_capacity_pct,
            "thin_provisioned": v.thin_provisioned,
            "mirrored": v.mirrored,
            "data_reduction_enabled": v.data_reduction_enabled,
            "hosts": v.hosts
        }
        for v in volumes
    ]

    return {"volumes": volume_data, "total": len(volume_data)}


@router.get("/volumes/{volume_name}/hosts")
async def get_volume_hosts(
        volume_name: str,
        storage_system_name: str = Query(..., description="Storage system name"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all hosts connected to a specific volume."""
    volume = db.query(CapacityVolume).filter(
        CapacityVolume.volume_name == volume_name,
        CapacityVolume.storage_system_name == storage_system_name
    ).first()

    if not volume or not volume.hosts:
        return {"hosts": [], "total": 0}

    # Parse host names from comma-separated string
    host_names = [h.strip() for h in volume.hosts.split(',') if h.strip()]

    # Get host details
    hosts = db.query(CapacityHost).filter(
        CapacityHost.name.in_(host_names)
    ).all()

    host_data = [
        {
            "id": h.id,
            "name": h.name,
            "condition": h.condition,
            "data_collection": h.data_collection,
            "probe_status": h.probe_status,
            "performance_monitor_status": h.performance_monitor_status,
            "os_type": h.os_type,
            "san_capacity_tb": gib_to_tb(h.san_capacity_gib or 0),
            "used_san_capacity_tb": gib_to_tb(h.used_san_capacity_gib or 0),
            "location": h.location,
            "primary_provisioned_capacity_tb": gib_to_tb(h.primary_provisioned_capacity_gib or 0),
            "primary_used_capacity_tb": gib_to_tb(h.primary_used_capacity_gib or 0),
            "last_successful_probe": h.last_successful_probe,
            "last_successful_monitor": h.last_successful_monitor
        }
        for h in hosts
    ]

    return {"hosts": host_data, "total": len(host_data),
            "volume_info": {"name": volume.volume_name, "capacity_tb": gib_to_tb(volume.provisioned_capacity_gib or 0)}}


# ============================================================================
# Historical Data
# ============================================================================

@router.get("/historical")
async def get_historical_data(
        start_date: date = Query(...),
        end_date: date = Query(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get historical trend data for date range."""
    # Get systems data grouped by report date
    systems_by_date = db.query(
        StorageSystem.report_date,
        func.sum(StorageSystem.usable_capacity_gib).label('total_capacity'),
        func.sum(StorageSystem.available_capacity_gib).label('available_capacity')
    ).filter(
        StorageSystem.report_date >= start_date,
        StorageSystem.report_date <= end_date
    ).group_by(StorageSystem.report_date).order_by(StorageSystem.report_date).all()

    trend_data = []
    for row in systems_by_date:
        total = row.total_capacity or 0
        available = row.available_capacity or 0
        used = total - available

        trend_data.append({
            "date": row.report_date.isoformat(),
            "total_capacity_tb": gib_to_tb(total),
            "used_capacity_tb": gib_to_tb(used),
            "available_capacity_tb": gib_to_tb(available),
            "utilization_pct": calculate_utilization_pct(used, total)
        })

    return {
        "trend_data": trend_data,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }


@router.get("/report-dates")
async def get_available_report_dates(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get list of available report dates."""
    dates = db.query(StorageSystem.report_date).distinct().order_by(
        StorageSystem.report_date.desc()
    ).all()

    return [d[0].isoformat() for d in dates]


# ============================================================================
# Enhanced Dashboard Endpoints (for v1.4.4 Overview Replacement)
# ============================================================================

@router.get("/dashboard/overview-enhanced")
async def get_enhanced_overview(
        report_date: Optional[date] = Query(None, description="Report date (defaults to latest)"),
        tenant: Optional[str] = Query(None, description="Filter by tenant name (admin only)"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Enhanced overview dashboard data with all visualizations.
    Includes: KPIs, alerts, forecasting, treemap, recommendations, savings analysis.
    v6.1.0: Now supports tenant filtering for admin users.
    """
    # Get latest report date if not specified
    if not report_date:
        latest = db.query(func.max(StorageSystem.report_date)).scalar()
        if not latest:
            return {
                "error": "No data available",
                "message": "Please upload Excel data first"
            }
        report_date = latest

    # Get all storage systems
    systems = db.query(StorageSystem).filter(
        StorageSystem.report_date == report_date
    ).all()

    # Get all storage pools
    pools = db.query(StoragePool).filter(
        StoragePool.report_date == report_date
    ).all()

    # Get all capacity hosts
    hosts = db.query(CapacityHost).filter(
        CapacityHost.report_date == report_date
    ).all()

    # Get all capacity volumes for the report date
    volumes = db.query(CapacityVolume).filter(
        CapacityVolume.report_date == report_date
    ).all()

    # ============================================================================
    # v6.1.0: TENANT FILTERING (Admin Only)
    # ============================================================================
    if tenant and current_user.role == "admin":
        # Get tenant-specific pool and host names
        tenant_pools = get_tenant_pool_names(db, tenant)
        tenant_hosts = get_tenant_host_names(db, tenant)
        tenant_systems = get_tenant_system_names(db, tenant)

        # Filter volumes by pools
        if tenant_pools:
            volumes = [v for v in volumes if v.pool in tenant_pools]
        else:
            volumes = []

        # Filter systems by tenant systems
        if tenant_systems:
            systems = [s for s in systems if s.name in tenant_systems]
        else:
            systems = []

        # Filter pools by tenant pools
        if tenant_pools:
            pools = [p for p in pools if p.name in tenant_pools]
        else:
            pools = []

        # Filter hosts by tenant hosts
        if tenant_hosts:
            hosts = [h for h in hosts if h.name in tenant_hosts]
        else:
            hosts = []

    # Calculate global KPIs from capacity_volumes table
    # Handle both old (capacity_gib) and new (provisioned_capacity_gib) column names for backward compatibility
    try:
        # Try new column name first
        total_provisioned_capacity_gib = sum(v.provisioned_capacity_gib or 0 for v in volumes)
    except AttributeError:
        # Fall back to old column name if database hasn't been migrated
        total_provisioned_capacity_gib = sum(getattr(v, 'capacity_gib', 0) or 0 for v in volumes)

    total_used_provisioned_gib = sum(v.used_capacity_gib or 0 for v in volumes)
    total_available_provisioned_gib = sum(v.available_capacity_gib or 0 for v in volumes)
    total_savings_gib = sum(s.data_reduction_gib or 0 for s in systems)

    # Calculate system-level metrics (for Storage System Utilization)
    system_usable_capacity_gib = sum(s.usable_capacity_gib or 0 for s in systems)
    system_available_capacity_gib = sum(s.available_capacity_gib or 0 for s in systems)
    system_used_capacity_gib = system_usable_capacity_gib - system_available_capacity_gib

    # Overall Provisioned Capacity Utilization: (sum of used / sum of provisioned) * 100
    provisioned_utilization_pct = calculate_utilization_pct(total_used_provisioned_gib,
                                                            total_provisioned_capacity_gib) if total_provisioned_capacity_gib > 0 else 0

    # Overall Storage System Utilization: ((usable - available) / usable) * 100
    system_utilization_pct = calculate_utilization_pct(system_used_capacity_gib,
                                                       system_usable_capacity_gib) if system_usable_capacity_gib > 0 else 0

    kpis = {
        "total_capacity_tb": round(gib_to_tb(total_provisioned_capacity_gib), 2),
        "total_used_tb": round(gib_to_tb(total_used_provisioned_gib), 2),
        "total_available_tb": round(gib_to_tb(total_available_provisioned_gib), 2),
        "total_savings_tb": gib_to_tb(total_savings_gib),
        "provisioned_utilization_pct": round(provisioned_utilization_pct, 1),
        "system_utilization_pct": round(system_utilization_pct, 1),
        "avg_utilization_pct": round(provisioned_utilization_pct, 1),  # For backward compatibility
        "num_systems": len(systems),
        "num_pools": len(pools),
        "num_hosts": len(hosts)
    }

    # Identify critical and warning pools
    critical_pools = [p for p in pools if (p.utilization_pct or 0) > 80]
    warning_pools = [p for p in pools if 70 < (p.utilization_pct or 0) <= 80]

    # Calculate days until full for critical pools
    urgent_pools = []
    for pool in critical_pools:
        days = calculate_days_until_full(
            pool.utilization_pct or 0,
            gib_to_tb(pool.usable_capacity_gib or 0)
        )
        if days < 30:
            urgent_pools.append({
                "name": pool.name,
                "storage_system": pool.storage_system_name,
                "utilization_pct": round(pool.utilization_pct or 0, 1),
                "days_until_full": days
            })

    alerts = {
        "critical_count": len(critical_pools),
        "warning_count": len(warning_pools),
        "urgent_count": len(urgent_pools),
        "critical_pools": [
            {
                "name": p.name,
                "storage_system": p.storage_system_name,
                "utilization_pct": round(p.utilization_pct or 0, 1),
                "days_until_full": calculate_days_until_full(
                    p.utilization_pct or 0,
                    gib_to_tb(p.usable_capacity_gib or 0)
                )
            }
            for p in sorted(critical_pools, key=lambda x: x.utilization_pct or 0, reverse=True)[:5]
        ],
        "warning_pools": [
            {
                "name": p.name,
                "storage_system": p.storage_system_name,
                "utilization_pct": round(p.utilization_pct or 0, 1),
                "days_until_full": calculate_days_until_full(
                    p.utilization_pct or 0,
                    gib_to_tb(p.usable_capacity_gib or 0)
                )
            }
            for p in sorted(warning_pools, key=lambda x: x.utilization_pct or 0, reverse=True)[:5]
        ],
        "urgent_pools": urgent_pools
    }

    # Top 10 systems by capacity
    top_systems = []
    for system in sorted(systems, key=lambda s: s.usable_capacity_gib or 0, reverse=True)[:10]:
        total = system.usable_capacity_gib or 0
        available = system.available_capacity_gib or 0
        used = total - available

        top_systems.append({
            "name": system.name,
            "type": system.type,
            "model": system.model,
            "capacity_tb": gib_to_tb(total),
            "used_tb": gib_to_tb(used),
            "available_tb": gib_to_tb(available),
            "utilization_pct": calculate_utilization_pct(used, total)
        })

    # Utilization distribution (histogram data)
    utilization_bins = [0] * 10  # 10 bins: 0-10%, 10-20%, ..., 90-100%
    for system in systems:
        total = system.usable_capacity_gib or 0
        available = system.available_capacity_gib or 0
        if total > 0:
            used = total - available
            util = (used / total) * 100
            bin_idx = min(int(util / 10), 9)
            utilization_bins[bin_idx] += 1

    utilization_distribution = {
        "bins": ["0-10%", "10-20%", "20-30%", "30-40%", "40-50%",
                 "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"],
        "counts": utilization_bins
    }

    # Forecasting data (top 5 pools by utilization)
    forecasting_pools = sorted(pools, key=lambda p: p.utilization_pct or 0, reverse=True)[:5]
    forecasting_data = []

    for pool in forecasting_pools:
        util = pool.utilization_pct or 0
        projections = []

        # Calculate growth rate based on current utilization
        if util >= 95:
            growth_rate = 0.02  # 2% per month
        elif util >= 80:
            growth_rate = 0.015  # 1.5% per month
        else:
            growth_rate = 0.01  # 1% per month

        # Project 12 months ahead
        for month in range(13):
            projected = min(100, util + (growth_rate * 100 * month))
            projections.append(round(projected, 1))

        forecasting_data.append({
            "name": pool.name,
            "storage_system": pool.storage_system_name,
            "current_utilization": round(util, 1),
            "projections": projections  # Monthly projections for 0-12 months
        })

    # Treemap data (hierarchical structure for visualization)
    from app.utils.processing import get_treemap_data
    treemap_data = get_treemap_data(db, report_date)

    # Top 20 hosts by usage
    top_hosts = []
    for host in sorted(hosts, key=lambda h: h.used_san_capacity_gib or 0, reverse=True)[:20]:
        top_hosts.append({
            "name": host.name,
            "os_type": host.os_type,
            "total_capacity_tb": gib_to_tb(host.san_capacity_gib or 0),
            "used_capacity_tb": gib_to_tb(host.used_san_capacity_gib or 0),
            "utilization_pct": calculate_utilization_pct(
                host.used_san_capacity_gib or 0,
                host.san_capacity_gib or 0
            )
        })

    # Savings analysis (top 10 systems by savings)
    savings_data = []
    for system in sorted(systems, key=lambda s: s.data_reduction_gib or 0, reverse=True)[:10]:
        if (system.data_reduction_gib or 0) > 0:
            savings_data.append({
                "name": system.name,
                "savings_tb": gib_to_tb(system.data_reduction_gib or 0),
                "compression_ratio": system.total_compression_ratio or 1.0
            })

    # Storage type distribution
    type_distribution = {}
    for system in systems:
        system_type = system.type or "Unknown"
        if system_type not in type_distribution:
            type_distribution[system_type] = 0
        type_distribution[system_type] += gib_to_tb(system.usable_capacity_gib or 0)

    storage_types = [
        {"type": k, "capacity_tb": round(v, 2)}
        for k, v in type_distribution.items()
    ]

    # Generate recommendations
    recommendations = []

    # Urgent capacity recommendation
    if urgent_pools:
        recommendations.append({
            "type": "danger",
            "title": "⚠️ URGENT ACTION REQUIRED",
            "message": f"{len(urgent_pools)} pools will reach capacity in < 30 days",
            "details": [
                f"{p['name']}: Add ~{round(p.get('capacity_tb', 0) * 0.3, 1)} TB to extend 90 days"
                for p in urgent_pools[:3]
            ]
        })

    # Efficiency opportunity
    low_util_systems = [s for s in systems if calculate_utilization_pct(
        (s.usable_capacity_gib or 0) - (s.available_capacity_gib or 0),
        s.usable_capacity_gib or 0
    ) < 30]

    if low_util_systems:
        reclaim_tb = sum(gib_to_tb(s.available_capacity_gib or 0) for s in low_util_systems)
        recommendations.append({
            "type": "info",
            "title": "💡 EFFICIENCY OPPORTUNITY",
            "message": f"{len(low_util_systems)} systems have < 30% utilization",
            "details": [
                "Consolidate workloads to reduce hardware footprint",
                "Migrate data from over-utilized pools",
                f"Potential to reclaim ~{round(reclaim_tb, 1)} TB"
            ]
        })

    # Savings achievement
    if total_savings_gib > 0:
        savings_pct = (
                    total_savings_gib / total_provisioned_capacity_gib * 100) if total_provisioned_capacity_gib > 0 else 0
        recommendations.append({
            "type": "success",
            "title": "💰 SAVINGS ACHIEVED",
            "message": f"Storage efficiency features saved {gib_to_tb(total_savings_gib):.1f} TB",
            "details": [
                f"This represents {savings_pct:.1f}% of total capacity",
                "Keep compression and deduplication enabled for continued savings"
            ]
        })

    if not recommendations:
        recommendations.append({
            "type": "success",
            "title": "✅ All Systems Normal",
            "message": "No immediate actions required. All systems operating normally."
        })

    return {
        "report_date": report_date.isoformat(),
        "kpis": kpis,
        "alerts": alerts,
        "top_systems": top_systems,
        "utilization_distribution": utilization_distribution,
        "forecasting_data": forecasting_data,
        "treemap_data": treemap_data,
        "top_hosts": top_hosts,
        "savings_data": savings_data,
        "storage_types": storage_types,
        "recommendations": recommendations
    }


@router.get("/dashboard/pools")
async def get_pools_data(
        report_date: Optional[date] = Query(None),
        limit: int = Query(50, ge=1, le=200),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get storage pools data for data tables."""
    if not report_date:
        latest = db.query(func.max(StoragePool.report_date)).scalar()
        if not latest:
            return {"items": []}
        report_date = latest

    pools = db.query(StoragePool).filter(
        StoragePool.report_date == report_date
    ).order_by(StoragePool.utilization_pct.desc()).limit(limit).all()

    items = []
    for pool in pools:
        items.append({
            "name": pool.name,
            "storage_system": pool.storage_system_name,
            "capacity_tb": gib_to_tb(pool.usable_capacity_gib or 0),
            "used_tb": gib_to_tb(pool.used_capacity_gib or 0),
            "available_tb": gib_to_tb(pool.available_capacity_gib or 0),
            "utilization_pct": round(pool.utilization_pct or 0, 1),
            "days_until_full": calculate_days_until_full(
                pool.utilization_pct or 0,
                gib_to_tb(pool.usable_capacity_gib or 0)
            )
        })

    return {"items": items, "report_date": report_date.isoformat()}


@router.get("/dashboard/hosts")
async def get_hosts_data(
        report_date: Optional[date] = Query(None),
        limit: int = Query(50, ge=1, le=200),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get capacity hosts data for data tables."""
    if not report_date:
        latest = db.query(CapacityHost.report_date).order_by(
            CapacityHost.report_date.desc()
        ).first()
        if not latest:
            return {"items": []}
        report_date = latest[0]

    hosts = db.query(CapacityHost).filter(
        CapacityHost.report_date == report_date
    ).order_by(CapacityHost.used_san_capacity_gib.desc()).limit(limit).all()

    items = []
    for host in hosts:
        items.append({
            "name": host.name,
            "os_type": host.os_type,
            "total_capacity_tb": gib_to_tb(host.san_capacity_gib or 0),
            "used_capacity_tb": gib_to_tb(host.used_san_capacity_gib or 0),
            "utilization_pct": calculate_utilization_pct(
                host.used_san_capacity_gib or 0,
                host.san_capacity_gib or 0
            )
        })

    return {"items": items, "report_date": report_date.isoformat()}


@router.get("/upload-logs")
async def get_upload_logs(
        limit: int = Query(10, ge=1, le=100, description="Number of logs to return"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get recent upload logs with skipped records details.
    Returns full row data for all skipped records.
    """
    import json

    logs = db.query(UploadLog).order_by(
        UploadLog.upload_date.desc()
    ).limit(limit).all()

    result = []
    for log in logs:
        skipped_records = []
        if log.skipped_records_json:
            try:
                skipped_records = json.loads(log.skipped_records_json)
            except:
                skipped_records = []

        upload_statistics = None
        if log.upload_statistics_json:
            try:
                upload_statistics = json.loads(log.upload_statistics_json)
            except:
                upload_statistics = None

        result.append({
            "id": log.id,
            "upload_date": log.upload_date.isoformat() if log.upload_date else None,
            "file_name": log.file_name,
            "user_id": log.user_id,
            "rows_added": log.rows_added,
            "duplicates_skipped": log.duplicates_skipped,
            "status": log.status,
            "upload_duration_seconds": log.upload_duration_seconds,
            "skipped_records": skipped_records,  # Full row data for each skipped record
            "statistics": upload_statistics  # Detailed upload statistics
        })

    return {"logs": result}


@router.get("/tables")
async def get_available_tables(
        current_user: User = Depends(get_current_admin_user),
):
    """
    Get list of available database tables.
    Admin only.
    """
    tables = [
        # Core Data Tables (from Excel uploads)
        {'name': 'storage_systems', 'label': '📦 Storage Systems', 'category': 'Core Data'},
        {'name': 'storage_pools', 'label': '💾 Storage Pools', 'category': 'Core Data'},
        {'name': 'capacity_volumes', 'label': '📊 Capacity Volumes', 'category': 'Core Data'},
        {'name': 'capacity_hosts', 'label': '🖥️ Capacity Hosts', 'category': 'Core Data'},
        {'name': 'capacity_disks', 'label': '💿 Capacity Disks', 'category': 'Core Data'},
        {'name': 'departments', 'label': '🏢 Departments', 'category': 'Core Data'},

        # Application/Management Tables
        {'name': 'users', 'label': '👤 Users', 'category': 'Management'},
        {'name': 'tenants', 'label': '🏢 Tenants', 'category': 'Management'},
        {'name': 'user_tenants', 'label': '🔗 User-Tenant Mappings', 'category': 'Management'},
        {'name': 'tenant_pool_mappings', 'label': '🔗 Tenant-Pool Mappings', 'category': 'Management'},
        {'name': 'host_tenant_mappings', 'label': '🔗 Host-Tenant Mappings', 'category': 'Management'},
        {'name': 'mdisk_system_mappings', 'label': '🔗 MDisk-System Mappings', 'category': 'Management'},
        {'name': 'alerts', 'label': '🚨 Alerts', 'category': 'Management'},
        {'name': 'upload_logs', 'label': '📋 Upload Logs', 'category': 'Management'},
        {'name': 'user_activity_logs', 'label': '📝 User Activity Logs', 'category': 'Management'},
    ]
    return {'tables': tables}


@router.get("/tables/{table_name}/schema")
async def get_table_schema(
        table_name: str,
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Get schema information for a table including field categories.
    Returns column name, data type, and category (Imported/Calculated).
    Admin only.
    """
    from app.utils.field_metadata import get_field_category

    # Map table names to models
    table_map = {
        # Core Data Tables
        'storage_systems': StorageSystem,
        'storage_pools': StoragePool,
        'capacity_volumes': CapacityVolume,
        'capacity_hosts': CapacityHost,
        'capacity_disks': CapacityDisk,
        'departments': Department,

        # Application/Management Tables
        'users': User,
        'tenants': Tenant,
        'user_tenants': UserTenant,
        'tenant_pool_mappings': TenantPoolMapping,
        'host_tenant_mappings': HostTenantMapping,
        'mdisk_system_mappings': MdiskSystemMapping,
        'alerts': Alert,
        'upload_logs': UploadLog,
        'user_activity_logs': UserActivityLog,
    }

    if table_name not in table_map:
        raise HTTPException(status_code=400, detail="Invalid table name")

    model = table_map[table_name]

    # Build schema with field categories
    schema = []
    for column in model.__table__.columns:
        # Get SQLAlchemy type
        col_type = str(column.type)

        # Simplify type names
        if 'VARCHAR' in col_type or 'TEXT' in col_type:
            simple_type = 'String'
        elif 'INTEGER' in col_type:
            simple_type = 'Integer'
        elif 'FLOAT' in col_type or 'NUMERIC' in col_type:
            simple_type = 'Float'
        elif 'BOOLEAN' in col_type:
            simple_type = 'Boolean'
        elif 'DATETIME' in col_type:
            simple_type = 'DateTime'
        elif 'DATE' in col_type:
            simple_type = 'Date'
        else:
            simple_type = col_type

        # Get field category from metadata
        category = get_field_category(table_name, column.name)

        schema.append({
            'column_name': column.name,
            'data_type': simple_type,
            'category': category,
            'nullable': column.nullable,
            'primary_key': column.primary_key
        })

    return {
        'table_name': table_name,
        'schema': schema
    }


@router.get("/tables/{table_name}")
async def get_table_data(
        table_name: str,
        limit: Optional[int] = Query(50, description="Number of rows to return (None for all rows)"),
        offset: int = Query(0, description="Offset for pagination"),
        sort_by: Optional[str] = Query(None, description="Column to sort by"),
        sort_order: Optional[str] = Query('asc', description="Sort order (asc/desc)"),
        filter_column: Optional[str] = Query(None, description="Column to filter"),
        filter_value: Optional[str] = Query(None, description="Filter value"),
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Get data from a specific table with filtering and sorting.
    Admin only.
    Pass limit=None or omit limit to fetch all rows.
    """
    # Map table names to models
    table_map = {
        # Core Data Tables
        'storage_systems': StorageSystem,
        'storage_pools': StoragePool,
        'capacity_volumes': CapacityVolume,
        'capacity_hosts': CapacityHost,
        'capacity_disks': CapacityDisk,
        'departments': Department,

        # Application/Management Tables
        'users': User,
        'tenants': Tenant,
        'user_tenants': UserTenant,
        'tenant_pool_mappings': TenantPoolMapping,
        'host_tenant_mappings': HostTenantMapping,
        'mdisk_system_mappings': MdiskSystemMapping,
        'alerts': Alert,
        'upload_logs': UploadLog,
        'user_activity_logs': UserActivityLog,
    }

    if table_name not in table_map:
        raise HTTPException(status_code=400, detail="Invalid table name")

    model = table_map[table_name]
    query = db.query(model)

    # Apply filter
    if filter_column and filter_value:
        if hasattr(model, filter_column):
            col = getattr(model, filter_column)
            query = query.filter(col.ilike(f'%{filter_value}%'))

    # Get total count before pagination
    total_count = query.count()

    # Apply sorting
    if sort_by and hasattr(model, sort_by):
        col = getattr(model, sort_by)
        if sort_order == 'desc':
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())
    else:
        # Default sort by ID
        query = query.order_by(model.id.desc())

    # Apply pagination (if limit is provided)
    query = query.offset(offset)
    if limit is not None:
        rows = query.limit(limit).all()
    else:
        # Fetch all rows when limit is None
        rows = query.all()

    # Convert to dict
    data = []
    for row in rows:
        row_dict = {}
        for column in row.__table__.columns:
            value = getattr(row, column.name)
            # Convert datetime to string
            if isinstance(value, (datetime, date)):
                row_dict[column.name] = value.isoformat()
            else:
                row_dict[column.name] = value
        data.append(row_dict)

    # Get column names
    columns = [col.name for col in model.__table__.columns]

    return {
        'table_name': table_name,
        'columns': columns,
        'data': data,
        'total_count': total_count,
        'limit': limit,
        'offset': offset
    }


# ============================================================================
# Tenant Management (Admin Only) - v6.1.0
# ============================================================================

@router.get("/tenants/list")
async def get_tenant_list(
        current_user: User = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
):
    """
    Get list of all unique tenants for admin filtering.
    Returns tenant names from Tenant table.
    v6.1.0: New endpoint for admin tenant filter dropdown.
    """
    # Get unique tenant names from Tenant table
    tenants = db.query(Tenant.name).distinct().order_by(Tenant.name).all()

    tenant_names = [tenant[0] for tenant in tenants]

    return {
        'tenants': tenant_names,
        'count': len(tenant_names)
    }
