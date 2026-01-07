# 📊 LimeSurvey Knowledge Graph - Docker Setup

Integrated system for managing LimeSurvey questionnaires with GraphDB knowledge graph and Survey Builder interface.

---

## 🏗️ Architecture

The project consists of 4 Docker services:

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                      │
│                  survey-network                      │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  LimeSurvey  │  │   GraphDB    │  │  MySQL   │  │
│  │  Port: 8080  │  │  Port: 7200  │  │Port: 3306│  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│         ↑                  ↑                         │
│         │                  │                         │
│         └──────────────────┴─────────────┐          │
│                                           │          │
│                                  ┌────────────────┐ │
│                                  │ Survey Builder │ │
│                                  │  Port: 5001    │ │
│                                  └────────────────┘ │
└─────────────────────────────────────────────────────┘
         │                │                │
         ↓                ↓                ↓
   localhost:8080  localhost:7200   localhost:5001
```

---

## 📋 Prerequisites

- **Docker Desktop** for macOS/Windows or **Docker Engine** for Linux
- **Docker Compose** V2 (included in Docker Desktop)
- Minimum 4GB RAM available
- Minimum 10GB disk space

### Verify Installation

```bash
# Check Docker
docker --version
# Output: Docker version 24.x.x or higher

# Check Docker Compose
docker compose version
# Output: Docker Compose version v2.x.x or higher
```

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd limesurvey-knowledge-graph

# Verify pyrml is present
ls pyrml/
# Should show: __init__.py, pyrml_api.py, ...
```

### 2. Start All Services

```bash
# Build and start all services
docker compose up -d

# Or force build without cache
docker compose build --no-cache
docker compose up -d
```

### 3. Verify Services

```bash
# Check service status
docker compose ps

# All should be "Up (healthy)"
```

### 4. Access Applications

**Survey Builder:**
- URL: http://localhost:5001/surveybuilder
- Main interface for survey management

**LimeSurvey:**
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin`

**GraphDB Workbench:**
- URL: http://localhost:7200
- Username: `admin`
- Password: `admin`

---

## ⚙️ Survey Builder Configuration

### 🔑 Correct URLs to Use

**⚠️ IMPORTANT:** When using Survey Builder, you MUST use Docker service names, not `localhost`:

#### ✅ Correct URLs (Container-to-Container):

```
LimeSurvey URL: http://limesurvey:8080/index.php/admin/remotecontrol
GraphDB URL: http://graphdb:7200
```

#### ❌ Wrong URLs (Will Not Work):

```
LimeSurvey URL: http://localhost:8080/...  ❌
GraphDB URL: http://localhost:7200  ❌
```

### 📝 Complete Configuration Example

When configuring Survey Builder, use these settings:

**LimeSurvey Connection:**
```
URL: http://limesurvey:8080/index.php/admin/remotecontrol
Username: admin
Password: admin
```

**GraphDB Connection:**
```
URL: http://graphdb:7200
Repository: test_repo
Username: admin
Password: admin
```

---

## 🔍 Why Use Service Names?

### Docker Networking Explained

```
┌─────────────────────────────────────────────────────┐
│ Inside survey-builder container:                     │
│                                                       │
│ ✅ http://limesurvey:8080   → Works (DNS resolved)   │
│ ✅ http://graphdb:7200       → Works (DNS resolved)   │
│ ❌ http://localhost:8080     → Fails (only container)│
│ ❌ http://localhost:7200     → Fails (only container)│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ From your browser (host machine):                    │
│                                                       │
│ ✅ http://localhost:8080     → Works (port mapped)   │
│ ✅ http://localhost:7200     → Works (port mapped)   │
│ ✅ http://localhost:5001     → Works (port mapped)   │
└─────────────────────────────────────────────────────┘
```

**Key Point:** Survey Builder runs **inside a container**, so it must use Docker service names (`limesurvey`, `graphdb`) to connect to other containers.

---

## 📁 Project Structure

```
limesurvey-knowledge-graph/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile.builder          # Survey Builder container
├── requirements.txt            # Python dependencies
├── app.py                      # Flask application
├── graphdb_client.py          # GraphDB integration
├── limesurvey_api.py          # LimeSurvey API client
├── utils.py                   # Utility functions
├── pyrml/                     # Local pyrml module
│   ├── __init__.py
│   ├── pyrml_api.py
│   ├── pyrml_core.py
│   └── ...
├── templates/                 # HTML templates
│   ├── home.html
│   ├── surveybuilder.html
│   └── ...
├── static/                    # Static files
│   ├── css/
│   ├── js/
│   └── images/
└── outputs/                   # Generated files
```

---

## 🐳 Docker Services

### Service Overview

| Service | Port | Description |
|---------|------|-------------|
| **mysql** | 3306 | MySQL database for LimeSurvey |
| **limesurvey** | 8080 | Survey management platform |
| **graphdb** | 7200 | RDF knowledge graph database |
| **survey-builder** | 5001 | Flask web application |

### Environment Variables

All services are pre-configured with default values in `docker-compose.yml`:

```yaml
# LimeSurvey
LIMESURVEY_URL: http://limesurvey:8080/index.php/admin/remotecontrol
LIMESURVEY_USERNAME: admin
LIMESURVEY_PASSWORD: admin

