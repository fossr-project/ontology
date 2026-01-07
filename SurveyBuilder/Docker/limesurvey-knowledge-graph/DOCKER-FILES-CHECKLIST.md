# Docker Setup - Complete File Checklist

## 📋 Required Files

### 1. Docker Configuration Files

| File | Description | Status |
|------|-------------|--------|
| `docker-compose.yml` | Main orchestration file - defines all services | ⭐ **REQUIRED** |
| `Dockerfile.converter` | Image for Semantic Converter service | ⭐ **REQUIRED** |
| `Dockerfile.builder` | Image for Survey Builder (Flask app) | ⭐ **REQUIRED** |
| `Dockerfile.init` | Image for initialization service | ⭐ **REQUIRED** |
| `.dockerignore` | Files to exclude from Docker images | ✅ Recommended |

### 2. Application Files

| File | Description | Status |
|------|-------------|--------|
| `main.py` | Core application logic (Semantic Converter classes) | ⭐ **REQUIRED** |
| `converter_service.py` | Flask wrapper for Converter API | ⭐ **REQUIRED** |
| `init_system.py` | Automatic system initialization | ⭐ **REQUIRED** |
| `requirements.txt` | Python dependencies | ⭐ **REQUIRED** |

### 3. Support Scripts

| File | Description | Status |
|------|-------------|--------|
| `start-docker.sh` | Interactive Docker management script | ✅ Highly Recommended |
| `check-docker-setup.sh` | Verification script for setup | ✅ Helpful |
| `DOCKER-SETUP.md` | Docker setup documentation | ✅ Recommended |

### 4. Directories

| Directory | Contents | Status |
|-----------|----------|--------|
| `rml/` | RML mapping files (*.ttl) | ⭐ **REQUIRED** |
| `ontology/` | limesurvey.ttl ontology file | ⭐ **REQUIRED** |
| `templates/` | index.html for Survey Builder | ⭐ **REQUIRED** |
| `samples/` | Sample survey files (*.lss, *.csv) | ✅ Optional |
| `exports/` | Auto-created for exports | 🔧 Auto-created |
| `output/` | Auto-created for TTL outputs | 🔧 Auto-created |
| `logs/` | Auto-created for logs | 🔧 Auto-created |

---

## 📝 File Contents Summary

### docker-compose.yml
Defines 6 services:
- `mysql` - Database for LimeSurvey
- `limesurvey` - Survey management platform
- `graphdb` - RDF triple store
- `semantic-converter` - Export and conversion service
- `survey-builder` - Web interface (Flask)
- `init-service` - One-time initialization

### Dockerfile.converter
```dockerfile
FROM python:3.10-slim
# Installs dependencies
# Copies main.py, converter_service.py
# Copies RML mappings and ontology
# Runs converter_service.py
```

### Dockerfile.builder
```dockerfile
FROM python:3.10-slim
# Installs dependencies
# Copies Flask app (main.py → app.py)
# Copies templates/
# Runs Flask on port 5005
```

### Dockerfile.init
```dockerfile
FROM python:3.10-slim
# Installs dependencies
# Copies init_system.py
# Runs initialization once and exits
```

### converter_service.py
Flask API wrapper that provides:
- `/health` - Health check endpoint
- `/api/export/survey/<id>` - Export survey from LimeSurvey
- `/api/list/surveys` - List available surveys

### init_system.py
Initialization script that:
1. Waits for GraphDB and LimeSurvey to be ready
2. Creates GraphDB repository
3. Uploads LimeSurvey ontology
4. Optionally imports sample data
5. Exits after completion

---

## 🔧 Setup Instructions

### Step 1: Download/Create All Files

Make sure you have all the files listed above in your project directory.

### Step 2: Verify Setup

```bash
chmod +x check-docker-setup.sh
./check-docker-setup.sh
```

This will show you which files are present and which are missing.

### Step 3: Make Scripts Executable

```bash
chmod +x start-docker.sh
chmod +x check-docker-setup.sh
```

### Step 4: Review Configuration

Check these files and customize if needed:
- `docker-compose.yml` - Ports, passwords, memory limits
- `Dockerfile.builder` - Ensure correct Flask app filename

### Step 5: Start Docker

```bash
./start-docker.sh
# Select option 1
```

---

## ⚠️ Important Notes

### Flask App Filename

In `Dockerfile.builder`, this line copies your Flask app:
```dockerfile
COPY main.py app.py
```

**If your Flask app has a different name:**
1. Either rename it to `main.py`
2. Or update the Dockerfile line, for example:
   ```dockerfile
   COPY my_flask_app.py app.py
   ```

### Repository Name Consistency

The repository name **must be the same** across all files:
- `docker-compose.yml`: `GRAPHDB_REPOSITORY: test_repo`
- `main.py`: Default repository should be `test_repo`
- Survey Builder configuration

### Required Files in Directories

**rml/directory:**
- `RMLGroup2.ttl`
- `RMLQuestion.ttl`
- `RMLQuestionFromJson.ttl` (optional)

**ontology/ directory:**
- `limesurvey.ttl`

**templates/ directory:**
- `index.html`

---

## 🧪 Testing Checklist

After starting Docker, verify:

- [ ] All containers are running: `docker-compose ps`
- [ ] LimeSurvey accessible: http://localhost:8080
- [ ] GraphDB accessible: http://localhost:7200
- [ ] Survey Builder accessible: http://localhost:5005
- [ ] Init service completed successfully: `docker-compose logs init-service`
- [ ] Repository created in GraphDB: Check http://localhost:7200/repository
- [ ] Ontology loaded: Run SPARQL query in GraphDB

### Quick Test Commands

```bash
# Check all services status
docker-compose ps

# Check logs
docker-compose logs -f survey-builder

# Test LimeSurvey API
curl -X POST http://localhost:8080/index.php/admin/remotecontrol \
  -H "Content-Type: application/json" \
  -d '{"method":"get_session_key","params":["admin","admin"],"id":1}'

# Test GraphDB
curl http://localhost:7200/rest/repositories/test_repo

# Test Survey Builder
curl http://localhost:5005
```

---

## 🆘 Troubleshooting

### "File not found" errors

Run verification script:
```bash
./check-docker-setup.sh
```

### Containers not starting

Check logs:
```bash
docker-compose logs [service-name]
```

### Port conflicts

Modify ports in `docker-compose.yml`:
```yaml
ports:
  - "9080:8080"  # Change 9080 to any available port
```

### Init service fails

Re-run initialization:
```bash
docker-compose up init-service
```

### Out of memory

Increase Docker memory limit in Docker Desktop settings or modify `docker-compose.yml`:
```yaml
graphdb:
  environment:
    GDB_HEAP_SIZE: 4G
```

---

## 📚 Additional Resources

- Main README: `README.md`
- Docker Setup Guide: `DOCKER-SETUP.md`
- Sample Data: `samples/` directory
- Logs: Check with `./start-docker.sh` option 6

---

## ✅ Final Checklist Before Starting

- [ ] All required files present
- [ ] Scripts are executable (`chmod +x *.sh`)
- [ ] Docker and Docker Compose installed
- [ ] At least 8GB RAM available
- [ ] Ports 8080, 7200, 5005 are free
- [ ] Flask app filename correct in Dockerfile.builder
- [ ] RML files and ontology present
- [ ] Templates directory with index.html

**If all checked, run:**
```bash
./start-docker.sh
```

**Good luck! 🚀**