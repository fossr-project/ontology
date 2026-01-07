#!/bin/bash

# LimeSurvey Knowledge Graph - Docker Startup Script

set -e

echo "=========================================="
echo "LimeSurvey Knowledge Graph Suite"
echo "Docker Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker from: https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p exports output logs samples ontology rml templates init-scripts

# Check if required files exist
echo -e "${BLUE}🔍 Checking required files...${NC}"

REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile.converter"
    "Dockerfile.builder"
    "Dockerfile.init"
    "main.py"
    "converter_service.py"
    "init_system.py"
    "requirements.txt"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please ensure all required files are in the project directory."
    exit 1
fi

echo -e "${GREEN}✅ All required files found${NC}"
echo ""

# Ask user what to do
echo "What would you like to do?"
echo ""
echo "1) 🚀 Start all services (first time / clean start)"
echo "2) ▶️  Start all services (quick start)"
echo "3) 🔄 Restart all services"
echo "4) ⏹️  Stop all services"
echo "5) 🗑️  Stop and remove all data (DESTRUCTIVE)"
echo "6) 📊 View logs"
echo "7) 🔍 Check service status"
echo "8) ❌ Exit"
echo ""
read -p "Enter your choice [1-8]: " choice

case $choice in
    1)
        echo -e "${BLUE}🚀 Starting all services (fresh build)...${NC}"
        docker compose down -v
        docker compose build --no-cache
        docker compose up -d
        
        echo ""
        echo -e "${GREEN}✅ Services are starting up!${NC}"
        echo ""
        echo "⏳ Waiting for initialization to complete..."
        echo "   This may take 2-3 minutes on first startup..."
        echo ""
        
        # Wait for init service to complete
        echo "📋 Watching initialization logs:"
        docker compose logs -f init-service &
        LOGS_PID=$!
        
        # Wait for init-service to exit
        while docker ps --format '{{.Names}}' | grep -q 'init-service'; do
            sleep 5
        done
        
        # Stop log watching
        kill $LOGS_PID 2>/dev/null || true
        
        echo ""
        echo -e "${GREEN}🎉 System initialization complete!${NC}"
        echo ""
        echo "=========================================="
        echo "Access Points:"
        echo "=========================================="
        echo ""
        echo -e "${BLUE}🌐 LimeSurvey:${NC}      http://localhost:8080"
        echo -e "${BLUE}🗃️  GraphDB:${NC}         http://localhost:7200"
        echo -e "${BLUE}🏗️  Survey Builder:${NC}  http://localhost:5005"
        echo ""
        echo "=========================================="
        echo "Default Credentials:"
        echo "=========================================="
        echo ""
        echo "LimeSurvey:  admin / admin"
        echo "GraphDB:     admin / admin"
        echo ""
        echo -e "${YELLOW}💡 Tip: Run './start-docker.sh' and select option 6 to view logs${NC}"
        echo ""
        ;;
        
    2)
        echo -e "${BLUE}▶️  Starting all services...${NC}"
        docker compose up -d
        echo ""
        echo -e "${GREEN}✅ Services started!${NC}"
        echo ""
        echo "Access points:"
        echo "  - LimeSurvey:      http://localhost:8080"
        echo "  - GraphDB:         http://localhost:7200"
        echo "  - Survey Builder:  http://localhost:5005"
        echo ""
        ;;
        
    3)
        echo -e "${BLUE}🔄 Restarting all services...${NC}"
        docker compose restart
        echo -e "${GREEN}✅ Services restarted!${NC}"
        ;;
        
    4)
        echo -e "${BLUE}⏹️  Stopping all services...${NC}"
        docker compose stop
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
        
    5)
        echo -e "${RED}⚠️  WARNING: This will delete ALL data!${NC}"
        read -p "Are you sure? Type 'yes' to confirm: " confirm
        if [ "$confirm" == "yes" ]; then
            echo -e "${BLUE}🗑️  Stopping and removing all data...${NC}"
            docker compose down -v
            rm -rf exports/* output/* logs/*
            echo -e "${GREEN}✅ All data removed${NC}"
        else
            echo "Cancelled."
        fi
        ;;
        
    6)
        echo -e "${BLUE}📊 Viewing logs (Ctrl+C to exit)...${NC}"
        echo ""
        echo "Which service logs would you like to view?"
        echo "1) All services"
        echo "2) LimeSurvey"
        echo "3) GraphDB"
        echo "4) Semantic Converter"
        echo "5) Survey Builder"
        echo "6) Init Service"
        echo ""
        read -p "Enter your choice [1-6]: " log_choice
        
        case $log_choice in
            1) docker compose logs -f ;;
            2) docker compose logs -f limesurvey ;;
            3) docker compose logs -f graphdb ;;
            4) docker compose logs -f semantic-converter ;;
            5) docker compose logs -f survey-builder ;;
            6) docker compose logs -f init-service ;;
            *) echo "Invalid choice" ;;
        esac
        ;;
        
    7)
        echo -e "${BLUE}🔍 Checking service status...${NC}"
        echo ""
        docker compose ps
        echo ""
        
        # Check health of each service
        echo "Health checks:"
        echo ""
        
        if docker compose ps | grep -q "limesurvey.*Up"; then
            echo -e "  LimeSurvey:       ${GREEN}✅ Running${NC}"
        else
            echo -e "  LimeSurvey:       ${RED}❌ Not running${NC}"
        fi
        
        if docker compose ps | grep -q "graphdb.*Up"; then
            echo -e "  GraphDB:          ${GREEN}✅ Running${NC}"
        else
            echo -e "  GraphDB:          ${RED}❌ Not running${NC}"
        fi
        
        if docker compose ps | grep -q "semantic-converter.*Up"; then
            echo -e "  Semantic Conv.:   ${GREEN}✅ Running${NC}"
        else
            echo -e "  Semantic Conv.:   ${RED}❌ Not running${NC}"
        fi
        
        if docker compose ps | grep -q "survey-builder.*Up"; then
            echo -e "  Survey Builder:   ${GREEN}✅ Running${NC}"
        else
            echo -e "  Survey Builder:   ${RED}❌ Not running${NC}"
        fi
        
        echo ""
        ;;
        
    8)
        echo "Goodbye!"
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac