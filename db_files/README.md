# Database Files Directory

## 📁 Purpose

This directory contains all database files for OneIT SAN Analytics, **separated from the code** to allow independent updates.

## ⚠️ IMPORTANT: Database File NOT Included in Package

### Why You Don't See `storage_insights.db`:

**This is INTENTIONAL and CORRECT!**

The database file (`.db`) is **gitignored** and **NOT included** in downloaded packages because:

1. ✅ **Your data is personal** - Each installation creates its own database
2. ✅ **Security** - Database contains user accounts and uploaded data
3. ✅ **File size** - Keeps package small (database can be 10+ MB with data)
4. ✅ **Prevents data overwrite** - Your database is never replaced during updates

### What You'll See After Download:
```
db_files/
├── README.md       ✅ This file
├── .gitkeep        ✅ Placeholder
└── storage_insights.db  ❌ NOT included (will be created)
```

### What Happens When You Start the App:

1. **Extract package** → `db_files/` folder exists but is empty
2. **Run `docker-compose up -d`** → Backend starts
3. **Backend creates database** → `storage_insights.db` appears automatically!
4. **Upload Excel data** → Database gets populated with your data

### To Verify Database Creation:

```bash
# After starting services, run:
./scripts/verify_database.sh

# Or manually check:
ls -lh db_files/storage_insights.db
```

## 🎯 Why This Structure?

When you update the application:
- **Update frontend only**: Replace `frontend/` folder only
- **Update backend only**: Replace `backend/` folder only  
- **Update both**: Replace both folders
- **Database**: Always preserved in `db_files/` - never replaced!

## 📊 Database File

### SQLite Database (Development)
```
db_files/storage_insights.db
```

This file contains:
- Storage Systems
- Storage Pools
- Capacity Volumes
- Inventory Hosts
- Capacity Hosts
- Inventory Disks
- Capacity Disks
- Departments
- User accounts
- Tenant mappings
- All your uploaded data!

### PostgreSQL Database (Production)
For production deployment, PostgreSQL runs in Docker volume:
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```
The `db_files/` folder is only used for development (SQLite).

## 🔒 Database Preservation

### Automatic Backup Location
```
~/storage_insights_backups/storage_insights_TIMESTAMP.db
```

### Manual Backup Command
```bash
cp db_files/storage_insights.db ~/Desktop/my_backup.db
```

### Restore Command
```bash
cp ~/Desktop/my_backup.db db_files/storage_insights.db
```

## 📦 Update Workflows

### Method 1: Selective Folder Replacement (NEW!)

**Update Frontend Only**:
```bash
cd /Users/nileshpandey/Documents/SAN/SAN_DASH_v2
rm -rf frontend/
cp -r /path/to/new/package/frontend/ .
docker-compose restart
```

**Update Backend Only**:
```bash
cd /Users/nileshpandey/Documents/SAN/SAN_DASH_v2
rm -rf backend/
cp -r /path/to/new/package/backend/ .
docker-compose restart
```

**Update Both (Database Safe)**:
```bash
cd /Users/nileshpandey/Documents/SAN/SAN_DASH_v2
rm -rf frontend/ backend/
cp -r /path/to/new/package/frontend/ .
cp -r /path/to/new/package/backend/ .
# db_files/ stays untouched!
docker-compose restart
```

### Method 2: Git Pull (Recommended)
```bash
cd /Users/nileshpandey/Documents/SAN/SAN_DASH_v2
./scripts/update.sh
```

### Method 3: Full Replacement with Backup
```bash
# 1. Backup
cp db_files/storage_insights.db ~/backup.db

# 2. Replace everything
cd /Users/nileshpandey/Documents/SAN
rm -rf SAN_DASH_v2
tar -xzf new-package.tar.gz

# 3. Restore database
cp ~/backup.db SAN_DASH_v2/db_files/storage_insights.db

# 4. Restart
cd SAN_DASH_v2
docker-compose restart
```

## ⚙️ Configuration

### Backend Configuration
File: `backend/app/core/config.py`
```python
DATABASE_URL: str = "sqlite:///../db_files/storage_insights.db"
```

The `../` means "go up one directory from backend/", so:
```
backend/ (current directory)
  ↓
webapp/ (up one level)
  ↓
db_files/ (sibling directory)
  ↓
storage_insights.db (database file)
```

## 🗂️ Directory Structure

```
webapp/
├── frontend/           # Next.js application (can replace)
├── backend/            # FastAPI application (can replace)
├── db_files/           # Database files (NEVER replace!)
│   ├── README.md       # This file
│   └── storage_insights.db  # Your data (gitignored)
├── scripts/            # Update and backup scripts
└── docs/               # Documentation
```

## 🚨 Important Notes

### ✅ SAFE Operations (Won't Affect Database)
- Replace `frontend/` folder
- Replace `backend/` folder
- Replace `scripts/` folder
- Replace `docs/` folder
- Run `git pull`
- Run `./scripts/update.sh`
- Run `docker-compose restart`

### ⚠️ CAUTION Operations
- Replacing entire `webapp/` folder (backup `db_files/` first!)
- Running `rm -rf SAN_DASH_v2` (backup `db_files/` first!)

### ❌ DANGEROUS Operations (Will Delete Database)
- Deleting `db_files/` folder
- Running `rm db_files/storage_insights.db`
- Running `docker-compose down -v` (if using PostgreSQL)

## 🔍 Verify Database

### Check Database Exists
```bash
ls -lh db_files/storage_insights.db
```

### Check Database Has Data
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('db_files/storage_insights.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM storage_systems')
systems = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM storage_pools')
pools = cursor.fetchone()[0]
print(f'Storage Systems: {systems}')
print(f'Storage Pools: {pools}')
print(f'Status: {"Has data ✅" if systems > 0 else "Empty - upload data"}')
conn.close()
EOF
```

## 📋 Size Reference

- **Empty database**: ~268 KB
- **Small dataset** (10 systems): ~500 KB
- **Medium dataset** (50 systems): ~2-5 MB
- **Large dataset** (100+ systems): 10+ MB

## 🆘 Database Issues

### Database Not Found
If `storage_insights.db` doesn't exist:
1. It will be created automatically on first Excel upload
2. Or restore from backup: `cp ~/backup.db db_files/storage_insights.db`

### Database Corrupted
If database is corrupted:
1. Check backups in `~/storage_insights_backups/`
2. Restore latest good backup
3. Or delete and re-upload Excel data

### Database Too Large
If database grows too large:
1. Export data to CSV via API
2. Delete old report dates
3. Vacuum database: `sqlite3 db_files/storage_insights.db "VACUUM;"`

## 📞 Support

For database issues:
- Check `DATABASE_PRESERVATION_GUIDE.md` in project root
- Check `ANSWER_TO_DATABASE_QUESTION.md` for common questions
- Run `./scripts/backup_database.sh` to create backup
- Run `./scripts/update.sh` for safe updates

## ✅ Summary

**Key Point**: The `db_files/` folder is **separate** from `frontend/` and `backend/`, allowing you to:

1. ✅ Update frontend code without touching backend or database
2. ✅ Update backend code without touching frontend or database
3. ✅ Update both without losing your data
4. ✅ Preserve your database independently from code changes

**Your data is safe as long as you don't delete the `db_files/` folder!**
