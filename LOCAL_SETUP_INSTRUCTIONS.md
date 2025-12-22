# SAN Dashboard v3 - Local Setup Instructions

## Overview
This package includes the complete SAN Analytics Dashboard with the new `overhead_used_capacity` field added to the volume table.

## What's New in This Version
✅ **NEW FEATURE**: `overhead_used_capacity` field
- Automatically calculated during data upload preprocessing
- Formula: `provisioned_capacity_gib - used_capacity_gib - available_capacity_gib`
- Excludes FlashSystem storage (A9K-A1, A9KR-R1, A9KR-R2)

## Prerequisites
- Docker & Docker Compose (recommended)
- OR Python 3.11+ and Node.js 18+ (for local development)

## Quick Start with Docker (Recommended)

### 1. Extract the ZIP file
```bash
unzip SAN_Dashboard_v3_with_overhead_capacity.zip -d SAN_Dashboard_v3
cd SAN_Dashboard_v3
```

### 2. Start all services
```bash
docker compose up -d
```

This will start:
- PostgreSQL database (port 5433)
- FastAPI backend (port 8000)
- Next.js frontend (port 3000)

### 3. Access the application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### 4. Default Login Credentials
```
Email: admin@company.com
Password: admin123
```

### 5. View logs
```bash
docker compose logs -f
```

### 6. Stop services
```bash
docker compose down
```

### 7. Stop and remove all data
```bash
docker compose down -v
```

## Local Development Setup (Without Docker)

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variables** (optional, defaults work for SQLite)
```bash
export DATABASE_URL="sqlite:///./san_analytics.db"
export SECRET_KEY="your-secret-key-here"
```

5. **Run the backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

1. **Open a new terminal and navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Set environment variables**
Create a `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Run the frontend**
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## Database Migration (If Using Existing Database)

If you have an existing database, you may need to add the new `overhead_used_capacity` column:

```sql
ALTER TABLE capacity_volumes 
ADD COLUMN overhead_used_capacity FLOAT;
```

Or let the application recreate the database (data will be lost):
```bash
# Stop services
docker compose down -v

# Start fresh
docker compose up -d
```

## Testing the New Feature

1. **Upload Excel Data**
   - Navigate to "Database Management" page
   - Upload an Excel file with storage data
   - The system will automatically calculate `overhead_used_capacity` during preprocessing

2. **Verify Calculation**
   - Check the API response for volume data at `/api/v1/data/volumes`
   - Non-FlashSystem volumes should have `overhead_used_capacity` calculated
   - FlashSystem volumes (A9K-A1, A9KR-R1, A9KR-R2) should have `overhead_used_capacity = 0`

## Project Structure

```
SAN_Dashboard_v3/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/      # API routes
│   │   ├── core/        # Configuration
│   │   ├── db/          # Database models & schemas
│   │   │   └── models.py      # ✨ NEW: overhead_used_capacity field
│   │   └── utils/       
│   │       └── processing.py  # ✨ NEW: calculate_overhead_used_capacity()
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Next.js React frontend
│   ├── app/            # App router pages
│   ├── components/     # React components
│   └── package.json
├── docker-compose.yml  # Docker orchestration
└── Documentation files

✨ = Modified files with new feature
```

## Modified Files in This Release

1. **backend/app/db/models.py**
   - Added `overhead_used_capacity` field to `CapacityVolume` model

2. **backend/app/utils/processing.py**
   - Added `calculate_overhead_used_capacity()` function
   - Implements calculation with FlashSystem exclusion logic

3. **backend/app/api/v1/data.py**
   - Integrated preprocessing into upload workflow

## Troubleshooting

### Port Already in Use
If ports 3000, 8000, or 5433 are already in use:

**Option 1**: Stop the conflicting service
```bash
# Find process using port
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :5433

# Kill the process
kill -9 <PID>
```

**Option 2**: Change ports in `docker-compose.yml`

### Database Connection Issues
```bash
# Check if PostgreSQL container is running
docker compose ps

# View PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Frontend Can't Connect to Backend
1. Check `NEXT_PUBLIC_API_URL` environment variable
2. Ensure backend is running on port 8000
3. Check CORS settings in `backend/app/main.py`

### Build Errors
```bash
# Clean Docker build cache
docker compose down
docker system prune -a
docker compose up -d --build
```

## Documentation

Comprehensive documentation is included:
- **DOCUMENTATION_INDEX.md** - Documentation navigation
- **DEPLOYMENT_GUIDE.md** - Detailed deployment instructions
- **DATABASE_DOCUMENTATION.md** - Database schemas and details
- **TECHNICAL_SPECIFICATIONS.md** - API reference and features
- **FIXES_AND_UPDATES.md** - Recent changes and fixes

## Support

For issues or questions:
1. Check the documentation files included in this package
2. Review the API documentation at http://localhost:8000/api/docs
3. Check browser console (F12) for frontend errors
4. Review logs with `docker compose logs -f`

## Git Repository

This code is maintained at:
https://github.com/neilpandey27-web/SAN_Dashboard_v3

Pull Request with these changes:
https://github.com/neilpandey27-web/SAN_Dashboard_v3/pull/1

---

**Version**: 2.0.0 with overhead_used_capacity feature
**Last Updated**: December 22, 2024
**Branch**: genspark_ai_developer
