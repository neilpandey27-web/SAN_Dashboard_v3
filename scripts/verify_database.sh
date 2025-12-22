#!/bin/bash
# Verify Database Setup
# Run this after starting services to check database status

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 OneIT SAN Analytics - Database Verification${NC}"
echo "=================================================="

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="$PROJECT_ROOT/db_files/storage_insights.db"

echo -e "\n${YELLOW}📁 Checking database location...${NC}"
echo "Expected path: $DB_PATH"

# Check if db_files folder exists
if [ ! -d "$PROJECT_ROOT/db_files" ]; then
    echo -e "${RED}❌ db_files/ folder not found!${NC}"
    echo "   This should not happen. Package may be corrupted."
    exit 1
else
    echo -e "${GREEN}✅ db_files/ folder exists${NC}"
fi

# Check if database file exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "\n${YELLOW}⚠️  Database file NOT found${NC}"
    echo ""
    echo "This is NORMAL for a fresh installation!"
    echo ""
    echo "The database will be created when:"
    echo "  1. You start the backend service (docker-compose up -d)"
    echo "  2. The application initializes"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Run: docker-compose up -d"
    echo "  2. Wait 10 seconds"
    echo "  3. Run this script again"
    echo "  4. Upload your Excel file in the app"
    echo ""
    exit 0
fi

# Database exists - check details
echo -e "\n${GREEN}✅ Database file found!${NC}"
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "   Location: $DB_PATH"
echo "   Size: $DB_SIZE"

# Check if database is accessible
echo -e "\n${YELLOW}🔍 Checking database contents...${NC}"

python3 << EOF
import sqlite3
import sys

try:
    conn = sqlite3.connect('$DB_PATH')
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f'   Tables found: {len(tables)}')
    
    # Check key tables
    cursor.execute('SELECT COUNT(*) FROM storage_systems')
    systems = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM storage_pools')
    pools = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM capacity_hosts')
    hosts = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users')
    users = cursor.fetchone()[0]
    
    print(f'\n   📊 Data Summary:')
    print(f'   - Storage Systems: {systems}')
    print(f'   - Storage Pools: {pools}')
    print(f'   - Capacity Hosts: {hosts}')
    print(f'   - User Accounts: {users}')
    
    if systems == 0 and pools == 0:
        print(f'\n   ⚠️  Database is empty - no storage data uploaded yet')
        print(f'   💡 Go to Database Management tab and upload your Excel file')
    else:
        print(f'\n   ✅ Database has data!')
    
    conn.close()
    sys.exit(0)
    
except sqlite3.Error as e:
    print(f'   ❌ Error reading database: {e}')
    sys.exit(1)
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}=================================================="
    echo -e "✅ Database is working correctly!${NC}"
    echo ""
else
    echo -e "\n${RED}=================================================="
    echo -e "❌ Database error detected${NC}"
    echo ""
    echo "Possible solutions:"
    echo "  1. Delete database: rm db_files/storage_insights.db"
    echo "  2. Restart services: docker-compose restart"
    echo "  3. Check logs: docker-compose logs backend"
fi

echo ""
