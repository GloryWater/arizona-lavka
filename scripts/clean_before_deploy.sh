#!/bin/bash
# 🧹 Script for cleaning project before deployment
# Usage: ./scripts/clean_before_deploy.sh

set -e

echo "🧹 Cleaning project before deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${YELLOW}Cleaning Python artifacts...${NC}"
find "$ROOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$ROOT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type f -name "*.log" -delete 2>/dev/null || true

echo -e "${YELLOW}Cleaning Node.js artifacts...${NC}"
rm -rf "$ROOT_DIR/frontend/node_modules" 2>/dev/null || true
rm -rf "$ROOT_DIR/frontend/dist" 2>/dev/null || true

echo -e "${YELLOW}Cleaning test results...${NC}"
rm -rf "$ROOT_DIR/load_tests/results" 2>/dev/null || true
rm -rf "$ROOT_DIR/load_tests/__pycache__" 2>/dev/null || true

echo -e "${YELLOW}Cleaning temporary files...${NC}"
rm -rf "$ROOT_DIR/-p" 2>/dev/null || true
rm -rf "$ROOT_DIR/trash_arizonalavka" 2>/dev/null || true
rm -rf "$ROOT_DIR/backend/logs" 2>/dev/null || true

echo -e "${YELLOW}Removing local environment files...${NC}"
rm -f "$ROOT_DIR/frontend/.env.local" 2>/dev/null || true
rm -f "$ROOT_DIR/backend/.env" 2>/dev/null || true
rm -f "$ROOT_DIR/backend/.python-version" 2>/dev/null || true

echo -e "${GREEN}✅ Cleaning completed!${NC}"
echo ""
echo "📁 Files ready for deployment:"
echo "  - backend/"
echo "  - frontend/"
echo "  - data/"
echo "  - load_tests/"
echo "  - docker-compose.yml"
echo "  - .env.example"
echo ""
echo "⚠️  Don't forget to:"
echo "  1. Create .env file from .env.example"
echo "  2. Set JWT_SECRET_KEY to a secure random value"
echo "  3. Set POSTGRES_PASSWORD to a secure random value"
echo "  4. Update CORS_ORIGINS for production"
