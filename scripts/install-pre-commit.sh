#!/bin/bash
# =============================================================================
# ARIZONA LAVKA MARKETPLACE - INSTALL PRE-COMMIT HOOKS
# =============================================================================
# This script installs pre-commit hooks for the project
# Usage: ./scripts/install-pre-commit.sh
# =============================================================================

set -e

echo "🔧 Installing pre-commit hooks for Arizona Lavka Marketplace..."

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.12+ first."
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo "✅ Found Python: $($PYTHON_CMD --version)"

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    $PYTHON_CMD -m pip install pre-commit
fi

echo "✅ Found pre-commit: $(pre-commit --version)"

# Install pre-commit hooks
echo "🔗 Installing git hooks..."
pre-commit install

# Install pre-commit hooks for all repos (optional)
# pre-commit install --install-hooks

echo ""
echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "📝 To run pre-commit manually:"
echo "   pre-commit run --all-files"
echo ""
echo "📝 To run pre-commit on all files with verbose output:"
echo "   pre-commit run --all-files --verbose"
echo ""
echo "📝 To run a specific hook:"
echo "   pre-commit run ruff --all-files"
echo ""
echo "📝 To uninstall pre-commit:"
echo "   pre-commit uninstall"
echo ""
