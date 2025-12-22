#!/bin/bash
# Database Backup Script for OneIT SAN Analytics
# Usage: ./scripts/backup_database.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 OneIT SAN Analytics - Database Backup${NC}"
echo "=================================================="

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$HOME/storage_insights_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="$PROJECT_ROOT/db_files/storage_insights.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}❌ Database not found at: $DB_PATH${NC}"
    echo -e "${YELLOW}💡 Tip: Database is created after first Excel upload${NC}"
    exit 1
fi

# Get database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)

echo -e "\n${YELLOW}📊 Database Info:${NC}"
echo "  Location: $DB_PATH"
echo "  Size: $DB_SIZE"
echo "  Backup to: $BACKUP_DIR"

# Create backup
BACKUP_FILE="$BACKUP_DIR/storage_insights_${TIMESTAMP}.db"
cp "$DB_PATH" "$BACKUP_FILE"

if [ -f "$BACKUP_FILE" ]; then
    echo -e "\n${GREEN}✅ Database backed up successfully!${NC}"
    echo "  Backup file: $BACKUP_FILE"
    echo "  Size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo -e "\n${RED}❌ Backup failed!${NC}"
    exit 1
fi

# Count records in database
echo -e "\n${YELLOW}📈 Database Statistics:${NC}"
python3 << EOF
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM storage_systems')
    systems = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM storage_pools')
    pools = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM capacity_hosts')
    hosts = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM capacity_volumes')
    volumes = cursor.fetchone()[0]
    
    print(f'  Storage Systems: {systems}')
    print(f'  Storage Pools: {pools}')
    print(f'  Capacity Hosts: {hosts}')
    print(f'  Capacity Volumes: {volumes}')
    
    conn.close()
except Exception as e:
    print(f'  Error reading database: {e}')
EOF

# Clean up old backups (keep last 10)
echo -e "\n${YELLOW}🧹 Cleaning old backups...${NC}"
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/storage_insights_*.db 2>/dev/null | wc -l)
echo "  Current backups: $BACKUP_COUNT"

if [ "$BACKUP_COUNT" -gt 10 ]; then
    REMOVE_COUNT=$((BACKUP_COUNT - 10))
    echo "  Removing $REMOVE_COUNT oldest backup(s)..."
    ls -t "$BACKUP_DIR"/storage_insights_*.db | tail -n +11 | xargs rm -f
    echo -e "  ${GREEN}✅ Kept 10 most recent backups${NC}"
else
    echo "  ✅ No cleanup needed (keeping all $BACKUP_COUNT backups)"
fi

# List recent backups
echo -e "\n${YELLOW}📂 Recent Backups:${NC}"
ls -lht "$BACKUP_DIR"/storage_insights_*.db 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ")"}'

echo -e "\n${GREEN}=================================================="
echo -e "✅ Backup Complete!${NC}"
echo ""
echo "💡 Restore command:"
echo "   cp $BACKUP_FILE backend/storage_insights.db"
echo ""