# GraphDB
GRAPHDB_URL: http://graphdb:7200
GRAPHDB_REPOSITORY: test_repo
GRAPHDB_USERNAME: admin
GRAPHDB_PASSWORD: admin

# Flask
FLASK_HOST: 0.0.0.0
FLASK_PORT: 5005
FLASK_DEBUG: "False"
```

---

## 🛠️ Common Commands

### Service Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart a specific service
docker compose restart survey-builder

# View logs
docker compose logs -f survey-builder
docker compose logs -f limesurvey
docker compose logs -f graphdb

# Check service status
docker compose ps
```

### Development

```bash
# Rebuild after code changes
docker compose build survey-builder
docker compose restart survey-builder

# Force rebuild without cache
docker compose build --no-cache survey-builder

# Access container shell
docker compose exec survey-builder bash
docker compose exec limesurvey bash
docker compose exec graphdb bash
```

### Maintenance

```bash
# View container logs
docker compose logs --tail=100 survey-builder

# Remove all containers and volumes (CAUTION: data loss!)
docker compose down -v

# Restart all services
docker compose restart

# Update images
docker compose pull
docker compose up -d
```

---

## 🔧 Troubleshooting

### Service Not Starting

```bash
# Check logs for errors
docker compose logs survey-builder

# Check if ports are already in use
lsof -i :5001
lsof -i :8080
lsof -i :7200

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Connection Errors

**Problem:** "Connection refused" when connecting to LimeSurvey/GraphDB

**Solution:** Make sure you're using service names:
- ✅ `http://limesurvey:8080`
- ✅ `http://graphdb:7200`
- ❌ NOT `http://localhost:8080`

### Template Errors (macOS)

**Problem:** `OSError: [Errno 35] Resource deadlock avoided`

**Solution:** Already fixed in `docker-compose.yml` - templates are copied into container, not mounted.

### Missing Dependencies

```bash
# Check if pyrml is present
docker compose exec survey-builder ls -la /app/pyrml/

# Verify Python packages
docker compose exec survey-builder pip list | grep -E "lark|iribaker|unidecode"
```

### Memory Issues

```bash
# Increase Docker Desktop memory limit:
# Docker Desktop → Settings → Resources → Memory
# Recommended: 4GB minimum, 8GB optimal

# Check current resource usage
docker stats
```

---

## 📊 Data Persistence

### Volumes

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep limesurvey

# Backup a volume
docker run --rm -v limesurvey-knowledge-graph_graphdb_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/graphdb-backup.tar.gz /data

# Restore a volume
docker run --rm -v limesurvey-knowledge-graph_graphdb_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/graphdb-backup.tar.gz -C /
```

### Volume List

- `mysql_data` - MySQL database
- `limesurvey_upload` - LimeSurvey uploads
- `limesurvey_config` - LimeSurvey configuration
- `graphdb_data` - GraphDB repositories
- `builder_logs` - Survey Builder logs

---

## 🔐 Security Notes

### Default Credentials

**⚠️ Change these in production!**

```yaml
# LimeSurvey
Username: admin
Password: admin

