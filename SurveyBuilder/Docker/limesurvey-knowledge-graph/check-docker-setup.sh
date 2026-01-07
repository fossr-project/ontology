#!/bin/bash

# Script per verificare che tutti i file Docker siano presenti

echo "=========================================="
echo "Docker Setup Verification"
echo "=========================================="
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Contatori
FOUND=0
MISSING=0

# Array di file richiesti
declare -A REQUIRED_FILES=(
    ["docker-compose.yml"]="Docker Compose configuration"
    ["Dockerfile.converter"]="Semantic Converter Docker image"
    ["Dockerfile.builder"]="Survey Builder Docker image"
    ["Dockerfile.init"]="Initialization service Docker image"
    [".dockerignore"]="Docker ignore file"
    ["start-docker.sh"]="Docker start script"
    ["main.py"]="Main application code"
    ["converter_service.py"]="Converter service wrapper"
    ["init_system.py"]="System initialization script"
    ["requirements.txt"]="Python dependencies"
)

# Array di directory richieste
declare -A REQUIRED_DIRS=(
    ["rml"]="RML mapping files"
    ["ontology"]="Ontology files"
    ["templates"]="HTML templates"
    ["samples"]="Sample data (optional)"
)

echo "Checking required files..."
echo ""

for file in "${!REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file - ${REQUIRED_FILES[$file]}"
        ((FOUND++))
    else
        echo -e "${RED}✗${NC} $file - ${REQUIRED_FILES[$file]} ${RED}(MISSING)${NC}"
        ((MISSING++))
    fi
done

echo ""
echo "Checking required directories..."
echo ""

for dir in "${!REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo -e "${GREEN}✓${NC} $dir/ - ${REQUIRED_DIRS[$dir]} ($file_count files)"
        ((FOUND++))
    else
        echo -e "${YELLOW}⚠${NC} $dir/ - ${REQUIRED_DIRS[$dir]} ${YELLOW}(MISSING - will be created)${NC}"
    fi
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✓ All required files present!${NC}"
    echo ""
    echo "You can now run:"
    echo "  chmod +x start-docker.sh"
    echo "  ./start-docker.sh"
    echo ""
else
    echo -e "${RED}✗ Missing $MISSING required file(s)${NC}"
    echo ""
    echo "Please create the missing files before proceeding."
    echo ""
fi

# Check specific file contents
echo "=========================================="
echo "Additional Checks"
echo "=========================================="
echo ""

# Check if start-docker.sh is executable
if [ -f "start-docker.sh" ]; then
    if [ -x "start-docker.sh" ]; then
        echo -e "${GREEN}✓${NC} start-docker.sh is executable"
    else
        echo -e "${YELLOW}⚠${NC} start-docker.sh is not executable"
        echo "  Run: chmod +x start-docker.sh"
    fi
fi

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed ($(docker --version))"
else
    echo -e "${RED}✗${NC} Docker is NOT installed"
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed ($(docker-compose --version))"
elif docker compose version &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose (plugin) is installed ($(docker compose version))"
else
    echo -e "${RED}✗${NC} Docker Compose is NOT installed"
fi

echo ""

# Show file structure
echo "=========================================="
echo "Current Directory Structure"
echo "=========================================="
echo ""

if command -v tree &> /dev/null; then
    tree -L 2 -I '__pycache__|*.pyc|.git' --dirsfirst
else
    ls -la
    echo ""
    echo "(Install 'tree' for better directory visualization)"
fi

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""

if [ $MISSING -eq 0 ]; then
    echo "1. Review docker-compose.yml configuration"
    echo "2. Ensure your Flask app file is correctly referenced in Dockerfile.builder"
    echo "3. Run: ./start-docker.sh"
    echo "4. Select option 1 (Start all services - first time)"
    echo "5. Wait 2-3 minutes for initialization"
    echo "6. Access services at:"
    echo "   - LimeSurvey:      http://localhost:8080"
    echo "   - GraphDB:         http://localhost:7200"
    echo "   - Survey Builder:  http://localhost:5005"
else
    echo "1. Create the missing files listed above"
    echo "2. Run this script again to verify"
    echo "3. Refer to DOCKER-SETUP.md for detailed instructions"
fi

echo ""