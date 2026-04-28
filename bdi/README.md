# 🧠 BDI Ontology (Belief–Desire–Intention)

This repository provides an OWL ontology for modelling **rational agents and their mental states** according to the **Belief–Desire–Intention (BDI)** paradigm.

👉 **Ontology file:**  
https://w3id.org/fossr/ontology/bdi

---

## 📌 Overview

The **BDI Ontology** is a modular **Ontology Design Pattern (ODP)** that captures the **cognitive architecture of agents** through:

- **Beliefs** (informational dimension)  
- **Desires** (motivational dimension)  
- **Intentions** (deliberative/commitment dimension)  

and their **dynamic interrelations**.

It provides a **formal, semantically grounded representation of agency**, enabling explicit modelling of how agents:
- perceive the world  
- deliberate over goals  
- form intentions  
- and act accordingly  

The ontology ensures **semantic interoperability**, **reusability**, and compliance with **Semantic Web standards**.

---

## 🖼️ Conceptual Overview

![BDI Ontology Diagram](https://raw.githubusercontent.com/fossr-project/ontology/refs/heads/main/bdi/bdi.png)

*Figure: Conceptual diagram of the BDI Ontology, showing relations between agents, mental states, plans, and the world.*

---

## 🎯 Purpose

The ontology is designed to act as both:

- a **conceptual model** for representing mental states and agency  
- an **operational bridge** between symbolic knowledge and executable reasoning  

It supports:

- Explainable AI (XAI)  
- Neuro-symbolic AI  
- Multi-agent systems  
- Semantic Web interoperability  

It enables a **bidirectional link between RDF data and agent cognition**, supporting paradigms such as *Triples-to-Beliefs-to-Triples (T2B2T)*.

---

## 🧩 Core Concepts

### Agents
- `bdi:Agent` — autonomous entities capable of reasoning and acting  

### Mental Entities
- `bdi:MentalEntity`
  - `bdi:Belief`
  - `bdi:Desire`
  - `bdi:Intention`
  - `bdi:Justification`

Mental states are modelled as **endurants**.

---

### Mental Processes
- `bdi:MentalProcess`

Mental processes are **perdurants** that:
- generate  
- modify  
- suppress mental states  

---

### World Representation
- `bdi:WorldState`

Represents a **contextualised environmental situation** that grounds mental states.

---

### Goals and Planning
- `bdi:Goal`
- `bdi:Plan`
- `bdi:Task`

Plans are structured sequences of tasks aimed at achieving goals.

---

### Temporal Dimension
- `bdi:TemporalEntity`
  - `bdi:TimeInstant`
  - `bdi:TimeInterval`

Mental entities are temporally contextualised via:
- `bdi:atTime`
- `bdi:hasValidity`

---

## 🔄 Modelling Rationale

The ontology distinguishes between:

- **Mental states (endurants)** — beliefs, desires, intentions  
- **Mental processes (perdurants)** — reasoning activities  

It adopts a **pattern-based design** grounded in:

- DOLCE foundational ontology  
- Ontology Design Patterns (ODPs), including:
  - EventCore  
  - Situation  
  - Provenance  
  - BasicPlan  
  - TimeIndexedSituation  

This ensures modularity, reuse, and semantic precision.

---

## 🔍 Competency Questions

The ontology is driven by competency questions (CQs) organised into four groups:

### 1. World, Agents, and Mental Entities
- What are mental entities?
- What mental states (i.e. befiefs, desires, and intentions) does an agent hold?
- What are the constituent mental entities that form part of a given mental entity?
- What mental processes has an agent undergone?
- What is the world state that a given mental state is about?
### 2. Dynamics of Mental States
- What beliefs motivated the formation of a given desire?
- Which desire does a particular intention fulfil?
- Which mental process generated a given belief, desire, or intention?
- When was a mental entity generated?
- What triggered a mental process?
- What justifications support a specific mental entity?
### 3. Goals and planning
- What goal does a given intention or plan aim to fulfil?
- What plan has been specified by a particular intention?
- What planning process led to the creation of a particular plan?
- What is the ordered sequence of tasks that compose a given plan?
### 4. Temporal reasoning
- What is the temporal validity (start and end time) of a mental state?
- What mental states were valid at a specific point in time?
- How has a mental entity evolved over time?

The functional commitment of the ontology has been rigorously validated using [OWLUnit](https://github.com/luigi-asprino/owl-unit), 
a framework for ontology unit testing that verifies the alignment between expected and actual reasoning
outcomes. All CQs, which identify unit tests, are associated with SPARQL queries and validation artefacts in the ontology with the OWLUnit vocabulary.
All unit tests are explained in a dedicated [document](unittesting.md).

---

## ⚙️ Implementation

- **Language:** OWL 2  
- **Classes:** 22  
- **Object properties:** 71  
- **Axioms:** 547  

The ontology:
- is version-controlled on GitHub  
- uses persistent URIs (`https://w3id.org/fossr/ontology/bdi/`)  
- supports RDF/XML, Turtle, and N-Triples  

It also includes:
- alignment with DOLCE+DnS UltraLite (DUL)  
- OPLaX annotations linking:
  - competency questions  
  - SPARQL queries  

---

## 🧪 Validation

The ontology is validated using:

- SPARQL queries for competency questions  
- OWLUnit (ontology unit testing framework)  
- OPLaX annotations for traceability  

All validation artefacts are available in the repository.

---

## 🔗 Use Cases

- Multi-agent systems  
- Explainable AI  
- Cognitive modelling  
- Decision-support systems  
- Semantic Web applications  

---

## 📁 Repository Structure

- `bdi/bdi.rdf` — OWL ontology  
- `bdi.ttl` — Turtle serialisation  
- `bdi.png` — conceptual diagram  
- `bdi.graphml` — graph representation  
- `tests/` — SPARQL queries and validation  

---

## 📜 License

This ontology is released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

https://creativecommons.org/licenses/by/4.0/

---

## 🤝 Contributing

Contributions are welcome:
- ontology extensions  
- alignments with other ontologies  
- datasets and SPARQL queries  
- tooling and reasoning support  

---

## 📚 Reference

If you use this ontology, please cite:

Zuppiroli, S., Longo, C. F., Lippolis, A. S., Paolillo, R., Giammei, L., Ceriani, M., Poggi, F., Zinilli, A., Nuzzolese, A. G.  
*The Belief-Desire-Intention Ontology for modelling mental reality and agency*
