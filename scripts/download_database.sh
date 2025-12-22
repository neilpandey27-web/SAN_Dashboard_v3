#!/bin/bash

#==============================================================================
# Download Standalone Database File
#==============================================================================
# Downloads the pre-configured storage_insights.db file
# Usage: bash scripts/download_database.sh [destination]
#==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DOWNLOAD_URL="https://www.genspark.ai/api/files/s/ciq0C1T9"
TEMP_FILE="/tmp/storage_database.tar.gz"
DEFAULT_DEST="./db_files/storage_insights.db"

# Get destination from argument or use default
DESTINATION="${1:-$DEFAULT_DEST}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Database Download Utility${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if curl or wget is available
if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -L -o"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -O"
else
    echo -e "${RED}Error: Neither curl nor wget is available${NC}"
    echo "Please install curl or wget to continue"
    exit 1
fi

# Download
echo -e "${YELLOW}Downloading database...${NC}"
echo "URL: $DOWNLOAD_URL"
$DOWNLOAD_CMD "$TEMP_FILE" "$DOWNLOAD_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}Download failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Download complete${NC}"
echo ""

# Extract
echo -e "${YELLOW}Extracting database...${NC}"
EXTRACT_DIR="/tmp/storage_db_extract"
rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$TEMP_FILE" -C "$EXTRACT_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Extraction failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Extraction complete${NC}"
echo ""

# Copy to destination
echo -e "${YELLOW}Installing database...${NC}"
DEST_DIR=$(dirname "$DESTINATION")
mkdir -p "$DEST_DIR"

# Backup existing database if it exists
if [ -f "$DESTINATION" ]; then
    BACKUP_FILE="${DESTINATION}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}⚠ Backing up existing database to:${NC}"
    echo "   $BACKUP_FILE"
    cp "$DESTINATION" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup created${NC}"
    echo ""
fi

# Copy new database
cp "$EXTRACT_DIR/storage_insights.db" "$DESTINATION"
chmod 644 "$DESTINATION"

if [ $? -ne 0 ]; then
    echo -e "${RED}Installation failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database installed${NC}"
echo ""

# Verify
echo -e "${YELLOW}Verifying database...${NC}"
if command -v sqlite3 &> /dev/null; then
    sqlite3 "$DESTINATION" "SELECT COUNT(*) FROM sqlite_master WHERE type='table'" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        TABLE_COUNT=$(sqlite3 "$DESTINATION" "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        echo -e "${GREEN}✓ Database verified (${TABLE_COUNT} tables)${NC}"
    else
        echo -e "${YELLOW}⚠ Could not verify database${NC}"
    fi
else
    echo -e "${YELLOW}⚠ sqlite3 not found, skipping verification${NC}"
fi

# Show README if extracted
if [ -f "$EXTRACT_DIR/README.md" ]; then
    echo ""
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}README available at:${NC}"
    echo "   $EXTRACT_DIR/README.md"
    echo ""
    echo -e "${YELLOW}View with: cat $EXTRACT_DIR/README.md${NC}"
fi

# Cleanup
rm -f "$TEMP_FILE"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Database Location: $DESTINATION"
echo "Database Size:     $(du -h "$DESTINATION" | cut -f1)"
echo ""
echo "Default Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Next Steps:"
echo "  1. Start your application"
echo "  2. Login with admin/admin123"
echo "  3. Upload your Excel files"
echo "  4. Change the admin password!"
echo ""
echo -e "${YELLOW}⚠ Important: Change the default password immediately!${NC}"
echo ""
