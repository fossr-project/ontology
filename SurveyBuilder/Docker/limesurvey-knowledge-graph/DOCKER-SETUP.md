# Docker Setup Guide

Complete Docker setup for LimeSurvey Knowledge Graph Suite.

## 📋 Prerequisites

- **Docker** 20.10+ 
- **Docker Compose** 2.0+
- **8GB RAM** minimum (12GB recommended)
- **10GB free disk space**

### Install Docker

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Windows/Mac:**
Download from [Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/yourusername/limesurvey-knowledge-graph.git
cd limesurvey-knowledge-graph
```

### 2. Make Start Script Executable

```bash
chmod +x start-docker.sh
```

### 3. Start All Services

```bash
./start-docker.sh
```

Select option **1** (Start all services - first time)

### 4. Wait for Initialization

The first startup takes 2-3 minutes. The script will show initialization logs.

### 5. Access Services

Once complete, access:

- **LimeSurvey**: http://localhost:8080
- **GraphDB**: http://localhost:7200  
- **Survey Builder**: http://localhost:5005

**Default credentials**: `admin` / `admin` for all services

---

## 📦 Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **limesurvey** | 8080 | Survey management platform |
| **mysql** | 3306 | Database for LimeSurvey |
| **graphdb** | 7200 | RDF triple store |
| **semantic-converter** | 8000 | Export & conversion service |
| **survey-builder** | 5005 | Web interface for building surveys |
| **init-service** | - | One-time initialization (exits after setup) |

---

## 🛠️ Management Commands

The `start-docker.sh` script provides an interactive menu:

```bash
./start-docker.sh
```

**Options:**

1. **🚀 Start (first time)** - Clean start with rebuild
2. **▶️ Start (quick)** - Start without rebuild
3. **🔄 Restart** - Restart all services
4. **⏹️ Stop** - Stop all services (data persists)
5. **🗑️ Remove all data** - Complete cleanup (destructive!)
6. **📊 View logs** - Follow service logs
7. **🔍 Check status** - See service health
8. **❌ Exit**

### Manual Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# View logs
docker-compose logs -f [service-name]

# Check status
docker-compose ps

# Restart a service
docker-compose restart [service-name]

# Stop and remove everything
docker-compose down -v
```

---

## 📁 Directory Structure

```
limesurvey-knowledge-graph/
├── docker-compose.yml           # Service orchestration
├── Dockerfile.converter         # Semantic Converter image
├── Dockerfile.builder          # Survey Builder image
├── Dockerfile.init             # Initialization image
├── start-docker.sh             # Interactive start script
│
├── main.py                     # Core application logic
├── converter_service.py        # Converter API service
├── init_system.py              # Initialization script
├── requirements.txt            # Python dependencies
│
├── rml/                        # RML mapping files
│   ├── RMLGroup2.ttl
│   ├── RMLQuestion.ttl
│   └── RMLQuestionFromJson.ttl
│
├── ontology/
│   └── limesurvey.ttl         # LimeSurvey ontology
│
├── templates/
│   └── index.html             # Survey Builder UI
│
├── samples/                   # Sample data
│   ├── survey1.lss
│   ├── survey2.lss
│   └── *.csv
│
├── exports/                   # Generated exports (volume)
├── output/                    # Generated TTL files (volume)
└── logs/                      # Service logs (volume)
```

---

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to change default settings:

**LimeSurvey:**
```yaml
environment:
  ADMIN_USER: admin
  ADMIN_PASSWORD: admin
  ADMIN_EMAIL: admin@example.com
```

**GraphDB:**
```yaml
environment:
  GDB_HEAP_SIZE: 2G
  GDB_MIN_MEM: 1G
  GDB_MAX_MEM: 2G
```

**Application Services:**
```yaml
environment:
  GRAPHDB_REPOSITORY: test_repo
  FLASK_DEBUG: "False"
```

### Port Mapping

Change ports in `docker-compose.yml`:

```yaml
services:
  limesurvey:
    ports:
      - "8080:8080"  # Change left number (host port)
  
  graphdb:
    ports:
      - "7200:7200"
  
  survey-builder:
    ports:
      - "5005:5005"
```

---

## 📊 Data Persistence

Data is stored in Docker volumes:

| Volume | Purpose |
|--------|---------|
| `mysql_data` | LimeSurvey database |
| `limesurvey_upload` | Uploaded files |
| `limesurvey_config` | LimeSurvey configuration |
| `graphdb_data` | RDF triples and indexes |
| `graphdb_import` | Import staging area |
| `converter_logs` | Converter service logs |
| `builder_logs` | Survey Builder logs |

### Backup Data

```bash
# Backup all volumes
docker-compose stop
docker run --rm -v limesurvey-knowledge-graph_graphdb_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/graphdb-backup-$(date +%Y%m%d).tar.gz /data

# Backup MySQL
docker-compose exec mysql mysqldump -u root -prootpassword limesurvey \
  > backups/limesurvey-$(date +%Y%m%d).sql
```

### Restore Data

```bash
# Restore GraphDB
docker run --rm -v limesurvey-knowledge-graph_graphdb_data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/graphdb-backup-YYYYMMDD.tar.gz -C /

# Restore MySQL
docker-compose exec -T mysql mysql -u root -prootpassword limesurvey \
  < backups/limesurvey-YYYYMMDD.sql
```

---

## 🔍 Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker-compose logs -f [service-name]
```

**Common issues:**
- Ports already in use (change port mapping)
- Insufficient memory (increase Docker memory limit)
- Missing files (ensure all files are present)

### Init Service Fails

**View initialization logs:**
```bash
docker-compose logs init-service
```

**Common causes:**
- GraphDB or LimeSurvey not ready yet (wait longer)
- Ontology file missing
- Network issues

**Manual re-run:**
```bash
docker-compose up init-service
```

### LimeSurvey Not Accessible

**Check if MySQL is ready:**
```bash
docker-compose logs mysql
```

**Wait for:** `mysqld: ready for connections`

**Restart LimeSurvey:**
```bash
docker-compose restart limesurvey
```

### GraphDB Out of Memory

**Increase heap size in docker-compose.yml:**
```yaml
graphdb:
  environment:
    GDB_HEAP_SIZE: 4G
    GDB_MAX_MEM: 4G
```

**Restart:**
```bash
docker-compose restart graphdb
```

### Survey Builder Not Loading Data

**Check GraphDB connection:**
```bash
curl http://localhost:7200/rest/repositories
```

**Check if repository exists:**
```bash
curl http://localhost:7200/rest/repositories/test_repo
```

**Re-run initialization:**
```bash
docker-compose stop init-service
docker-compose rm -f init-service
docker-compose up init-service
```

### Container Keeps Restarting

**Check status:**
```bash
docker-compose ps
```

**View last 100 log lines:**
```bash
docker-compose logs --tail=100 [service-name]
```

**Check resource usage:**
```bash
docker stats
```

---

## 🔒 Security Considerations

### Production Deployment

**Change default passwords:**

1. Edit `docker-compose.yml` BEFORE first start
2. Update all `admin/admin` credentials
3. Use strong passwords (16+ characters)

**Enable HTTPS:**

Add reverse proxy (nginx/traefik) with SSL certificates:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./certs:/etc/nginx/certs:ro
```

**Restrict network access:**

```yaml
networks:
  survey-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Use environment files:**

Create `.env` file (don't commit!):
```env
MYSQL_ROOT_PASSWORD=strong_password_here
LIMESURVEY_ADMIN_PASSWORD=another_strong_password
GRAPHDB_PASSWORD=yet_another_password
```

Reference in docker-compose.yml:
```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
```

---

## 🧪 Testing the Setup

### 1. Test LimeSurvey

```bash
# Create test survey
curl -X POST http://localhost:8080/index.php/admin/remotecontrol \
  -H "Content-Type: application/json" \
  -d '{"method":"get_session_key","params":["admin","admin"],"id":1}'
```

### 2. Test GraphDB

```bash
# Check repository
curl http://localhost:7200/rest/repositories/test_repo
```

### 3. Test Survey Builder

```bash
# Health check
curl http://localhost:5005
```

### 4. Complete Workflow Test

1. Access LimeSurvey: http://localhost:8080
2. Create a simple survey
3. Export it using Semantic Converter
4. View in GraphDB: http://localhost:7200
5. Build new survey in Survey Builder: http://localhost:5005

---

## 📈 Performance Tuning

### Increase Memory

**GraphDB:**
```yaml
environment:
  GDB_HEAP_SIZE: 4G
  GDB_MIN_MEM: 2G
  GDB_MAX_MEM: 4G
```

**MySQL:**
```yaml
command: --innodb-buffer-pool-size=1G --innodb-log-file-size=256M
```

### Use SSD for Volumes

Mount volumes on SSD for better performance:

```yaml
volumes:
  graphdb_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/ssd/graphdb
```

---

## 🆘 Getting Help

**View all service logs:**
```bash
./start-docker.sh
# Select option 6 (View logs) → 1 (All services)
```

**Common log locations:**
- `/app/logs/*.log` inside containers
- `docker-compose logs` for stdout/stderr

**Debug mode:**
```yaml
survey-builder:
  environment:
    FLASK_DEBUG: "True"
```

**Access container shell:**
```bash
docker-compose exec survey-builder /bin/bash
```

---

## 🎓 Next Steps

Once your Docker setup is running:

1. **Import sample surveys** from the `samples/` directory
2. **Configure RemoteControl API** in LimeSurvey (should be auto-enabled)
3. **Export your first survey** using the Semantic Converter
4. **Explore GraphDB** and run SPARQL queries
5. **Build a new survey** using the Survey Builder interface

Refer to the main [README.md](README.md) for detailed usage instructions.

---

## 📝 Notes

- First startup takes 2-3 minutes
- Init service runs once and exits (this is normal)
- Data persists across restarts
- Use `docker-compose down -v` to reset everything
- Check logs if services don't start

---

**Happy surveying! 🎉**