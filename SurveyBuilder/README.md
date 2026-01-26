# 📦 LimeSurvey Knowledge Graph - Project Structure

## 📁 Main Folders

```
.
├── SUS_test/          # 📊 Test surveys and sample data
├── Docker/            # 🐳 Complete setup with containers
├── Code/              # 💻 Scripts only for existing infrastructure
└── CodeUnion/         # 🎨 Survey Builder & Knowledge Graph Interface
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

This project offers **three deployment options** based on your needs:

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

## 🎨 **Option 3: CodeUnion/** - Integrated Web Application

**Complete Python Flask application for survey management and knowledge graph operations**

### **What's Included:**
- ✅ **Survey Builder Interface** - Visual survey creation and editing
- ✅ **LimeSurvey Integration** - Create, import, and export surveys via API
- ✅ **GraphDB Integration** - Full knowledge graph operations
- ✅ **Variable Search** - Search surveys by variables and metadata
- ✅ **RML Conversion** - Automatic survey-to-RDF transformation
- ✅ **Web Interface** - Complete web-based management console

### **Best For:**
- 👥 Users who want a complete web application
- 👥 Users who need visual survey building tools
- 👥 Teams requiring collaborative survey management
- 👥 Projects needing advanced knowledge graph queries
- 👥 Users who want integrated LimeSurvey ↔ GraphDB workflows

### **Key Features:**

#### **Survey Builder:**
- 📝 Create surveys visually with drag-and-drop interface
- 🔄 Import existing surveys from LimeSurvey
- 📤 Export surveys directly to LimeSurvey
- 🎨 Configure question types, subquestions, and answer options
- 👁️ Real-time preview of survey structure

#### **LimeSurvey Operations:**
- 🔌 Connect to LimeSurvey via RemoteControl API
- 📊 List all surveys, groups, and questions
- ⬇️ Import survey data into GraphDB
- ⬆️ Export GraphDB surveys to LimeSurvey
- 🔄 Bidirectional synchronization

#### **GraphDB Operations:**
- 🗄️ Store surveys as RDF knowledge graphs
- 🔍 SPARQL query interface
- 🔎 Search by variables, question types, metadata
- 📊 Visualize survey structure and relationships
- 🔗 Link surveys with semantic relationships

#### **Advanced Search:**
- 🎯 Find questions by variable name
- 🏷️ Filter by question type (L, M, F, Q, etc.)
- 📋 Search across multiple surveys
- 🔗 Discover related questions and surveys
- 📈 Analyze survey metadata

### **Quick Start:**
```bash
cd CodeUnion/

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure connections
# Edit app.py or use environment variables:
export LIMESURVEY_URL="http://localhost:8080/index.php/admin/remotecontrol"
export LIMESURVEY_USERNAME="admin"
export LIMESURVEY_PASSWORD="admin"
export GRAPHDB_URL="http://localhost:7200"
export GRAPHDB_REPOSITORY="test_repo"

# 3. Run application
python app.py

# 4. Access web interface
# http://localhost:5005/surveybuilder
```

### **Structure:**
```
CodeUnion/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── surveybuilder.html     # Survey Builder interface
│   ├── graphdb.html           # GraphDB interface
│   └── limesurvey.html        # LimeSurvey interface
├── static/                     # CSS, JS, images
│   ├── js/
│   │   ├── surveybuilder.js   # Survey Builder logic
│   │   ├── graphdb.js         # GraphDB operations
│   │   └── limesurvey.js      # LimeSurvey operations
│   └── css/
├── pyrml/                      # RML conversion library
└── outputs/                    # Generated files
```

### **API Endpoints:**

#### **Survey Builder:**
- `GET /surveybuilder` - Main Survey Builder interface
- `POST /api/surveybuilder/config` - Save configuration
- `GET /api/surveybuilder/groups` - Get survey groups
- `GET /api/surveybuilder/questions` - Get questions
- `POST /api/surveybuilder/limesurvey/create` - Create survey in LimeSurvey

#### **GraphDB:**
- `GET /graphdb` - GraphDB interface
- `POST /api/graphdb/query` - Execute SPARQL query
- `POST /api/graphdb/import` - Import RDF data
- `GET /api/graphdb/search` - Search by variables

#### **LimeSurvey:**
- `GET /limesurvey` - LimeSurvey interface
- `GET /api/limesurvey/surveys` - List all surveys
- `GET /api/limesurvey/groups/:sid` - Get survey groups
- `GET /api/limesurvey/questions/:sid` - Get survey questions
- `POST /api/limesurvey/export` - Export survey to JSON

### **Workflow Example:**

```
1. Create Survey in Survey Builder
   ↓
