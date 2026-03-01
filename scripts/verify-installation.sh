#!/bin/bash
# 🤖 Self-Healing CI Installation Verification Script
#
# This script verifies that all components of the self-healing CI pipeline
# are properly installed and configured.
#
# Usage: bash verify-installation.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR" && git rev-parse --show-toplevel)"

echo "🔍 Verifying Self-Healing CI Installation..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

status_ok=0
status_warnings=0
status_errors=0

# Helper functions
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$REPO_ROOT/$file" ]; then
        echo -e "${GREEN}✅${NC} Found: $description"
        ((status_ok++))
    else
        echo -e "${RED}❌${NC} Missing: $description ($file)"
        ((status_errors++))
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$REPO_ROOT/$dir" ]; then
        echo -e "${GREEN}✅${NC} Found: $description"
        ((status_ok++))
    else
        echo -e "${YELLOW}⚠️${NC}  Missing: $description ($dir)"
        ((status_warnings++))
    fi
}

# Check workflow file
echo "📋 Checking Workflow Files..."
check_file ".github/workflows/self-healing-ci.yml" "Main CI workflow"
echo ""

# Check documentation
echo "📚 Checking Documentation..."
check_file "SELF_HEALING_CI_QUICK_START.md" "Quick start guide"
check_file "SELF_HEALING_CI_SETUP.md" "Setup guide"
check_file ".github/workflows/SELF_HEALING_CI.md" "Detailed documentation"
echo ""

# Check scripts
echo "🐍 Checking Support Scripts..."
check_file "scripts/incident_analyzer.py" "Incident analyzer script"
check_file "scripts/flaky_test_healer.py" "Flaky test healer script"
echo ""

# Check schemas
echo "📋 Checking JSON Schemas..."
check_file "schemas/ci-metrics.schema.json" "CI metrics JSON schema"
echo ""

# Check directories
echo "📁 Checking Directories..."
check_directory ".github/metrics" "Metrics storage directory"
echo ""

# Check workflow syntax
echo "🔧 Checking Workflow Syntax..."
if command -v gh &> /dev/null; then
    if gh workflow validate .github/workflows/self-healing-ci.yml &> /dev/null; then
        echo -e "${GREEN}✅${NC} Workflow YAML syntax is valid"
        ((status_ok++))
    else
        echo -e "${RED}❌${NC} Workflow YAML syntax error"
        ((status_errors++))
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Can't validate workflow (gh CLI not installed)"
    ((status_warnings++))
fi
echo ""

# Check Python scripts syntax
echo "🐍 Checking Python Scripts..."
if command -v python3 &> /dev/null; then
    for script in scripts/incident_analyzer.py scripts/flaky_test_healer.py; do
        if python3 -m py_compile "$REPO_ROOT/$script" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} Valid Python: $(basename $script)"
            ((status_ok++))
        else
            echo -e "${YELLOW}⚠️${NC}  Syntax issue: $(basename $script)"
            ((status_warnings++))
        fi
    done
else
    echo -e "${YELLOW}⚠️${NC}  Python 3 not found (needed for advanced features)"
    ((status_warnings++))
fi
echo ""

# Check git configuration
echo "🔐 Checking Git Configuration..."
if git config user.name &> /dev/null && git config user.email &> /dev/null; then
    echo -e "${GREEN}✅${NC} Git user configured"
    ((status_ok++))
else
    echo -e "${YELLOW}⚠️${NC}  Git user not configured (needed for metrics commits)"
    ((status_warnings++))
fi
echo ""

# Check write permissions simulation
echo "🔐 Checking Permissions..."
if [ -w "$REPO_ROOT/.github" ]; then
    echo -e "${GREEN}✅${NC} Write permission to .github directory"
    ((status_ok++))
else
    echo -e "${RED}❌${NC} No write permission to .github directory"
    ((status_errors++))
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "📊 Installation Verification Summary"
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Passed:${NC} $status_ok checks"
echo -e "${YELLOW}⚠️  Warnings:${NC} $status_warnings checks"
echo -e "${RED}❌ Failed:${NC} $status_errors checks"
echo ""

if [ $status_errors -eq 0 ]; then
    if [ $status_warnings -eq 0 ]; then
        echo -e "${GREEN}🎉 Installation verified successfully!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Commit changes: git add . && git commit -m '🤖 Add self-healing CI'"
        echo "2. Push to repository: git push"
        echo "3. Create a PR or push to main to trigger the workflow"
        echo "4. Monitor in GitHub Actions tab"
        echo "5. View metrics dashboard: open .github/metrics/dashboard.html"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Installation mostly complete with some warnings${NC}"
        echo ""
        echo "You can still use the pipeline, but some optional features may not work."
        echo "Consider installing:"
        echo "- Python 3 (for advanced analysis scripts)"
        echo "- GitHub CLI (for workflow validation)"
        exit 0
    fi
else
    echo -e "${RED}❌ Installation verification found issues${NC}"
    echo ""
    echo "Please review the missing files listed above and ensure:"
    echo "1. All workflow files are in place"
    echo "2. Scripts directory exists with required Python files"
    echo "3. Proper file permissions are set"
    echo ""
    echo "Run this script again after fixing issues"
    exit 1
fi
