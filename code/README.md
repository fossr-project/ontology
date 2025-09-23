# BDI + MS-LaTTE: Data Cleaning & Validation Experiments

A small toolkit to (1) clean MS-LaTTE task annotations into a high-agreement dataset and (2) run BDI-augmented vs. plain LLM validations, saving results.

--------------------------------------------------------------------------------

## Repository files


├─ clean-original-data.py          # cleans raw MS-LaTTE annotations
├─ bdi-experiment.py               # runs BDI-vs-plain validation experiments
├─ MS-LaTTE.json                   # input 
├─ filtered_tasks.csv              # output 
├─ controversial_tasks.json        # output 
├─ bdi_validation_results.json     # output 
└─ bdi_comparison_report.html      # output 

--------------------------------------------------------------------------------

## Quickstart

### 1) Environment

python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows (PowerShell)
 .venv\Scripts\Activate.ps1

pip install -U openai

# Set API key (recommended)
# Linux/Mac:
export OPENAI_API_KEY=sk-...
# Windows (PowerShell):
 $env:OPENAI_API_KEY="sk-..."


### 2) Data Cleaning (MS-LaTTE → CSV/JSON)

The cleaning script reads MS-LaTTE.json, computes consensus for Location and Time tags, and writes:

- filtered_tasks.csv — high-agreement items
- controversial_tasks.json — the “least clear” items for manual review

Run:
python clean-original-data.py

Consensus thresholds (defaults in code):
- LOC_THRESHOLD = 0.70   # majority share for Location
- TIME_THRESHOLD = 0.65  # per-tag share for Time; multiple Time tags may pass

Notes:
- MAX_CONTROVERSIAL = 50 keeps the top-N most ambiguous tasks.
- Outputs are overwritten each run.

### 3) BDI Validation Experiments

This script loads a BDI ontology and queries an LLM twice per test:
1) baseline (no ontology)
2) with the ontology injected in the system prompt

It saves both responses and an HTML diff-like report.

Run:
python bdi-experiment.py

Outputs:
- bdi_validation_results.json — raw side-by-side completions

Configuration (inside bdi-experiment.py):
- Model: gpt-4o (chat)
- Ontology path: bdi-v0.2.rdf


--------------------------------------------------------------------------------

## Inputs

### A) MS-LaTTE Task (expected fields)

Minimal example for each task in MS-LaTTE.json:

{
  "ID": "task-00123",
  "TaskTitle": "Pick up groceries from the store",
  "ListTitle": "Errands",
  "LocJudgements": [
    { "Known": true, "Locations": ["home"] },
    { "Known": true, "Locations": ["supermarket"] }
  ],
  "TimeJudgements": [
    { "Known": true, "Times": "WD-morning, WD-afternoon" },
    { "Known": true, "Times": "WD-morning" }
  ]
}

Field names can be adapted if your raw file uses slightly different keys, but keep the structure (IDs, titles, lists of location/time judgements).

### B) Time Taxonomy

Time tags combine day type and part of day:

- Weekday (WD): WD-morning, WD-afternoon, WD-evening, WD-night
- Weekend (WE): WE-morning, WE-afternoon, WE-evening, WE-night

Keep this taxonomy consistent in both annotations and ontology.

### C) Ontology

- File: bdi-v0.2.rdf 


--------------------------------------------------------------------------------

## Outputs

### filtered_tasks.csv
Columns:
- ID
- TaskTitle
- ListTitle
- Location     — consensus Location label
- Times        — semicolon-separated set of Time tags that pass the threshold
- LocShare     — share/proportion of the consensus Location

### controversial_tasks.json
- The original task objects for the least clear cases, sorted by ambiguity.

### bdi_validation_results.json
- For each test: test name, test data, the query, the baseline response, and the ontology-conditioned response.

