# 🚀 OneIT SAN Analytics - Deployment Guide

**Version:** 2.0.0  
**Last Updated:** December 11, 2025

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Setup](#docker-setup)
3. [Local Development Setup](#local-development-setup)
4. [Database Configuration](#database-configuration)
5. [Production Deployment](#production-deployment)
6. [Docker Rebuild Instructions](#docker-rebuild-instructions)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start

### **Prerequisites**
- Docker & Docker Compose (recommended) **OR**
- Python 3.9+, Node.js 18+, PostgreSQL 15+

### **Quick Docker Start (Recommended)**

```bash
# 1. Clone or extract the project
cd webapp

# 2. Start with Docker Compose
docker compose up -d

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs

# 4. Default credentials
# Username: admin@company.com
# Password: admin123
```

---

## 🐳 Docker Setup

### **Docker Compose Configuration**

The project includes a complete Docker setup with:
- **PostgreSQL 15** database
- **FastAPI** backend (Python)
- **Next.js** frontend (React/TypeScript)

### **Important: Docker Networking Fix**

**If you experience CORS errors or clicks not working:**

The `docker-compose.yml` has been configured with proper networking:

```yaml
frontend:
  environment:
    # CRITICAL: Use host.docker.internal for browser → backend communication
    - NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
  extra_hosts:
    # Linux compatibility
    - "host.docker.internal:host-gateway"

backend:
  environment:
    # Allow requests from all possible sources
    - CORS_ORIGINS=["http://localhost:3000","http://frontend:3000","http://host.docker.internal:3000","http://127.0.0.1:3000"]
```

### **Docker Commands**

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Restart a specific service
docker compose restart backend
docker compose restart frontend

# Rebuild after code changes
docker compose build --no-cache
docker compose up -d

# Stop all services
docker compose down

# Complete reset (removes data!)
docker compose down -v
```

### **Linux-Specific Setup**

If `host.docker.internal` doesn't work on Linux:

**Option 1: Use Docker bridge IP**
```yaml
# In docker-compose.yml
NEXT_PUBLIC_API_URL=http://172.17.0.1:8000
```

**Option 2: Find your host IP**
```bash
ip addr show docker0 | grep inet
# Use that IP in NEXT_PUBLIC_API_URL
```

---

## 💻 Local Development Setup

### **Backend Setup (Python/FastAPI)**

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your database URL and settings

# 5. Initialize database
# For PostgreSQL:
# Ensure PostgreSQL is running and database exists
# The app will create tables automatically on first run

# 6. Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend Setup (Next.js)**

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Set up environment variables
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > .env.local

# 4. Run development server
npm run dev

# Frontend will be available at http://localhost:3000
```

### **Mac-Specific Setup**

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb storage_insights

# Install Python dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node.js dependencies
cd ../frontend
npm install

# Start both services
# Terminal 1:
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2:
cd frontend && npm run dev
```

---

## 🗄️ Database Configuration

### **PostgreSQL (Recommended for Production)**

**Connection URL Format:**
```
postgresql://username:password@host:port/database_name
```

**Docker (default):**
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/storage_insights
```

**Local development:**
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/storage_insights
```

### **SQLite (Development Only)**

For local development without PostgreSQL:

```bash
# In backend/.env
DATABASE_URL=sqlite:///../db_files/storage_insights.db

# The db_files directory will be created automatically
```

### **Database Initialization**

The application automatically:
1. Creates all required tables on first run
2. Creates default admin user (admin@company.com / admin123)
3. Sets up indexes and constraints

**Manual Migration (if needed):**
```bash
cd backend

# Check current database
python -c "from app.db.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"

# The app handles migrations automatically via SQLAlchemy
```

### **Database Backup**

```bash
# PostgreSQL backup (Docker)
docker compose exec db pg_dump -U postgres storage_insights > backup.sql

# PostgreSQL restore (Docker)
docker compose exec -T db psql -U postgres storage_insights < backup.sql

# SQLite backup
cp db_files/storage_insights.db db_files/storage_insights.db.backup
```

---

## 🚀 Production Deployment

### **Production Checklist**

Before deploying to production:

- [ ] Change `SECRET_KEY` in environment variables
- [ ] Set `DEBUG=false`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Configure proper CORS origins
- [ ] Set up SMTP for email alerts (optional)
- [ ] Configure SSL/HTTPS
- [ ] Set up regular database backups
- [ ] Change default admin password

### **Environment Variables (Production)**

**Backend (.env):**
```bash
# Application
APP_NAME=OneIT SAN Analytics
APP_VERSION=2.0.0
DEBUG=false

# Security
SECRET_KEY=your-super-secret-key-here-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:pass@host:5432/storage_insights

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# SMTP (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@company.com
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### **Docker Production Deployment**

```bash
# 1. Update docker-compose.yml with production values

# 2. Build production images
docker compose -f docker-compose.yml build

# 3. Start services
docker compose up -d

# 4. Check logs
docker compose logs -f

# 5. Verify health
curl http://localhost:8000/health
```

### **Manual Production Deployment**

**Backend:**
```bash
cd backend

# Use production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**Frontend:**
```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start

# Or use PM2 for process management
npm install -g pm2
pm2 start npm --name "frontend" -- start
```

---

## 🔄 Docker Rebuild Instructions

### **When to Rebuild**

Rebuild your Docker containers when:
- You've updated frontend code (React/Next.js changes)
- You've updated backend code (Python/FastAPI changes)
- Fixes have been applied (like the three critical fixes)
- Dependencies have changed

### **Rebuild Methods**

#### **Option 1: Full Rebuild (Recommended)**

```bash
# Navigate to project directory
cd /home/user/webapp

# Stop all containers
docker compose down

# Rebuild frontend with new changes
docker compose build frontend

# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Check logs (optional)
docker compose logs -f frontend
```

#### **Option 2: Quick Frontend-Only Rebuild**

```bash
cd /home/user/webapp

# Rebuild only frontend container
docker compose build frontend

# Restart only frontend service
docker compose restart frontend

# Check status
docker compose ps frontend
```

#### **Option 3: Rebuild from Scratch (If issues persist)**

```bash
cd /home/user/webapp

# Stop and remove all containers
docker compose down -v

# Remove old images
docker compose build --no-cache frontend

# Start fresh
docker compose up -d

# Verify
docker compose ps
```

### **Expected Build Times**

- **Full rebuild**: 3-5 minutes
- **Frontend only**: 2-3 minutes
- **No-cache rebuild**: 5-10 minutes

---

## 🔧 Troubleshooting

### **1. CORS Errors in Browser Console**

**Symptom:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution for Docker:**
```yaml
# Ensure docker-compose.yml has:
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=http://host.docker.internal:8000
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

**Solution for Local:**
```bash
# Ensure backend .env has:
CORS_ORIGINS=["http://localhost:3000"]

# Ensure frontend .env.local has:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **2. Database Connection Errors**

**Error:** `FATAL: database "storage_insights" does not exist`

**Solution:**
```bash
# Docker:
docker compose exec db createdb -U postgres storage_insights

# Local PostgreSQL:
createdb storage_insights
```

**Error:** `could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
# Docker:
docker compose ps

# Local:
pg_isready
sudo systemctl status postgresql  # Linux
brew services list  # Mac
```

### **3. Row Clicks Not Working (Drill-down)**

**Symptom:** Clicking on storage system rows does nothing

**Cause:** Usually CORS or environment configuration issue

**Solution:**
1. Check browser console (F12) for errors
2. Verify `NEXT_PUBLIC_API_URL` is correctly set
3. For Docker: Must use `host.docker.internal:8000`
4. For Local: Use `localhost:8000`
5. Hard refresh browser (Ctrl+Shift+R)

### **4. Upload Failures**

**Error:** `413 Payload Too Large`

**Solution:**
```python
# In backend/app/core/config.py
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
```

**Error:** `Invalid file format`

**Solution:**
- Ensure file is `.xlsx` or `.xls`
- Check column headers match expected format
- Verify data formatting

### **5. Port Already in Use**

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000
# or
netstat -ano | grep 8000

# Kill the process
kill -9 <PID>

# Or use different ports in docker-compose.yml:
ports:
  - "8001:8000"  # backend
  - "3001:3000"  # frontend
```

### **6. Docker Build Failures**

**Error:** Build failures or dependency issues

**Solution:**
```bash
# Clean rebuild
docker compose down
docker system prune -a
docker compose build --no-cache
docker compose up -d
```

### **7. Frontend Build Errors**

**Error:** `Module not found` or TypeScript errors

**Solution:**
```bash
cd frontend

# Clean install
rm -rf node_modules .next
npm install

# Clear cache
npm cache clean --force
npm install
```

### **8. Frontend not building**
```bash
# Check for port conflicts
sudo lsof -i :3000

# Check Docker logs
docker compose logs frontend

# Try clean rebuild
docker compose down
docker system prune -f
docker compose build --no-cache frontend
docker compose up -d
```

### **9. Changes not reflecting**
```bash
# Force rebuild without cache
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend
```

### **10. Permission issues**
```bash
# Fix permissions (if needed)
sudo chown -R $USER:$USER /home/user/webapp
```

### **11. Authentication Issues**

**Error:** `Invalid credentials` with correct password

**Solution:**
```bash
# Reset admin password using Python shell
cd backend
source venv/bin/activate
python

>>> from app.db.database import get_db
>>> from app.models.models import User
>>> from app.core.security import get_password_hash
>>> db = next(get_db())
>>> admin = db.query(User).filter(User.email == "admin@company.com").first()
>>> admin.hashed_password = get_password_hash("admin123")
>>> db.commit()
>>> exit()
```

---

## 📚 Additional Resources

### **API Documentation**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### **Project Structure**
```
webapp/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Configuration
│   │   ├── db/            # Database
│   │   ├── models/        # Data models
│   │   └── main.py        # Application entry
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              # Next.js frontend
│   ├── app/               # Next.js app router
│   ├── components/        # React components
│   ├── lib/               # Utilities
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml     # Docker orchestration
└── README.md
```

### **Default Credentials**
- **Email:** admin@company.com
- **Password:** admin123
- **⚠️ Change these in production!**

---

## 📦 Download Complete Application

**Complete Webapp Folder (All Files)**:
```
https://8000-i65shl7xcwopxsxvhr7d8-b32ec7bb.sandbox.novita.ai/download/webapp-complete-folder
```

**File**: `webapp-complete-folder.tar.gz` (491 KB)

**Includes**:
- ✅ Complete backend application
- ✅ Complete frontend application (with all fixes)
- ✅ All configuration files
- ✅ Docker setup
- ✅ Database migrations
- ✅ All three fixes applied (tooltips, columns, CSV download)

---

## 🆘 Support

For additional help:
1. Check browser console (F12) for client-side errors
2. Check backend logs: `docker compose logs backend`
3. Check frontend logs: `docker compose logs frontend`
4. Review API docs: http://localhost:8000/api/docs

---

**Status**: ✅ Complete deployment guide covering Docker, local development, and production setups
