# LimeSurvey Knowledge Graph Suite

A complete Python-based toolset for converting LimeSurvey surveys into semantic RDF knowledge graphs and building new surveys from GraphDB data through an interactive web interface.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
  - [1. LimeSurvey Setup](#1-limesurvey-setup)
  - [2. GraphDB Setup](#2-graphdb-setup)
  - [3. Python Environment Setup](#3-python-environment-setup)
- [Component 1: LimeSurvey Semantic Converter](#component-1-limesurvey-semantic-converter)
- [Component 2: Survey Builder](#component-2-survey-builder)
- [Complete Workflow](#complete-workflow)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Future Development](#future-development)
- [License](#license)

---

## Overview

This suite provides two complementary tools:

1. **LimeSurvey Semantic Converter**: Exports survey data from LimeSurvey, transforms it into RDF using RML mappings, and loads it into GraphDB
2. **Survey Builder**: A Flask web application that queries GraphDB to build new surveys by selecting and combining existing groups and questions

**Key Features:**
- Bidirectional integration between LimeSurvey and GraphDB
- Semantic representation of survey structures
- Interactive drag-and-drop survey builder
- SPARQL query interface for advanced data exploration
- Export to multiple formats (JSON, CSV, LSS, direct LimeSurvey import)
- Support for complex question types, subquestions, and answer options

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │  Survey Management Platform     │
                    │        (LimeSurvey)             │
                    └────────────┬────────────────────┘
                                 │
                    Remote Control REST API
                                 │
                    ┌────────────┴────────────┐
                    │                         │
         ┌──────────▼──────────┐   ┌─────────▼──────────┐
         │  Survey Builder     │   │ Semantic Converter │
         │  (Flask Web App)    │   │  (Python + RML)    │
         └──────────┬──────────┘   └─────────┬──────────┘
                    │                        │
              SPARQL Query              Data Import
                    │                        │
                    └────────┬───────────────┘
                             │
                    ┌────────▼─────────┐
                    │ Knowledge Graph  │
                    │   (GraphDB)      │
                    │  Triple Store    │
                    └──────────────────┘
```

**Components:**

1. **Survey Management Platform (LimeSurvey)**: Source and destination for survey data
2. **Semantic Converter**: Exports data from LimeSurvey and converts to RDF using RML mappings
3. **Knowledge Graph (GraphDB)**: Central triple store containing semantic survey data
4. **Survey Builder**: Web interface for querying GraphDB and creating new surveys
5. **Remote Control REST API**: Bidirectional communication channel between LimeSurvey and Python components

---

## Prerequisites

- **Python 3.8+**
- **LimeSurvey 5.x+** with RemoteControl API enabled
- **GraphDB 10.x+** (Free or Enterprise edition)
- **Web browser** (Chrome, Firefox, or Edge recommended for Survey Builder)
- **Git** (for cloning the repository)

---

## Installation Guide

### 1. LimeSurvey Setup

#### Install LimeSurvey Locally

**Option 1: Using XAMPP (Windows/Mac/Linux)**

1. Download and install [XAMPP](https://www.apachefriends.org/)
2. Download [LimeSurvey](https://www.limesurvey.org/download)
3. Extract LimeSurvey to `xampp/htdocs/limesurvey`
4. Start Apache and MySQL from XAMPP Control Panel
5. Navigate to `http://localhost/limesurvey` and follow installation wizard
6. Create admin credentials (save them!)

**Option 2: Using Docker**

```bash
docker run -d --name limesurvey \
  -p 8080:80 \
  -e DB_TYPE=mysql \
  -e DB_HOST=mysql \
  -e DB_NAME=limesurvey \
  martialblog/limesurvey:latest
```

#### Enable RemoteControl API

**This step is critical for both tools to work!**

1. Log in to LimeSurvey as administrator
2. Navigate to **Configuration** → **Global settings**
3. Click on the **Interfaces** tab
4. Find **RPC interface enabled** and set it to **JSON-RPC**
5. Click **Save**

**Verify RemoteControl is Active:**

```bash
curl -X POST http://localhost/limesurvey/index.php/admin/remotecontrol \
  -H "Content-Type: application/json" \
  -d '{"method":"get_session_key","params":["admin","password"],"id":1}'
```

Expected response: `{"result":"your_session_key_here","id":1,...}`

#### Import Sample Surveys

The repository includes sample surveys for testing:

**Method 1: Using provided survey files**

1. In LimeSurvey admin panel:
   - Go to **Create survey** → **Import**
   - Select **Import survey** from dropdown
   - Upload `samples/survey1.lss` or `samples/survey2.lss`
   - Click **Import survey**
2. Note the Survey ID (you'll need it for the Semantic Converter)

**Method 2: Using CSV data directly**

If you prefer to work directly with exported data:
- `samples/list_groups_694511.csv` - Sample groups data
- `samples/list_questions_694511.csv` - Sample questions data

These files can be used directly with the RML mappings (see Semantic Converter section).

---

### 2. GraphDB Setup

#### Install GraphDB

**Standalone Installation**

1. Download [GraphDB Free](https://www.ontotext.com/products/graphdb/download/)
2. Extract the archive to your preferred location
3. Run GraphDB:
   ```bash
   # Linux/Mac
   cd graphdb-free-10.x.x
   ./bin/graphdb
   
   # Windows
   cd graphdb-free-10.x.x
   bin\graphdb.cmd
   ```
4. Open browser to `http://localhost:7200`
5. Create admin credentials if prompted

#### Create Repository

The Semantic Converter can create repositories automatically, but you can also create one manually:

1. Open GraphDB Workbench at `http://localhost:7200`
2. Click **Setup** → **Repositories** → **Create new repository**
3. Choose **GraphDB Repository**
4. Configure:
   - **Repository ID**: `test_repo` (must match the repository name used in scripts)
   - **Title**: `LimeSurvey Knowledge Graph`
   - **Ruleset**: `empty` (no reasoning needed for this use case)
5. Click **Create**

---

### 3. Python Environment Setup

#### Clone the Repository

```bash
git clone https://github.com/yourusername/limesurvey-knowledge-graph.git
cd limesurvey-knowledge-graph
```

#### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
requests>=2.31.0
rdflib>=6.3.2
pyrml>=0.4.0
flask>=2.3.0
flask-cors>=4.0.0
SPARQLWrapper>=2.0.0
python-dotenv>=1.0.0
```

#### Configuration Files

Create a `.env` file in the project root with your credentials:

```env
# LimeSurvey Configuration
LIMESURVEY_URL=http://localhost/limesurvey/index.php/admin/remotecontrol
LIMESURVEY_USERNAME=admin
LIMESURVEY_PASSWORD=your_password

# GraphDB Configuration
GRAPHDB_URL=http://localhost:7200
GRAPHDB_USERNAME=admin
GRAPHDB_PASSWORD=admin
GRAPHDB_REPOSITORY=test_repo

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5005
FLASK_DEBUG=True
```

**⚠️ Important**: Add `.env` to `.gitignore` to keep credentials secure!

---

## Component 1: LimeSurvey Semantic Converter

The Semantic Converter exports survey structures from LimeSurvey and transforms them into RDF triples using RML (R2RML) mappings.

### Quick Start

```python
from main import LimeSurveyExporter, RMLtoGraphDBPipeline

# 1. Export survey data from LimeSurvey
exporter = LimeSurveyExporter(
    url="http://localhost/limesurvey/index.php/admin/remotecontrol",
    username="admin",
    password="your_password"
)


# Export groups (creates CSV)
exporter.export_groups(survey_id)

# 2. Convert to RDF and load into GraphDB
pipeline = RMLtoGraphDBPipeline(
    graphdb_url="http://localhost:7200",
    username="admin",
    password="admin"
)

# Setup repository and load ontology
pipeline.setup_repository(
    repo_id="test_repo",
    repo_title="LimeSurvey Knowledge Graph",
    clear_if_exists=True
)

# Load the LimeSurvey ontology
pipeline.load_ontology(
    repo_id="test_repo",
    ontology_file="limesurvey.ttl",
    context="http://example.org/ontology"
)

# 3. Convert and upload groups
pipeline.process_and_upload(
    rml_file="RMLGroup2.ttl",
    repo_id="test_repo",
    context="http://example.org/groups",
    save_local=True,
    output_file="output_groups.ttl"
)

# 4. Convert and upload questions
pipeline.process_and_upload(
    rml_file="RMLQuestion.ttl",
    repo_id="test_repo",
    context="http://example.org/questions",
    save_local=True,
    output_file="output_questions.ttl"
)

print("✅ Data successfully loaded into GraphDB!")
```

### Conversion Workflow Options

#### Option A: Direct Export from LimeSurvey

**Best for**: Active LimeSurvey instances with RemoteControl API enabled

```python
```python
# Export from LimeSurvey → JSON/CSV → RML → GraphDB
exporter.export_groups(survey_id)

# Then proceed with pipeline.process_and_upload()
```

#### Option B: Use Existing CSV Files

**Best for**: When you already have exported CSV files

1. Place your CSV files in the project directory:
   - `list_groups_{survey_id}.csv`
   - `list_questions_{survey_id}.csv`

2. Update RML mapping files to point to your CSVs:

**Edit `RMLGroup2.ttl`:**
```turtle
rml:source [
  a csvw:Table;
  csvw:url "list_groups_20251014_105921.csv";  # Change to your file
  csvw:dialect [ a csvw:Dialect; csvw:delimiter "," ]
];
```

**Edit `RMLQuestion.ttl`:**
```turtle
rml:source [
  a csvw:Table;
  csvw:url "list_questions.csv";  # Change to your file
  csvw:dialect [ a csvw:Dialect; csvw:delimiter "," ]
];
```

3. Run the pipeline:
```python
pipeline.process_and_upload(
    rml_file="RMLGroup2.ttl",
    repo_id="test_repo",
    context="http://example.org/groups"
)
```

#### Option C: Use Pre-generated TTL Files

**Best for**: When you already have RDF data in Turtle format

```python
from main import GraphDBManager

graphdb = GraphDBManager(
    base_url="http://localhost:7200",
    username="admin",
    password="admin"
)

# Create repository
graphdb.create_repository("test_repo", "LimeSurvey KB")

# Upload ontology
graphdb.upload_file(
    repo_id="test_repo",
    file_path="limesurvey.ttl",
    context="http://example.org/ontology"
)

# Upload data files
graphdb.upload_file(
    repo_id="test_repo",
    file_path="output_groups.ttl",
    context="http://example.org/groups"
)

graphdb.upload_file(
    repo_id="test_repo",
    file_path="output_questions.ttl",
    context="http://example.org/questions"
)
```

### Understanding the RML Mappings

The RML mappings define how CSV/JSON data maps to RDF triples:

**Example: Group Mapping (simplified)**
```turtle
:GroupTriplesMap
  rml:logicalSource [
    rml:source "list_groups.csv" ;
    rml:referenceFormulation ql:CSV
  ] ;
  rr:subjectMap [
    rr:template "http://example.org/group/{gid}" ;
    rr:class ls:QuestionGroup
  ] ;
  rr:predicateObjectMap [
    rr:predicate ls:hasName ;
    rr:objectMap [
      rr:template "http://example.org/groupname/{gid}" 
    ]
  ] .
```

This creates triples like:
```turtle
<http://example.org/group/1> a ls:QuestionGroup ;
    ls:hasName <http://example.org/groupname/1> .
```

---

## Component 2: Survey Builder

The Survey Builder is a Flask web application that provides an interactive interface for querying GraphDB and building new surveys.

### Starting the Survey Builder

```bash
# Make sure you're in the project directory with activated virtualenv
python main.py  # This starts the Flask app (the file with Flask code)
```

You should see:
```
======================================================================
GraphDB Survey Builder - Flask Application
======================================================================
GraphDB URL: http://localhost:7200
Repository: test_repo

Server starting on http://localhost:5005
======================================================================
```

Open your browser to: **http://localhost:5005**

### Features

#### 1. Connection & Data Loading

**Test Connection**
- Click **🧪 Connection Test** to verify GraphDB is accessible
- Shows total triples, classes, and namespaces

**Load Data**
- Click **📌 Upload Data** to fetch groups and questions from GraphDB
- Data is displayed in the left sidebar

#### 2. Browse & Select

**Groups**
- Expand groups with the ▶ icon to see nested questions
- Click on a group to select it (and all its questions)
- Edit group names and descriptions with the ✏️ icon

**Questions**
- View question text, type, and metadata
- See answer options and subquestions if present
- Click to select individual questions
- Edit question text with the ✏️ icon

**Search**
- Use the search box to filter groups and questions
- Search works on names, descriptions, IDs, and text

#### 3. Organize Survey

**Drag & Drop**
- Reorder groups by dragging them
- Move questions between groups
- Drag questions to "drop zones" to add them to groups

**Preview Tab**
- See your survey structure in real-time
- Expand/collapse groups
- View order numbers
- Remove items with ✕ button

#### 4. SPARQL Query Interface

Click **🔍 Query SPARQL** to open the advanced query panel:

**Features:**
- Pre-loaded query templates
- Execute custom SPARQL queries
- View results in table format
- Export results as CSV or JSON
- **Load results directly into the app** for building surveys

**Example Query:**
```sparql
PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT ?group ?groupName ?question ?questionText
WHERE {
    ?group a ls:QuestionGroup ;
           ls:hasName ?name .
    ?name ls:nameText ?groupName .
    
    ?question ls:hasGroup ?group ;
              ls:hasContent ?content .
    ?content ls:text ?questionText .
}
LIMIT 100
```

#### 5. Export Options

**JSON Export**
- Structured JSON with all survey metadata
- Compatible with Survey Builder format

**CSV Export**
- LimeSurvey-compatible CSV format
- Semi-colon delimited
- Ready for manual import

**Direct LimeSurvey Export**
1. Click **🚀 Create on LimeSurvey**
2. Enter survey title and LimeSurvey credentials
3. The app will:
   - Create the survey
   - Create all groups
   - Import all questions with full details (subquestions, answer options, attributes)
   - Provide a direct link to the new survey

### Survey Builder Configuration

The Flask app reads configuration from the top configuration bar and `.env` file:

**In-App Configuration:**
- GraphDB URL and Repository can be changed in the UI
- LimeSurvey credentials are entered when creating a survey

**Environment Variables (`main.py`):**
```python
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY = "test_repo"
LIMESURVEY_URL = "http://localhost/limesurvey/index.php/admin/remotecontrol"
LIMESURVEY_USERNAME = "sara"
LIMESURVEY_PASSWORD = "sara"
```

---

## Complete Workflow

Here's a complete end-to-end workflow:

### Scenario: Create a new survey by combining questions from existing surveys

**Step 1: Export existing surveys to GraphDB**

```python
from main import LimeSurveyExporter, RMLtoGraphDBPipeline

# Export Survey 1
exporter = LimeSurveyExporter(url="...", username="...", password="...")
exporter.export_all_question_properties_survey(survey_id=123)
exporter.export_groups(survey_id=123)

# Export Survey 2
exporter.export_all_question_properties_survey(survey_id=456)
exporter.export_groups(survey_id=456)

# Convert to RDF
pipeline = RMLtoGraphDBPipeline(graphdb_url="http://localhost:7200")
pipeline.setup_repository("test_repo", clear_if_exists=True)
pipeline.load_ontology("test_repo", "limesurvey.ttl")

# Load groups
pipeline.process_and_upload("RMLGroup2.ttl", "test_repo", "http://example.org/groups")

# Load questions  
pipeline.process_and_upload("RMLQuestion.ttl", "test_repo", "http://example.org/questions")
```

**Step 2: Start Survey Builder**

```bash
python main.py  # Start Flask app
# Open http://localhost:5005
```

**Step 3: Build new survey**

1. Click **📌 Upload Data** to load groups/questions from GraphDB
2. Browse and select desired groups and questions
3. Use drag-and-drop to organize them
4. Edit text if needed
5. Preview the structure

**Step 4: Export to LimeSurvey**

1. Click **🚀 Create on LimeSurvey**
2. Enter:
   - Survey title: "Combined Survey 2025"
   - LimeSurvey URL and credentials
3. Click **🚀 Create Survey**
4. Wait for processing (complex surveys may take a minute)
5. Click the provided link to view your new survey in LimeSurvey

**Step 5: Activate and use**

In LimeSurvey:
1. Review the imported survey
2. Make any final adjustments
3. Activate the survey
4. Share with participants

---

## Project Structure

```
limesurvey-knowledge-graph/
├── main.py                          # Semantic Converter (main export/import logic)
├── app.py                           # Survey Builder (Flask application)
├── requirements.txt                 # Python dependencies
├── .env                             # Configuration (create this)
├── .gitignore                       # Git ignore file
├── README.md                        # This file
│
├── rml/                             # RML mapping files
│   ├── RMLGroup2.ttl                # Groups mapping
│   ├── RMLQuestion.ttl              # Questions mapping (CSV)
│   └── RMLQuestionFromJson.ttl      # Questions mapping (JSON)
│
├── ontology/
│   └── limesurvey.ttl               # LimeSurvey ontology
│
├── samples/                         # Sample data
│   ├── survey1.lss                  # Sample survey 1 (LimeSurvey format)
│   ├── survey2.lss                  # Sample survey 2
│   ├── list_groups_694511.csv       # Sample groups CSV
│   └── list_questions_694511.csv    # Sample questions CSV
│
├── templates/
│   └── index.html                   # Survey Builder web interface
│
├── exports/                         # Generated exports (created automatically)
│   ├── questions.json
│   ├── questions_normalized.json
│   └── *.csv
│
└── output/                          # Generated TTL files (created automatically)
    ├── output_groups.ttl
    └── output_questions.ttl
```

---

## Configuration

### LimeSurvey RemoteControl Settings

Ensure these settings in LimeSurvey:
- **Global settings → Interfaces → RPC interface**: JSON-RPC
- **User account**: Must have permission to create surveys

### GraphDB Repository Settings

Recommended settings for `test_repo`:
- **Ruleset**: `empty` (no reasoning needed)
- **Entity ID size**: 32
- **Enable context index**: Yes

### File Naming Convention

**Important**: The repository name in GraphDB must match across all components:
- In `main.py` (Semantic Converter): `GRAPHDB_REPOSITORY = "test_repo"`
- In Survey Builder Flask app: `REPOSITORY = "test_repo"`
- When creating repository: `repo_id = "test_repo"`

**Survey file naming**:
- Groups CSV: `list_groups_{survey_id}_{timestamp}.csv`
- Questions CSV: `list_questions_{survey_id}_{timestamp}.csv`
- Questions JSON: `questions.json` (normalized: `questions_normalized.json`)
- TTL outputs: `output_groups.ttl`, `output_questions.ttl`

---

## Examples

### Example 1: Export specific survey

```python
from main import LimeSurveyExporter

exporter = LimeSurveyExporter(
    url="http://localhost/limesurvey/index.php/admin/remotecontrol",
    username="admin",
    password="password"
)

# List all surveys
surveys_path = exporter.export_surveys()
print(f"Surveys exported to: {surveys_path}")

# Export specific survey data
survey_id = 123456
exporter.export_all_question_properties_survey(survey_id)
exporter.export_groups(survey_id)
exporter.export_questions(survey_id)
```

### Example 2: Query GraphDB directly

```python
from main import GraphDBClient

client = GraphDBClient("http://localhost:7200", "test_repo")

# Count all questions
query = """
PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT (COUNT(?question) as ?count)
WHERE {
    ?question a ls:Question .
}
"""

results = client.execute_query(query)
count = results["results"]["bindings"][0]["count"]["value"]
print(f"Total questions in GraphDB: {count}")
```

### Example 3: Batch conversion

```python
from main import RMLtoGraphDBPipeline

pipeline = RMLtoGraphDBPipeline("http://localhost:7200")

# Setup
pipeline.setup_repository("my_surveys", "My Surveys KB")
pipeline.load_ontology("my_surveys", "limesurvey.ttl")

# Batch process multiple RML files
results = pipeline.batch_process(
    rml_files=[
        "RMLGroup2.ttl",
        "RMLQuestion.ttl",
        "RMLAnswerOptions.ttl"
    ],
    repo_id="my_surveys",
    contexts=[
        "http://example.org/groups",
        "http://example.org/questions",
        "http://example.org/answers"
    ]
)

print(f"✅ Processed {results['total_triples']} triples")
print(f"✅ Success: {len(results['success'])} files")
print(f"✗ Failed: {len(results['failed'])} files")
```

---

## Troubleshooting

### Common Issues

#### 1. "Connection refused" when connecting to GraphDB

**Problem**: GraphDB is not running or wrong URL

**Solution**:
```bash
# Check if GraphDB is running
curl http://localhost:7200/rest/repositories

# If not, start GraphDB
cd graphdb-free-10.x.x
./bin/graphdb  # or bin\graphdb.cmd on Windows
```

#### 2. "Repository not found"

**Problem**: Repository `test_repo` doesn't exist

**Solution**:
```python
from main import GraphDBManager

graphdb = GraphDBManager("http://localhost:7200")
graphdb.create_repository("test_repo", "Test Repository")
```

#### 3. "RemoteControl API not enabled"

**Problem**: LimeSurvey RPC interface is disabled

**Solution**:
1. Login to LimeSurvey as admin
2. Configuration → Global settings → Interfaces
3. Set "RPC interface enabled" to "JSON-RPC"
4. Save

#### 4. Empty results in Survey Builder

**Problem**: No data loaded from GraphDB

**Possible causes**:
- Wrong namespace in queries
- Repository is empty
- Wrong repository name

**Solution**:
```python
# Test connection and check data
from main import GraphDBClient

client = GraphDBClient("http://localhost:7200", "test_repo")

# Check total triples
query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
results = client.execute_query(query)
print("Total triples:", results["results"]["bindings"][0]["count"]["value"])

# Check classes
query = """
SELECT ?class (COUNT(?instance) as ?count)
WHERE { ?instance a ?class }
GROUP BY ?class
"""
results = client.execute_query(query)
for binding in results["results"]["bindings"]:
    print(f"- {binding['class']['value']}: {binding['count']['value']} instances")
```

#### 5. Survey Builder not loading questions from groups

**Problem**: Questions appear as "orphan" instead of under groups

**Cause**: Missing `QuestionFlow` relationships in the data

**Solution**:
This is expected if your data doesn't include explicit question ordering. You can:
1. Manually organize questions using drag-and-drop in the UI
2. Add `QuestionFlow` relationships in your RML mappings
3. Use the SPARQL interface to create custom queries that link questions to groups

#### 6. Import fails with "Invalid .lsq format"

**Problem**: Generated .lsq XML doesn't match LimeSurvey's schema

**Solution**:
- Ensure all required fields are present
- Check that question type codes are single characters (L, T, M, etc.)
- Verify variable names start with a letter and contain only alphanumerics
- Make sure mandatory/encrypted fields are Y or N (not 1/0)

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Areas for contribution:**
- Additional RML mappings for different LimeSurvey features
- Support for more question types
- Improved Survey Builder UI/UX
- Additional export formats
- Unit tests
- Documentation improvements

---

## Future Development

### Planned Features

**Docker Support** 🐳
- Complete Docker Compose setup with all components
- One-command deployment: `docker-compose up`
- Pre-configured containers for LimeSurvey, MySQL, GraphDB, and Survey Builder
- Volume management for persistent data

**Enhanced Features**
- Response data integration (not just structure)
- Version control for surveys
- Diff/merge capabilities for survey versions
- Multi-language survey support
- Advanced SPARQL query builder
- Survey templates and patterns
- Collaborative editing

### Roadmap

- **v2.0**: Docker containerization
- **v2.1**: Response data support
- **v2.2**: Survey versioning
- **v3.0**: Multi-user collaboration

Stay tuned for updates!

---

## License


```
MIT License

Copyright (c) 2025 LimeSurvey Knowledge Graph Suite Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- **LimeSurvey** for the survey management platform
- **GraphDB** by Ontotext for the triple store
- **RMLMapper** for RDF generation
- **Flask** for the web framework
- Contributors and community members

---

## Support

For issues, questions, or suggestions:

- 📧 Email: sara.zuppiroli@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/limesurvey-knowledge-graph/issues)
- 📖 Documentation: [GitHub Wiki](https://github.com/yourusername/limesurvey-knowledge-graph/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/limesurvey-knowledge-graph/discussions)

---

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{limesurvey_kg_suite,
  title = {LimeSurvey Knowledge Graph Suite},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/limesurvey-knowledge-graph}
}
```

---

**Made with ❤️ for the survey research community**