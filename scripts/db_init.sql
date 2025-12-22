-- OneIT SAN Analytics Database Initialization Script
-- This script is run automatically when PostgreSQL container starts

-- Database is created by POSTGRES_DB env var, so just confirm it
SELECT 'Database storage_insights initialized' AS status;

-- The actual table creation is handled by SQLAlchemy's Base.metadata.create_all()
-- which runs on application startup via init_db() in app/db/database.py
