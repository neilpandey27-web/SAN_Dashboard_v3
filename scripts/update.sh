#!/bin/bash
# Safe Update Script for OneIT SAN Analytics
# Preserves database while updating code
# Usage: ./scripts/update.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 OneIT SAN Analytics - Safe Update${NC}"
echo "=================================================="

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Step 1: Backup database
echo -e "\n${YELLOW}📦 Step 1: Backing up database...${NC}"
if [ -f "scripts/backup_database.sh" ]; then
    bash scripts/backup_database.sh
else
    echo -e "${YELLOW}⚠️  Backup script not found, skipping backup${NC}"
fi

# Step 2: Stop services
echo -e "\n${YELLOW}🛑 Step 2: Stopping services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose down
    echo -e "${GREEN}✅ Docker services stopped${NC}"
elif command -v pm2 &> /dev/null; then
    pm2 stop all
    echo -e "${GREEN}✅ PM2 services stopped${NC}"
else
    echo -e "${YELLOW}⚠️  No service manager found (docker-compose or pm2)${NC}"
fi

# Step 3: Pull latest code
echo -e "\n${YELLOW}📥 Step 3: Pulling latest code...${NC}"
if [ -d ".git" ]; then
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes!${NC}"
        echo "Stashing changes..."
        git stash
        STASHED=true
    else
        STASHED=false
    fi
    
    # Pull latest
    git pull origin main || git pull origin master
    echo -e "${GREEN}✅ Code updated${NC}"
    
    # Restore stashed changes if any
    if [ "$STASHED" = true ]; then
        echo "Restoring stashed changes..."
        git stash pop
    fi
else
    echo -e "${RED}❌ Not a git repository!${NC}"
    echo "Cannot update via git. Please use manual file replacement."
    exit 1
fi

# Step 4: Update dependencies
echo -e "\n${YELLOW}📦 Step 4: Updating dependencies...${NC}"

# Backend dependencies
if [ -f "backend/requirements.txt" ]; then
    echo "Updating Python dependencies..."
    cd backend
    pip install -r requirements.txt --user --quiet
    cd ..
    echo -e "${GREEN}✅ Python dependencies updated${NC}"
fi

# Frontend dependencies
if [ -f "frontend/package.json" ]; then
    echo "Updating Node dependencies..."
    cd frontend
    npm install --silent
    cd ..
    echo -e "${GREEN}✅ Node dependencies updated${NC}"
fi

# Step 5: Rebuild containers (if using Docker)
if command -v docker-compose &> /dev/null; then
    echo -e "\n${YELLOW}🔨 Step 5: Rebuilding Docker containers...${NC}"
    docker-compose build --quiet
    echo -e "${GREEN}✅ Containers rebuilt${NC}"
fi

# Step 6: Start services
echo -e "\n${YELLOW}🚀 Step 6: Starting services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo -e "${GREEN}✅ Docker services started${NC}"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/api/docs"
elif command -v pm2 &> /dev/null; then
    pm2 start ecosystem.config.cjs
    echo -e "${GREEN}✅ PM2 services started${NC}"
    echo ""
    pm2 list
else
    echo -e "${YELLOW}⚠️  Please start services manually${NC}"
fi

# Step 7: Verify database
echo -e "\n${YELLOW}🔍 Step 7: Verifying database...${NC}"
if [ -f "db_files/storage_insights.db" ]; then
    DB_SIZE=$(du -h db_files/storage_insights.db | cut -f1)
    echo -e "${GREEN}✅ Database found (Size: $DB_SIZE)${NC}"
    
    # Check records
    python3 << EOF
import sqlite3
try:
    conn = sqlite3.connect('db_files/storage_insights.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM storage_systems')
    systems = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM storage_pools')
    pools = cursor.fetchone()[0]
    print(f'   Storage Systems: {systems}')
    print(f'   Storage Pools: {pools}')
    if systems > 0:
        print('   ✅ Database has data!')
    else:
        print('   ⚠️  Database is empty - upload data in Database Management tab')
    conn.close()
except Exception as e:
    print(f'   ⚠️  Could not read database: {e}')
EOF
else
    echo -e "${YELLOW}⚠️  Database not found - will be created on first upload${NC}"
fi

echo -e "\n${GREEN}=================================================="
echo -e "✅ Update Complete!${NC}"
echo ""
echo "💡 Next steps:"
echo "   1. Access the application at http://localhost:3000"
echo "   2. Login with admin/admin123"
echo "   3. Your data should be intact!"
echo ""
echo "📝 Logs:"
echo "   docker-compose logs -f     # Docker logs"
echo "   pm2 logs                   # PM2 logs"
echo ""
