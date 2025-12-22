#!/bin/bash
# Tenant Dropdown Diagnostic Script
# Run this and share the output to debug the issue

echo "═══════════════════════════════════════════════════════"
echo "   OneIT SAN Analytics - Tenant Dropdown Diagnostics"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "1. DOCKER CONTAINER STATUS"
echo "─────────────────────────────────────────────────────"
docker compose ps
echo ""

echo "2. DATABASE - CHECK IF TENANTS EXIST"
echo "─────────────────────────────────────────────────────"
docker compose exec -T db psql -U postgres -d storage_insights -c "SELECT id, name, description FROM tenants ORDER BY name;" 2>&1
echo ""

echo "3. BACKEND - TEST TENANT API ENDPOINT"
echo "─────────────────────────────────────────────────────"
echo "Testing: http://localhost:8000/api/v1/data/tenants/list"
echo "Note: This requires a valid JWT token"
echo ""

echo "4. BACKEND LOGS (Last 30 lines)"
echo "─────────────────────────────────────────────────────"
docker compose logs --tail=30 backend 2>&1
echo ""

echo "5. FRONTEND LOGS (Last 30 lines)"
echo "─────────────────────────────────────────────────────"
docker compose logs --tail=30 frontend 2>&1
echo ""

echo "6. DATABASE CONNECTION TEST"
echo "─────────────────────────────────────────────────────"
docker compose exec -T db psql -U postgres -d storage_insights -c "\dt" 2>&1 | grep -E "(users|tenants|tenant_pool)" || echo "Tables not found"
echo ""

echo "7. CHECK IF ADMIN USER EXISTS"
echo "─────────────────────────────────────────────────────"
docker compose exec -T db psql -U postgres -d storage_insights -c "SELECT email, role, status FROM users WHERE email = 'admin@company.com';" 2>&1
echo ""

echo "═══════════════════════════════════════════════════════"
echo "   BROWSER CONSOLE LOGS NEEDED"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Please also share the following from your browser:"
echo ""
echo "1. Open http://localhost:3000"
echo "2. Login as admin@company.com / admin123"
echo "3. Press F12 to open DevTools"
echo "4. Click 'Console' tab"
echo "5. Refresh the page"
echo "6. Copy ALL lines that start with [TenantFilter]"
echo ""
echo "7. Click 'Network' tab"
echo "8. Filter by 'tenants'"
echo "9. Look for request to: /data/tenants/list"
echo "10. If it exists, click it and share:"
echo "    - Status code (200, 401, 500, etc.)"
echo "    - Response body"
echo ""
echo "═══════════════════════════════════════════════════════"
