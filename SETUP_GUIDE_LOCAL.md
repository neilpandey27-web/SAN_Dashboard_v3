# 🚀 SAN Dashboard v3 - Local Setup Guide

## Latest Updates (Dec 23, 2024)
- ✅ Fixed comparison table to show tenant-level breakdown
- ✅ Restructured table: Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %
- ✅ Added debug logging for treemap data
- ✅ Enhanced tenant filtering and data organization

---

## 📋 Prerequisites

### Required Software:
1. **Node.js** (v18 or higher)
   - Download from: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

2. **Python** (v3.10 or higher)
   - Download from: https://www.python.org/
   - Verify: `python --version` or `python3 --version`

3. **PostgreSQL** (v14 or higher)
   - Download from: https://www.postgresql.org/download/
   - Verify: `psql --version`

---

## 🔧 Installation Steps

### Step 1: Extract the ZIP file
```bash
# Extract the downloaded zip file
unzip SAN_Dashboard_v3_Latest.zip
cd SAN_Dashboard_v3
```

### Step 2: Setup PostgreSQL Database

#### Option A: Using psql command line
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Inside psql prompt:
CREATE DATABASE san_dashboard;
CREATE USER san_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE san_dashboard TO san_user;
\q
```

#### Option B: Using pgAdmin
1. Open pgAdmin
2. Create a new database named `san_dashboard`
3. Create a user `san_user` with password
4. Grant all privileges to `san_user` on `san_dashboard`

### Step 3: Configure Backend Environment

```bash
cd backend

# Create .env file
cat > .env << 'ENVEOF'
# Database Configuration
DATABASE_URL=postgresql://san_user:your_secure_password@localhost:5432/san_dashboard

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Application Settings
DEBUG=True
ENVEOF

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
# Make sure you're in the backend directory with venv activated
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run database migrations
alembic upgrade head

# Create default admin user
python scripts/create_admin.py
# Follow prompts to create admin user
```

### Step 5: Configure Frontend Environment

```bash
cd ../frontend

# Create .env.local file
cat > .env.local << 'ENVEOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
ENVEOF

# Install Node.js dependencies
npm install
```

---

## 🚀 Running the Application

### Terminal 1: Start Backend Server

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**
API Documentation: **http://localhost:8000/docs**

### Terminal 2: Start Frontend Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## 📊 First-Time Usage

1. **Open browser**: Navigate to http://localhost:3000
2. **Login**: Use the admin credentials you created
3. **Navigate to Database Management**: Click on "Database Management" in the sidebar
4. **Upload Excel File**: Upload your storage data Excel file with required sheets:
   - Storage_Systems
   - Storage_Pools
   - Capacity_Volumes
   - Inventory_Hosts
   - Capacity_Hosts
   - Inventory_Disks
   - Capacity_Disks
   - Departments

5. **View Dashboard**: Go to "Overview" to see the dashboard with all charts and data

---

## 🎯 New Features in Latest Version

### Tenant-Level Comparison Table
- Organized by Tenant (not System)
- Shows: Tenant | Systems | Pool Names | Simple Avg % | Weighted Avg %
- Color-coded badges for utilization levels:
  - 🔴 Red: >80% (Critical)
  - 🟡 Yellow: >70% (Warning)
  - 🟢 Green: ≤70% (Healthy)

### Treemap Visualization
- Hierarchical view of storage capacity
- Weighted average calculation method
- Interactive drill-down capabilities

---

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Error:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
# or check in Services (Windows)

# Verify database exists
psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='san_dashboard';"
```

**Migration Errors:**
```bash
# Reset migrations (WARNING: deletes all data)
cd backend
alembic downgrade base
alembic upgrade head
```

### Frontend Issues

**Module Not Found:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Port Already in Use:**
```bash
# Kill process on port 3000 (Frontend)
# Linux/macOS:
lsof -ti:3000 | xargs kill -9
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Kill process on port 8000 (Backend)
# Linux/macOS:
lsof -ti:8000 | xargs kill -9
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**API Connection Error:**
- Verify backend is running on port 8000
- Check `frontend/.env.local` has correct `NEXT_PUBLIC_API_URL`
- Check browser console for CORS errors

---

## 📝 Environment Variables Reference

### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret for authentication
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `ALLOWED_ORIGINS`: CORS allowed origins

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL`: Backend API base URL

---

## 🔐 Default Admin Credentials

After running `python scripts/create_admin.py`, use the credentials you set.

**Recommended defaults for development:**
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123` (change in production!)

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Project README**: See README.md in root directory
- **Technical Specs**: See TECHNICAL_SPECIFICATIONS.md
- **Database Docs**: See DATABASE_DOCUMENTATION.md

---

## 🆘 Support

If you encounter any issues:
1. Check browser console for frontend errors
2. Check backend terminal for API errors
3. Verify all environment variables are set correctly
4. Ensure PostgreSQL service is running
5. Clear browser cache and cookies

---

## 📦 Production Deployment

For production deployment, see `DEPLOYMENT_GUIDE.md` for:
- Docker deployment
- Security hardening
- Performance optimization
- Backup strategies

---

**Version**: 6.2.0 (Latest with tenant-level comparison table)
**Last Updated**: December 23, 2024