2. Export to LimeSurvey
   ↓
3. Export LimeSurvey data to JSON
   ↓
4. Convert JSON to RDF with RML
   ↓
5. Import RDF into GraphDB
   ↓
6. Search and query in GraphDB
   ↓
7. Create new survey based on existing questions
```

### **Environment Variables:**

```bash
# LimeSurvey Configuration
LIMESURVEY_URL=http://localhost:8080/index.php/admin/remotecontrol
LIMESURVEY_USERNAME=admin
LIMESURVEY_PASSWORD=admin

# GraphDB Configuration
GRAPHDB_URL=http://localhost:7200
GRAPHDB_REPOSITORY=test_repo
GRAPHDB_USERNAME=admin
GRAPHDB_PASSWORD=admin

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5005
FLASK_DEBUG=False
```

### **Requirements:**
- Python 3.8+
- Flask 2.0+
- SPARQLWrapper
- requests
- pyrml (included)
- LimeSurvey instance (accessible via API)
- GraphDB instance (accessible via SPARQL endpoint)

---

## 🔄 **Synchronization Between Folders**

Both Docker/ and Code/ folders contain the same conversion scripts. You can keep them synchronized:

```bash
# If you modify files in Code/
cd Code/
./sync_files.sh  # Syncs to Docker/

# If you modify files in Docker/
cd Docker/
./sync_files.sh  # Syncs to Code/
```

**CodeUnion/** is independent and contains the complete web application.

**Why sync?**
- Keep both versions up-to-date
- Test in Docker, deploy in Code (or vice versa)
- Share improvements between setups

---

## 📊 **Comparison**

| Feature | SUS_test/ | Docker/ | Code/ | CodeUnion/ |
|---------|-----------|---------|-------|------------|
| **Sample surveys** | ✅ Yes | ⚠️ Uses SUS_test | ⚠️ Uses SUS_test | ⚠️ Uses SUS_test |
| **Test data** | ✅ Yes | ⚠️ Uses SUS_test | ⚠️ Uses SUS_test | ⚠️ Uses SUS_test |
| **LimeSurvey included** | ❌ No | ✅ Yes | ❌ No | ❌ No (connects to external) |
| **GraphDB included** | ❌ No | ✅ Yes | ❌ No | ❌ No (connects to external) |
| **Survey Builder UI** | ❌ No | ✅ Yes | ❌ No | ✅ Yes (advanced) |
| **Web Interface** | ❌ No | ✅ Basic | ❌ No | ✅ Complete |
| **Conversion scripts** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes (integrated) |
| **Variable Search** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **SPARQL Queries** | ❌ No | ⚠️ Manual | ⚠️ Manual | ✅ Integrated |
| **API Integration** | ❌ No | ✅ Yes | ❌ No | ✅ Advanced |
| **Setup time** | N/A | ⚡ 5 minutes | ⏱️ Depends | ⏱️ 10 minutes |
| **Download size** | 📦 ~10MB | 📦 Full (~500MB) | 📦 Light (~5MB) | 📦 Medium (~50MB) |
| **Ideal for** | 🎯 Reference | 🎯 Quick Start | 🎯 Production Scripts | 🎯 Full Application |

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

#### **Want Complete Web App → Use CodeUnion/**
```bash
# 1. Download CodeUnion folder
# 2. cd CodeUnion/
# 3. pip install -r requirements.txt
# 4. Configure environment variables
# 5. python app.py
# 6. Access http://localhost:5005/surveybuilder
# 7. Use SUS_test/ surveys for testing
```

---

## 📖 **Documentation**

- **Docker Setup**: See `Docker/README.md`
- **Code Setup**: See `Code/README.md`
- **CodeUnion Setup**: See `CodeUnion/README.md`
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

### **For CodeUnion Users:**
- Full-featured web application
- Requires LimeSurvey and GraphDB running
- Best for production use with advanced features
- Includes all conversion tools integrated
- Visual interface for all operations

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
- ✅ You only need conversion scripts

**Choose CodeUnion/ if:**
- ✅ You want a complete web application
- ✅ You need visual survey building tools
- ✅ You want integrated LimeSurvey ↔ GraphDB workflows
- ✅ You need advanced search and query features
- ✅ You're building a production system

---