# GraphDB
Username: admin
Password: admin

# MySQL
Username: limesurvey
Password: limesurvey
Root Password: rootpassword
```

### Production Recommendations

1. **Change all default passwords**
2. **Use environment variable files** (`.env`)
3. **Enable HTTPS** with reverse proxy
4. **Restrict network access**
5. **Regular backups**
6. **Update images regularly**

---

## 🚀 Production Deployment

### Using .env File

Create `.env` file:

```bash
# LimeSurvey
LIMESURVEY_ADMIN_PASSWORD=your_secure_password

# GraphDB
GRAPHDB_PASSWORD=your_secure_password

# MySQL
MYSQL_PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_secure_root_password
```

Reference in `docker-compose.yml`:

```yaml
environment:
  LIMESURVEY_PASSWORD: ${LIMESURVEY_ADMIN_PASSWORD}
```

### Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/surveybuilder

server {
    listen 80;
    server_name surveybuilder.example.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📝 Development Notes

### Modifying Templates/Static Files

After modifying templates or static files, rebuild:

```bash
docker compose build survey-builder
docker compose restart survey-builder
```

**Note:** Templates and static files are copied into the container (not mounted as volumes) to avoid macOS file locking issues.

### Adding Python Dependencies

1. Add package to `requirements.txt`:
   ```
   new-package==1.0.0
   ```

2. Rebuild container:
   ```bash
   docker compose build --no-cache survey-builder
   docker compose restart survey-builder
   ```

### Debugging

```bash
# Access Python shell in container
docker compose exec survey-builder python

# Run tests
docker compose exec survey-builder python -m pytest

# Check app configuration
docker compose exec survey-builder python -c "
import os
print('LIMESURVEY_URL:', os.getenv('LIMESURVEY_URL'))
print('GRAPHDB_URL:', os.getenv('GRAPHDB_URL'))
"
```

---

## 🧪 Testing Connections

### Test LimeSurvey API

```bash
docker compose exec survey-builder python << 'EOF'
import requests
import json

url = "http://limesurvey:8080/index.php/admin/remotecontrol"
payload = {
    "method": "get_session_key",
    "params": ["admin", "admin"],
    "id": 1
}

response = requests.post(url, json=payload)
print("LimeSurvey Response:", response.json())
EOF
```

### Test GraphDB

```bash
docker compose exec survey-builder curl http://graphdb:7200/repositories
```

---

## 📚 Additional Resources

### Documentation

- [LimeSurvey Manual](https://manual.limesurvey.org/)
- [GraphDB Documentation](https://graphdb.ontotext.com/documentation/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

### API Endpoints

**Survey Builder:**
- `GET /` - Home page
- `GET /surveybuilder` - Survey Builder interface
- `POST /api/*` - Various API endpoints

**LimeSurvey RemoteControl:**
- Endpoint: `http://limesurvey:8080/index.php/admin/remotecontrol`
- [API Documentation](https://manual.limesurvey.org/RemoteControl_2_API)

**GraphDB SPARQL:**
- Endpoint: `http://graphdb:7200/repositories/{repo}`
- Query: `http://graphdb:7200/repositories/{repo}/statements`

---

## 🐛 Known Issues

### macOS File Locking

**Issue:** Volume mounts cause deadlock on macOS
**Status:** ✅ Fixed - templates/static copied into container

### Port Conflicts

**Issue:** Ports 8080, 7200, or 5001 already in use
**Solution:** Stop conflicting services or change ports in `docker-compose.yml`

```yaml
ports:
  - "8081:8080"  # Use 8081 instead of 8080
```

---

## ⚡ Quick Reference Card

### Essential URLs

```
Survey Builder:  http://localhost:5001/surveybuilder
LimeSurvey:      http://localhost:8080
GraphDB:         http://localhost:7200
```

### Essential Credentials

```
All services:
Username: admin
Password: admin
```

### Essential Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f survey-builder

# Rebuild
docker compose build --no-cache survey-builder
```

### Configuration URLs (Survey Builder Form)

```
LimeSurvey: http://limesurvey:8080/index.php/admin/remotecontrol
GraphDB:    http://graphdb:7200
Repository: test_repo
```

---

**🎉 Happy Surveying!**
