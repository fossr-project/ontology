# 📦 LimeSurvey Knowledge Graph - Project Structure

## 📁 Main Folders

```
.
├── SUS_test/          # 📊 Test surveys and sample data
├── Docker/            # 🐳 Complete setup with containers
└── Code/              # 💻 Scripts only for existing infrastructure
```

---

## 📊 **SUS_test/** - Sample Surveys & Test Data

**Test surveys and example configurations**

### **What's Included:**
- ✅ Sample LimeSurvey surveys (.lss format)
- ✅ Test questionnaires
- ✅ Example JSON exports
- ✅ Sample configurations
- ✅ Reference data for testing

### **Purpose:**
- 🎯 Test the conversion pipeline
- 🎯 Validate RML mappings
- 🎯 Example surveys to learn from
- 🎯 Quality assurance

### **Usage:**
```bash
cd SUS_test/

# Import surveys into LimeSurvey
# Use these as templates for your own surveys
# Test data extraction and conversion
```

---

## 🎯 Choose Your Deployment

This project offers **two deployment options** based on your needs:

---

## 🐳 **Option 1: Docker/** - Complete Setup (Recommended)

**For users who want everything ready to go**

### **What's Included:**
- ✅ LimeSurvey container (pre-configured)
- ✅ GraphDB container (pre-configured)
- ✅ Survey Builder web interface
- ✅ All conversion scripts (RML, Python, Bash)
- ✅ Sample data and configurations
- ✅ docker-compose.yml for easy deployment

### **Best For:**
- 👥 New users
- 👥 Users without existing LimeSurvey/GraphDB installations
- 👥 Users who want quick setup and testing
- 👥 Development and demo environments

### **Quick Start:**
```bash
cd Docker/
docker-compose up -d

# Access:
# - LimeSurvey: http://localhost:8080
# - GraphDB: http://localhost:7200
# - Survey Builder: http://localhost:5001
```

### **Structure:**
```
Docker/
├── docker-compose.yml
├── Dockerfile.builder
├── requirements.txt
├── app.py
├── questions_only.json
├── subquestions_only.json
├── answeroptions_only.json
├── attributes_only.json
├── 1_questions.rml
├── 2_subquestions.rml
├── 3_answeroptions.rml
├── 4_attributes.rml
├── split_json.py
├── convert_all.sh
└── sync_files.sh
```

---

## 💻 **Option 2: Code/** - Scripts Only

**For users who already have LimeSurvey and GraphDB running**

### **What's Included:**
- ✅ Conversion scripts (RML, Python, Bash)
- ✅ JSON transformation tools
- ✅ Configuration templates
- ❌ No containers (you provide your own services)

### **Best For:**
- 👥 Users with existing LimeSurvey installation
- 👥 Users with existing GraphDB installation
- 👥 Production environments with custom infrastructure
- 👥 Users who want lightweight, scripts-only deployment

### **Requirements:**
You must already have:
- ✅ LimeSurvey running (accessible via API)
- ✅ GraphDB running (accessible via SPARQL endpoint)
- ✅ Python 3.8+ with pyrml installed

### **Quick Start:**
```bash
cd Code/

# 1. Configure your endpoints
# Edit connection settings for your LimeSurvey and GraphDB

# 2. Run conversions
./convert_all.sh

# 3. Load into your GraphDB
# Use your existing GraphDB interface
```

### **Structure:**
```
Code/
├── questions_only.json
├── subquestions_only.json
├── answeroptions_only.json
├── attributes_only.json
├── 1_questions.rml
├── 2_subquestions.rml
├── 3_answeroptions.rml
├── 4_attributes.rml
├── split_json.py
├── convert_all.sh
└── sync_files.sh
```

---

## 🔄 **Synchronization Between Folders**

Both folders contain the same conversion scripts. You can keep them synchronized:

```bash
# If you modify files in Code/
cd Code/
./sync_files.sh  # Syncs to Docker/

# If you modify files in Docker/
cd Docker/
./sync_files.sh  # Syncs to Code/
```

**Why sync?**
- Keep both versions up-to-date
- Test in Docker, deploy in Code (or vice versa)
- Share improvements between setups

---

## 📊 **Comparison**

| Feature | SUS_test/ | Docker/ | Code/ |
|---------|-----------|---------|-------|
| **Sample surveys** | ✅ Yes | ⚠️ Uses SUS_test | ⚠️ Uses SUS_test |
| **Test data** | ✅ Yes | ⚠️ Uses SUS_test | ⚠️ Uses SUS_test |
| **LimeSurvey included** | ❌ No | ✅ Yes | ❌ No (you provide) |
| **GraphDB included** | ❌ No | ✅ Yes | ❌ No (you provide) |
| **Survey Builder UI** | ❌ No | ✅ Yes | ❌ No |
| **Conversion scripts** | ❌ No | ✅ Yes | ✅ Yes |
| **Setup time** | N/A | ⚡ 5 minutes | ⏱️ Depends on your infrastructure |
| **Download size** | 📦 ~10MB | 📦 Full (~500MB) | 📦 Light (~5MB) |
| **Ideal for** | 🎯 Reference & Testing | 🎯 Complete Development | 🎯 Production Deployment |

---

## 🚀 **Getting Started**

### **Step 1: Get Sample Data (Optional)**
```bash
# Browse SUS_test/ for example surveys
cd SUS_test/
# Import .lss files into your LimeSurvey
```

### **Step 2: Choose Your Deployment**

#### **New Users → Use Docker/**
```bash
# 1. Download Docker folder
# 2. cd Docker/
# 3. docker-compose up -d
# 4. Access http://localhost:5001
# 5. Import surveys from SUS_test/ if needed
```

#### **Existing Infrastructure → Use Code/**
```bash
# 1. Download Code folder
# 2. cd Code/
# 3. Configure your LimeSurvey/GraphDB endpoints
# 4. ./convert_all.sh
# 5. Use SUS_test/ surveys for testing
```

---

## 📖 **Documentation**

- **Docker Setup**: See `Docker/README.md`
- **Code Setup**: See `Code/README.md`
- **RML Mappings**: See individual `.rml` files
- **Synchronization**: See `README_DUPLICATES_EN.md`

---

## 💡 **Tips**

### **For Docker Users:**
- All services run in containers
- Data persists in Docker volumes
- Easy to reset: `docker-compose down -v`
- No conflicts with existing services

### **For Code Users:**
- Configure connection strings to your services
- Ensure your LimeSurvey API is accessible
- Ensure your GraphDB SPARQL endpoint is accessible
- Scripts use your existing infrastructure

---

## 🆘 **Which One Should I Use?**

**Choose Docker/ if:**
- ✅ You want to try the system quickly
- ✅ You don't have LimeSurvey/GraphDB installed
- ✅ You want an isolated test environment
- ✅ You're doing development or demos

**Choose Code/ if:**
- ✅ You already have LimeSurvey running
- ✅ You already have GraphDB running
- ✅ You want to integrate with existing infrastructure
- ✅ You need a production deployment

---

## 📞 **Support**

- **Docker issues**: Check `Docker/README.md`
- **Code issues**: Check `Code/README.md`
- **RML issues**: Check `.rml` files comments
- **General questions**: See main documentation

---

## ✅ **Summary**

```
SUS_test/ → Sample surveys and test data (for reference)
Docker/   → Complete package with everything (for easy setup)
Code/     → Scripts only, bring your own infrastructure (for production)

Use SUS_test/ for example surveys and testing.
Both Docker/ and Code/ contain the same conversion scripts.
Use sync_files.sh to keep Docker/ and Code/ synchronized.
```
