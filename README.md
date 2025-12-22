# OneIT SAN Analytics Dashboard

**Version 2.0.0** - A comprehensive storage monitoring and capacity management dashboard for IBM storage systems.

## 📚 Documentation

**All documentation has been reorganized into 4 comprehensive files:**

- **[📖 DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Start here! Navigation guide to all documentation
- **[🚀 DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete setup, Docker, local development, troubleshooting
- **[🔧 FIXES_AND_UPDATES.md](FIXES_AND_UPDATES.md)** - All fixes, updates, and verification guides
- **[🗄️ DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)** - Database persistence, schemas, backup/restore
- **[📘 TECHNICAL_SPECIFICATIONS.md](TECHNICAL_SPECIFICATIONS.md)** - Features, architecture, APIs, data models

> **Note:** All previous documentation files (~30+ files) have been consolidated into these 4 comprehensive guides. Original files are backed up in `old_docs_backup/` directory. **80% fewer files, 100% better organization!**

## ✨ Key Features

- **📊 Interactive Dashboard**
  - Overview with dual treemaps (Pool & Disk capacity visualization)
  - Compression metrics and deduplication analysis
  - Historical growth tracking and forecasting
  - Duration filters (3, 6, 12 months, All time)

- **🗂️ Data Management**
  - Storage Systems with drill-down to disk details
  - Storage Pools management
  - Disk and Host inventory
  - Excel upload for bulk data import
  - Upload history tracking

- **🚨 Alerts & Monitoring**
  - Threshold-based alerting (80%, 90% utilization)
  - Email notifications (configurable)
  - Alert management and resolution

- **👥 User Management**
  - JWT-based authentication
  - Role-based access control (Admin, User, Viewer)
  - User CRUD operations

- **📈 Reports**
  - Capacity and utilization reports
  - Historical trend analysis
  - Export to Excel/PDF



## Tech Stack

### Backend
- FastAPI (Python 3.11)
- SQLAlchemy 2.x
- **PostgreSQL** (Recommended) / SQLite (Development)
- JWT Authentication
- Pandas for data processing

### Frontend
- Next.js 14
- React 18
- TypeScript
- Bootstrap 5 (Dark Theme)
- Plotly.js for charts

## 🌐 Live Demo (Sandbox Environment)

- **Frontend**: https://3000-i65shl7xcwopxsxvhr7d8-b32ec7bb.sandbox.novita.ai
- **Backend API**: https://8000-i65shl7xcwopxsxvhr7d8-b32ec7bb.sandbox.novita.ai
- **API Docs**: https://8000-i65shl7xcwopxsxvhr7d8-b32ec7bb.sandbox.novita.ai/api/docs

**Default Credentials:**
- Email: `admin@company.com`
- Password: `admin123`

## 🚀 Quick Start

### **Docker (Recommended)**

```bash
# 1. Start all services
docker compose up -d

# 2. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs

# 3. Login
# Email: admin@company.com
# Password: admin123
```

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete instructions**

### **Local Development**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed setup**

## 🐳 Docker Deployment

### **Services Included**
- PostgreSQL 15 Database (port 5433)
- FastAPI Backend (port 8000)
- Next.js Frontend (port 3000)

### **Key Features**
- ✅ Persistent volume for database
- ✅ Health checks for all services
- ✅ Secure container networking
- ✅ Production-ready configuration

### **Commands**
```bash
docker compose up -d          # Start all services
docker compose ps             # Check status
docker compose logs -f        # View logs
docker compose down           # Stop services
docker compose down -v        # Stop and remove data
```

**Full Docker documentation: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

## 📁 Project Structure

```
webapp/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/v1/      # API routes
│   │   ├── core/        # Configuration
│   │   ├── db/          # Database
│   │   ├── models/      # Data models
│   │   └── main.py      # Application entry
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── app/             # App router pages
│   ├── components/      # React components
│   ├── lib/             # Utilities
│   └── package.json
├── docker-compose.yml         # Docker orchestration
├── DOCUMENTATION_INDEX.md     # Documentation navigation
├── DEPLOYMENT_GUIDE.md        # Setup & deployment
├── FIXES_AND_UPDATES.md       # Changes & fixes
├── DATABASE_DOCUMENTATION.md  # Database details
├── TECHNICAL_SPECIFICATIONS.md # Features & APIs
└── README.md                  # This file
```

## 🔌 API Documentation

Complete API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

**Main Endpoints:**
- Authentication: `/api/v1/auth/*`
- Data Management: `/api/v1/data/*`
- Alerts: `/api/v1/alerts/*`
- Users: `/api/v1/users/*`

**See [TECHNICAL_SPECIFICATIONS.md](TECHNICAL_SPECIFICATIONS.md) for complete API reference**

## 📤 Data Upload

Upload Excel files with storage data via Database Management page.

**Supported formats:** `.xlsx`, `.xls`  
**Max size:** 50MB (configurable)

**Expected sheets:**
- Storage Systems
- Storage Pools
- Disks
- Hosts

The application automatically extracts and classifies data.

## 🆘 Troubleshooting

**Common Issues:**
- **CORS errors**: Check Docker networking configuration
- **Row clicks not working**: Verify `NEXT_PUBLIC_API_URL` environment variable
- **Database connection**: Ensure PostgreSQL container is healthy

**See [DEPLOYMENT_GUIDE.md - Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting) for detailed solutions**

## 📄 License

MIT License

## 💬 Support

- **Start with**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for navigation
- **Setup issues**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Recent changes**: [FIXES_AND_UPDATES.md](FIXES_AND_UPDATES.md)
- **Database questions**: [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)
- **Technical details**: [TECHNICAL_SPECIFICATIONS.md](TECHNICAL_SPECIFICATIONS.md)
- **API reference**: http://localhost:8000/api/docs
- **Browser console**: F12 for frontend errors
- **Logs**: `docker compose logs -f`


## Latest Updates (December 11, 2025)

### Three Critical Fixes Applied ✅

1. **Database Management Tooltips** - Field descriptions now appear on hover in Schema view
2. **Storage Systems Columns** - Fixed to show: System Name, Capacity (TB), Used (TB), Available (TB), Util %, Pools, Volumes
3. **CSV Download** - Added download button for table data in Database Management

See [FIXES_AND_UPDATES.md](FIXES_AND_UPDATES.md) for detailed information.

### Documentation Reorganization ✅

- **Before**: 30+ scattered documentation files
- **After**: 4 comprehensive, well-organized files
- **Benefit**: 80% fewer files, easier to find information, reduced duplication

See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for the new documentation structure.
