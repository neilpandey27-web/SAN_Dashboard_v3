"""
OneIT SAN Analytics Dashboard - FastAPI Backend Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import logging
import os

from app.core.config import settings
from app.db.database import init_db
from app.api.v1 import auth, data, alerts, users, mappings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the application."""
    # Startup
    logger.info("Starting OneIT SAN Analytics API...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down OneIT SAN Analytics API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="API for OneIT SAN Analytics Dashboard - Monitor and manage IBM storage capacity",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(data.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(mappings.router, prefix=settings.API_V1_STR)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Download endpoint for v2.6.0
@app.get("/download/v2.6.0")
async def download_v260():
    """Download v2.6.0 version (401KB - source code only, no git history)."""
    file_path = "/home/user/webapp/backend/public/webapp-v2.6.0.tar.gz"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="webapp-v2.6.0.tar.gz",
            media_type="application/gzip"
        )
    return JSONResponse(
        status_code=404,
        content={"detail": "Backup file not found"}
    )


# Download endpoint for updated frontend folder
@app.get("/download/frontend")
async def download_frontend():
    """Download updated frontend folder with simplified Storage Systems tab."""
    file_path = "/home/user/webapp/backend/public/frontend-updated.tar.gz"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="frontend-updated.tar.gz",
            media_type="application/gzip"
        )
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend archive not found"}
    )


# Download endpoint for latest (with git history)
@app.get("/download/webapp-latest")
async def download_backup():
    """Download the latest webapp backup (145MB - includes git history)."""
    file_path = "/home/user/webapp/backend/public/webapp-latest-20251211.tar.gz"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="webapp-latest-20251211.tar.gz",
            media_type="application/gzip"
        )
    return JSONResponse(
        status_code=404,
        content={"detail": "Backup file not found"}
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/api/docs",
        "api_base": settings.API_V1_STR
    }


# Download endpoint for updated frontend
@app.get("/download/frontend-updated")
async def download_frontend_updated():
    """Download the updated frontend folder with simplified Storage Systems tab."""
    file_path = "/home/user/webapp/webapp/public/downloads/frontend-updated.tar.gz"
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="frontend-updated.tar.gz",
            media_type="application/gzip"
        )
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend archive not found"}
    )


# Download endpoint for backup file (OLD - use /download/complete instead)
@app.get("/download/backup")
async def download_backup():
    """Download the latest project backup."""
    backup_file = "/home/user/webapp/public/downloads/webapp-backup-20251207-144938.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Backup file not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-storage-insights-backup.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for COMPLETE backup with ALL updates
@app.get("/download/complete")
async def download_complete():
    """Download the complete project backup with all updates including statistics UI."""
    backup_file = "/home/user/webapp/public/downloads/webapp-complete-latest.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Complete backup file not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-storage-insights-complete.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for latest webapp folder
@app.get("/download/webapp")
async def download_webapp():
    """Download the complete webapp folder archive."""
    backup_file = "/home/user/webapp/public/downloads/webapp-download.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Webapp download file not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-download.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for Docker CORS fix
@app.get("/download/webapp-docker-fix")
async def download_docker_fix():
    """Download the webapp archive with Docker CORS fix."""
    backup_file = "/home/user/webapp/public/downloads/webapp-docker-cors-FIXED.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Docker fix file not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-docker-cors-FIXED.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for consolidated documentation version
@app.get("/download/webapp-consolidated")
async def download_consolidated():
    """Download webapp with consolidated documentation (79 docs → 4 files)."""
    backup_file = "/home/user/webapp/public/downloads/webapp-consolidated-docs.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Consolidated docs file not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-consolidated-docs.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for three fixes
@app.get("/download/webapp-three-fixes")
async def download_three_fixes():
    """Download three fixes archive (tooltips, storage systems, CSV download)."""
    backup_file = "/home/user/webapp/public/downloads/webapp-three-fixes.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Three fixes archive not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-three-fixes.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for three fixes complete package
@app.get("/download/webapp-three-fixes-complete")
async def download_three_fixes_complete():
    """Download complete package with fixes and Docker rebuild instructions."""
    backup_file = "/home/user/webapp/public/downloads/webapp-three-fixes-complete.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Complete three fixes package not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-three-fixes-complete.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for storage systems fix with API updates
@app.get("/download/webapp-storage-systems-fixed")
async def download_storage_systems_fixed():
    """Download updated package with Storage Systems column fix including API updates."""
    backup_file = "/home/user/webapp/public/downloads/webapp-storage-systems-fixed.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Storage Systems fix package not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-storage-systems-fixed.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for all fixes verified
@app.get("/download/webapp-all-fixes-verified")
async def download_all_fixes_verified():
    """Download complete verified package with all three fixes and troubleshooting guides."""
    backup_file = "/home/user/webapp/public/downloads/webapp-all-fixes-verified.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "All fixes verified package not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-all-fixes-verified.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for complete webapp folder
@app.get("/download/webapp-complete-folder")
async def download_complete_folder():
    """Download the complete webapp folder with all files (backend, frontend, configs, docs)."""
    backup_file = "/home/user/webapp/public/downloads/webapp-complete-folder.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Complete webapp folder not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-complete-folder.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for drill-down fix
@app.get("/download/webapp-drilldown")
async def download_drilldown():
    """Download webapp with Storage Systems drill-down fix (correct columns + navigation)."""
    backup_file = "/home/user/webapp/public/downloads/webapp-drilldown-fixed.tar.gz"
    
    if not os.path.exists(backup_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Drill-down fix file not found"}
        )
    
    return FileResponse(
        path=backup_file,
        filename="webapp-drilldown-fixed.tar.gz",
        media_type="application/gzip"
    )


# Download endpoint for fixed db-mgmt page
@app.get("/download/db-mgmt-fix")
async def download_dbmgmt_fix():
    """Download the fixed db-mgmt page."""
    fixed_file = "/home/user/webapp/public/downloads/db-mgmt-page-FIXED.tsx"
    
    if not os.path.exists(fixed_file):
        return JSONResponse(
            status_code=404,
            content={"detail": "Fixed file not found"}
        )
    
    return FileResponse(
        path=fixed_file,
        filename="page.tsx",
        media_type="text/plain"
    )


# Download endpoints for upload statistics feature
@app.get("/download/models-py")
async def download_models():
    """Download updated models.py file."""
    return FileResponse(
        path="/home/user/webapp/public/downloads/models.py",
        filename="models.py",
        media_type="text/plain"
    )


@app.get("/download/data-py")
async def download_data():
    """Download updated data.py file."""
    return FileResponse(
        path="/home/user/webapp/public/downloads/data.py",
        filename="data.py",
        media_type="text/plain"
    )


@app.get("/download/migration-sql")
async def download_migration():
    """Download database migration SQL."""
    return FileResponse(
        path="/home/user/webapp/public/downloads/add_statistics_column.sql",
        filename="add_statistics_column.sql",
        media_type="text/plain"
    )


@app.get("/download/install-guide")
async def download_install_guide():
    """Download installation guide."""
    return FileResponse(
        path="/home/user/webapp/public/downloads/UPLOAD_STATS_UPDATE.md",
        filename="INSTALL_GUIDE.md",
        media_type="text/markdown"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
