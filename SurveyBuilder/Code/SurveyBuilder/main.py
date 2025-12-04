"""
GraphDB Survey Builder - Flask Application
Python backend per interagire con GraphDB e costruire questionari LimeSurvey
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
from xml.dom import minidom
import requests
import base64

app = Flask(__name__)
CORS(app)

# Configurazione GraphDB
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY = "limesurvey"

# Configurazione LimeSurvey
LIMESURVEY_URL = "http://localhost:8080/index.php/admin/remotecontrol"
LIMESURVEY_USERNAME = "admin"
LIMESURVEY_PASSWORD = "password"


class LimeSurveyAPI:
    """Client per LimeSurvey RemoteControl API"""

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.session_key = None

    def _call(self, method: str, params: List) -> Any:
        """Effettua una chiamata RPC all'API di LimeSurvey"""
        payload = {
            "method": method,
            "params": params,
            "id": 1
        }

        print(f"DEBUG: Calling LimeSurvey method: {method}")
        print(f"DEBUG: URL: {self.url}")

        try:
            response = requests.post(self.url, json=payload, timeout=30)

            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response content type: {response.headers.get('content-type', 'unknown')}")

            # Check if response is HTML (error page)
            if 'text/html' in response.headers.get('content-type', ''):
                print(f"DEBUG: Received HTML instead of JSON")
                print(f"DEBUG: First 500 chars: {response.text[:500]}")
                raise Exception(
                    f"LimeSurvey returned HTML instead of JSON. Check if RemoteControl is enabled and URL is correct. URL: {self.url}")

            result = response.json()

            # Check for RPC error
            if "error" in result and result["error"]:
                error_msg = result["error"]
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", str(error_msg))
                print(f"DEBUG: API Error: {error_msg}")
                raise Exception(f"LimeSurvey API Error: {error_msg}")

            print(f"DEBUG: Success - Result: {str(result.get('result'))[:200]}")
            return result.get("result")

        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request failed: {e}")
            raise Exception(f"Failed to connect to LimeSurvey: {e}")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {e}")
            print(f"DEBUG: Response text: {response.text[:500]}")
            raise Exception(f"Invalid JSON response from LimeSurvey. Check if RemoteControl API is enabled.")

    def get_session_key(self) -> str:
        """Ottiene la session key per l'autenticazione"""
        if not self.session_key:
            self.session_key = self._call("get_session_key", [self.username, self.password])
            if not self.session_key or self.session_key == "null":
                raise Exception("Failed to authenticate with LimeSurvey")
        return self.session_key

    def release_session_key(self):
        """Rilascia la session key"""
        if self.session_key:
            self._call("release_session_key", [self.session_key])
            self.session_key = None

    def create_survey(self, title: str, language: str = "it") -> int:
        """Crea una nuova survey"""
        session_key = self.get_session_key()

        print(f"DEBUG: Creating survey with title: {title}, language: {language}")

        # Use a random survey ID (LimeSurvey will auto-generate)
        import random
        temp_sid = random.randint(100000, 999999)

        # Call con parametri corretti: session_key, sid, title, language, format
        survey_id = self._call("add_survey", [session_key, temp_sid, title, language, "G"])

        if not survey_id or survey_id == "null":
            raise Exception("Failed to create survey - no ID returned")

        print(f"DEBUG: Created survey with ID: {survey_id}")
        return int(survey_id)

    def add_group(self, survey_id: int, title: str, description: str = "", order: int = 0) -> int:
        """Aggiunge un gruppo alla survey"""
        session_key = self.get_session_key()


        group_id = self._call("add_group", [session_key, survey_id, title,description])
        print(f"Created group {title} with ID: {group_id}")
        return int(group_id)

    def add_question(self, survey_id: int, group_id: int, question_data: Dict, order: int = 0) -> int:
        """Aggiunge una domanda al gruppo"""
        session_key = self.get_session_key()

        q_data = {
            "title": question_data.get("code", f"Q{order}"),
            "question": question_data.get("text", ""),
            "type": question_data.get("type", "T"),
            "mandatory": "Y" if question_data.get("mandatory", False) else "N",
            "question_order": order
        }

        question_id = self._call("add_question", [session_key, survey_id, group_id, q_data])
        print(f"Created question {q_data['title']} with ID: {question_id}")
        return int(question_id)

    def activate_survey(self, survey_id: int):
        """Attiva la survey"""
        session_key = self.get_session_key()
        result = self._call("activate_survey", [session_key, survey_id])
        print(f"Survey {survey_id} activated")
        return result


class GraphDBClient:
    """Client per interagire con GraphDB"""

    def __init__(self, endpoint: str, repository: str):
        self.endpoint = f"{endpoint}/repositories/{repository}"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Esegue una query SPARQL e ritorna i risultati"""
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            return results
        except Exception as e:
            raise Exception(f"Errore query SPARQL: {str(e)}")

    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Recupera tutti i gruppi con le loro domande in un'unica query"""
        query = """
            PREFIX ns1: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX data: <https://w3id.org/fossr/data/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            SELECT ?group ?groupId ?groupName ?groupdescription
                   ?question ?questionId ?questionText ?variableCod ?questionType ?questionOrder
            WHERE {
                ?group a ns1:QuestionGroup .

                OPTIONAL {
                    ?group ns1:hasId ?identifier .
                    ?identifier ns1:id ?groupId .
                }

                OPTIONAL {
                    ?group ns1:hasName ?name .
                    ?name ns1:nameText ?groupName .
                }

                OPTIONAL {
                    ?group ns1:hasContent ?content .
                    ?content ns1:text ?groupdescription .
                }

                # Link question -> group
                OPTIONAL {
                    ?question ns1:hasGroup ?group .

                    OPTIONAL {
                        ?question ls:hasId ?Identifier .
                        ?Identifier ls:id ?questionId .
                    }

                    OPTIONAL {
                        ?question ls:hasContent ?Content .
                        ?Content ls:text ?questionText .
                    }

                    OPTIONAL { 
                        ?question ls:hasVariable ?var . 
                        ?var ls:variableCod ?variableCod .
                    }

                    OPTIONAL {
                        ?question ls:hasType ?type .
                        ?type ls:code ?questionType .
                    }

                    # Try to get order if available
                    OPTIONAL {
                        ?group ls:hasQuestionFlow ?flow .
                        ?flow ls:hasQuestionStep ?step .
                        ?step ls:hasQuestion ?question .
                        ?step ls:questionOrder ?questionOrder .
                    }
                }
            }
            ORDER BY ?groupId ?questionOrder ?questionId
        """

        print(f"DEBUG: Executing unified groups+questions query...")
        results = self.execute_query(query)

        # Process results - group by group URI
        groups_dict = {}

        for binding in results["results"]["bindings"]:
            group_uri = binding["group"]["value"]

            # Create group if not exists
            if group_uri not in groups_dict:
                groups_dict[group_uri] = {
                    "uri": group_uri,
                    "id": binding.get("groupId", {}).get("value", "N/A"),
                    "name": binding.get("groupName", {}).get("value", "Unnamed Group"),
                    "description": binding.get("groupdescription", {}).get("value", ""),
                    "type": "group",
                    "questions": []
                }

            # Add question if present
            if "question" in binding:
                question_uri = binding["question"]["value"]

                # Check if question already added (avoid duplicates)
                if not any(q["uri"] == question_uri for q in groups_dict[group_uri]["questions"]):
                    question = {
                        "uri": question_uri,
                        "id": binding.get("questionId", {}).get("value", "N/A"),
                        "text": binding.get("questionText", {}).get("value", "No text"),
                        "variableCod": binding.get("variableCod", {}).get("value", ""),
                        "questionType": binding.get("questionType", {}).get("value", "L"),
                        "order": binding.get("questionOrder", {}).get("value", "0"),
                        "groupUri": group_uri,
                        "type": "question"
                    }
                    groups_dict[group_uri]["questions"].append(question)

        # Convert to list
        groups = list(groups_dict.values())

        print(f"DEBUG: Found {len(groups)} groups")
        for group in groups:
            print(f"DEBUG: Group ID={group['id']}, Name={group['name']}, Questions={len(group['questions'])}")

        return groups

    def get_all_questions(self) -> List[Dict[str, Any]]:
        """Recupera tutte le domande"""
        query = """
            PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?question ?questionId ?questionText ?variableCod ?isMandatory ?questionType
            WHERE {
                ?question a ls:Question .
                OPTIONAL { 
                    ?question ls:hasId ?Identifier. 
                    ?Identifier ls:id ?questionId 
                }
                OPTIONAL { 
                    ?question ls:hasContent ?Content.
                    ?Content ls:text ?questionText 
                }
                OPTIONAL {
                    ?question ls:hasVariable ?var .
                    ?var ls:variableCod ?variableCod
                }
                OPTIONAL {
                    ?question ls:hasType ?type .
                    ?type ls:code ?questionType
                }
                OPTIONAL { ?question ls:isMandatory ?isMandatory }
            }
            ORDER BY ?questionId
        """

        print(f"DEBUG: Executing questions query...")
        results = self.execute_query(query)
        questions = []

        print(f"DEBUG: Found {len(results['results']['bindings'])} questions")

        for binding in results["results"]["bindings"]:
            question = {
                "uri": binding["question"]["value"],
                "id": binding.get("questionId", {}).get("value", "N/A"),
                "text": binding.get("questionText", {}).get("value", "No text"),
                "variableCod": binding.get("variableCod", {}).get("value", ""),
                "isMandatory": binding.get("isMandatory", {}).get("value", "0"),
                "questionType": binding.get("questionType", {}).get("value", "L"),
                "type": "question"
            }
            questions.append(question)
            print(f"DEBUG: Question found - ID: {question['id']}, Text: {question['text'][:50]}...")

        return questions

    def get_questions_by_group(self, group_uri: str) -> List[Dict[str, Any]]:
        """Recupera le domande di un gruppo specifico tramite QuestionFlow"""
        query = f"""
            PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?question ?questionId ?questionText ?variableCod ?questionOrder ?questionType
            WHERE {{
                # Percorso: Group -> QuestionFlow -> QuestionStep -> Question
                <{group_uri}> ls:hasQuestionFlow ?flow .
                ?flow ls:hasQuestionStep ?step .
                ?step ls:hasQuestion ?question .

                OPTIONAL {{ ?step ls:questionOrder ?questionOrder }}
                OPTIONAL {{ 
                    ?question ls:hasId ?Identifier. 
                    ?Identifier ls:id ?questionId 
                }}
                OPTIONAL {{ 
                    ?question ls:hasContent ?Content.
                    ?Content ls:text ?questionText 
                }}
                OPTIONAL {{
                    ?question ls:hasVariable ?var .
                    ?var ls:variableCod ?variableCod
                }}
                OPTIONAL {{
                    ?question ls:hasType ?type .
                    ?type ls:code ?questionType
                }}
            }}
            ORDER BY ?questionOrder
        """

        try:
            results = self.execute_query(query)
            questions = []

            for binding in results["results"]["bindings"]:
                question = {
                    "uri": binding["question"]["value"],
                    "id": binding.get("questionId", {}).get("value", "N/A"),
                    "text": binding.get("questionText", {}).get("value", "No text"),
                    "variableCod": binding.get("variableCod", {}).get("value", ""),
                    "order": binding.get("questionOrder", {}).get("value", "0"),
                    "questionType": binding.get("questionType", {}).get("value", "L"),
                    "groupUri": group_uri
                }
                questions.append(question)

            return questions
        except Exception as e:
            print(f"DEBUG: Error getting questions for group {group_uri}: {e}")
            return []

    def get_answer_options(self, question_uri: str) -> List[Dict[str, Any]]:
        """Recupera le opzioni di risposta per una domanda"""
        query = f"""
            PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

            SELECT ?answer ?answerCode ?answerText ?answerOrder ?assessmentValue
            WHERE {{
                <{question_uri}> ls:hasAnswerOption ?answer .
                OPTIONAL {{ ?answer ls:answerCode ?answerCode }}
                OPTIONAL {{ ?answer ls:answerText ?answerText }}
                OPTIONAL {{ ?answer ls:answerOrder ?answerOrder }}
                OPTIONAL {{ ?answer ls:assessmentValue ?assessmentValue }}
            }}
            ORDER BY ?answerOrder
        """

        results = self.execute_query(query)
        answers = []

        for binding in results["results"]["bindings"]:
            answer = {
                "code": binding.get("answerCode", {}).get("value", ""),
                "text": binding.get("answerText", {}).get("value", ""),
                "order": binding.get("answerOrder", {}).get("value", "0"),
                "assessmentValue": binding.get("assessmentValue", {}).get("value", "0")
            }
            answers.append(answer)

        return answers


class SurveyExporter:
    """Esportatore per questionari in vari formati"""

    @staticmethod
    def to_json(groups: List[Dict], questions: List[Dict]) -> str:
        """Esporta in formato JSON"""
        data = {
            "survey_info": {
                "title": "Nuovo Questionario",
                "created": datetime.now().isoformat(),
                "source": "GraphDB",
                "format_version": "1.0"
            },
            "groups": groups,
            "questions": questions
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def to_csv(groups: List[Dict], questions: List[Dict]) -> str:
        """Esporta in formato CSV compatibile con LimeSurvey"""
        output = io.StringIO()
        fieldnames = ['class', 'type/scale', 'name', 'relevance', 'text',
                      'help', 'language', 'mandatory', 'other']
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        # Survey header
        writer.writerow({
            'class': 'S',
            'name': 'Nuovo Questionario',
            'language': 'it'
        })

        # Groups and questions
        for group in groups:
            # Group row
            writer.writerow({
                'class': 'G',
                'name': group['name'],
                'text': group.get('description', ''),
                'relevance': '1'
            })

            # Questions in this group
            group_questions = [q for q in questions if q.get('groupUri') == group['uri']]
            for question in group_questions:
                writer.writerow({
                    'class': 'Q',
                    'type/scale': question.get('questionType', 'L'),
                    'name': question.get('variableCod', f"Q{question['id']}"),
                    'relevance': '1',
                    'text': question['text'].replace(';', ','),
                    'language': 'it',
                    'mandatory': 'Y' if question.get('isMandatory') == '1' else 'N',
                    'other': 'N'
                })

        # Standalone questions
        standalone = [q for q in questions if not q.get('groupUri')]
        for question in standalone:
            writer.writerow({
                'class': 'Q',
                'type/scale': question.get('questionType', 'L'),
                'name': question.get('variableCod', f"Q{question['id']}"),
                'relevance': '1',
                'text': question['text'].replace(';', ','),
                'language': 'it',
                'mandatory': 'Y' if question.get('isMandatory') == '1' else 'N',
                'other': 'N'
            })

        return output.getvalue()

    @staticmethod
    def to_lss_xml(groups: List[Dict], questions: List[Dict]) -> str:
        """Esporta in formato LSS XML (LimeSurvey native format)"""
        root = ET.Element("document")
        ET.SubElement(root, "LimeSurveyDocType").text = "Survey"
        ET.SubElement(root, "DBVersion").text = "600"

        # Languages
        languages = ET.SubElement(root, "languages")
        ET.SubElement(languages, "language").text = "it"

        # Survey
        surveys_elem = ET.SubElement(root, "surveys")
        survey_row = ET.SubElement(surveys_elem, "rows")
        fields = ET.SubElement(survey_row, "fields")

        ET.SubElement(fields, "field", name="sid").text = "1"
        ET.SubElement(fields, "field", name="owner_id").text = "1"
        ET.SubElement(fields, "field", name="admin").text = "Administrator"
        ET.SubElement(fields, "field", name="active").text = "N"
        ET.SubElement(fields, "field", name="language").text = "it"

        # Survey language settings
        survey_ls = ET.SubElement(root, "surveys_languagesettings")
        ls_row = ET.SubElement(survey_ls, "rows")
        ls_fields = ET.SubElement(ls_row, "fields")
        ET.SubElement(ls_fields, "field", name="surveyls_survey_id").text = "1"
        ET.SubElement(ls_fields, "field", name="surveyls_language").text = "it"
        ET.SubElement(ls_fields, "field", name="surveyls_title").text = "Nuovo Questionario"

        # Groups
        groups_elem = ET.SubElement(root, "groups")
        for idx, group in enumerate(groups, 1):
            group_row = ET.SubElement(groups_elem, "rows")
            group_fields = ET.SubElement(group_row, "fields")

            ET.SubElement(group_fields, "field", name="gid").text = str(group.get('id', idx))
            ET.SubElement(group_fields, "field", name="sid").text = "1"
            ET.SubElement(group_fields, "field", name="group_order").text = str(idx)

        # Pretty print
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        return xml_str


# Flask Routes
@app.route('/')
def index():
    """Pagina principale"""
    return render_template('index.html')


@app.route('/api/sparql/query', methods=['POST'])
def execute_sparql_query():
    """Esegue una query SPARQL custom sul repository"""
    try:
        data = request.json
        query = data.get('query', '')

        if not query or query.strip() == '':
            return jsonify({
                "status": "error",
                "message": "Query SPARQL vuota"
            }), 400

        print(f"\n{'=' * 70}")
        print(f"Executing custom SPARQL query:")
        print(query)
        print(f"{'=' * 70}\n")

        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        results = client.execute_query(query)

        # Format results for display
        bindings = results.get("results", {}).get("bindings", [])

        # Get column names from first result
        columns = []
        if bindings:
            columns = list(bindings[0].keys())

        # Format data
        formatted_results = []
        for binding in bindings:
            row = {}
            for col in columns:
                value = binding.get(col, {}).get("value", "")
                row[col] = value
            formatted_results.append(row)

        print(f"✓ Query executed successfully")
        print(f"✓ Found {len(formatted_results)} results")

        return jsonify({
            "status": "success",
            "columns": columns,
            "results": formatted_results,
            "count": len(formatted_results)
        })

    except Exception as e:
        print(f"✗ Query error: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/sparql/templates', methods=['GET'])
def get_sparql_templates():
    """Restituisce template di query SPARQL predefinite"""
    templates = [
        {
            "name": "Tutti i Gruppi",
            "description": "Elenca tutti i gruppi con ID e nome",
            "query": """PREFIX ns1: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT ?group ?groupId ?groupname ?groupdescription 
WHERE {
    ?group a ns1:QuestionGroup .

    OPTIONAL {
        ?group ns1:hasId ?identifier .
        ?identifier ns1:id ?groupId
    }

    OPTIONAL {
        ?group ns1:hasName ?name .
        ?name ns1:nameText ?groupname
    }

    OPTIONAL {
        ?group ns1:hasContent ?content .
        ?content ns1:text ?groupdescription
    }
}
ORDER BY ?groupId
LIMIT 100"""
        },
        {
            "name": "Tutte le Domande",
            "description": "Elenca tutte le domande con testo e variabile",
            "query": """PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT ?question ?questionId ?questionText ?variableCod ?questionType
WHERE {
    ?question a ls:Question .

    OPTIONAL { 
        ?question ls:hasId ?Identifier. 
        ?Identifier ls:id ?questionId 
    }

    OPTIONAL { 
        ?question ls:hasContent ?Content.
        ?Content ls:text ?questionText 
    }

    OPTIONAL {
        ?question ls:hasVariable ?var .
        ?var ls:variableCod ?variableCod
    }

    OPTIONAL {
        ?question ls:hasType ?type .
        ?type ls:code ?questionType
    }
}
ORDER BY ?questionId
LIMIT 100"""
        },
        {
            "name": "Gruppi con Domande",
            "description": "Mostra la relazione gruppo -> domande via QuestionFlow",
            "query": """PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT ?groupName ?questionText ?questionOrder
WHERE {
    ?group a ls:QuestionGroup .
    ?group ls:hasName ?name .
    ?name ls:nameText ?groupName .

    ?group ls:hasQuestionFlow ?flow .
    ?flow ls:hasQuestionStep ?step .
    ?step ls:hasQuestion ?question .
    ?step ls:questionOrder ?questionOrder .

    ?question ls:hasContent ?content .
    ?content ls:text ?questionText .
}
ORDER BY ?groupName ?questionOrder
LIMIT 100"""
        },
        {
            "name": "Conta Triple",
            "description": "Conta il numero totale di triple nel repository",
            "query": """SELECT (COUNT(*) as ?totalTriples)
WHERE {
    ?s ?p ?o
}"""
        },
        {
            "name": "Classi e Istanze",
            "description": "Mostra tutte le classi e il numero di istanze",
            "query": """SELECT ?class (COUNT(?instance) as ?count)
WHERE {
    ?instance a ?class .
}
GROUP BY ?class
ORDER BY DESC(?count)"""
        },
        {
            "name": "Domande per Gruppo Specifico",
            "description": "Trova tutte le domande di un gruppo (cambia 'Demografia')",
            "query": """PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT ?question ?questionText ?questionOrder
WHERE {
    ?group a ls:QuestionGroup .
    ?group ls:hasName ?name .
    ?name ls:nameText ?groupName .

    # Cambia "Demografia" con il nome del tuo gruppo
    FILTER(CONTAINS(LCASE(?groupName), "demografia"))

    ?group ls:hasQuestionFlow ?flow .
    ?flow ls:hasQuestionStep ?step .
    ?step ls:hasQuestion ?question .
    ?step ls:questionOrder ?questionOrder .

    ?question ls:hasContent ?content .
    ?content ls:text ?questionText .
}
ORDER BY ?questionOrder
LIMIT 100"""
        },
        {
            "name": "Struttura Completa",
            "description": "Mostra Survey → Gruppi → Domande",
            "query": """PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

SELECT ?survey ?groupName ?questionText
WHERE {
    ?survey a ls:Survey .
    ?survey ls:hasSurveyVersion ?version .
    ?version ls:hasGroupFlow ?gflow .
    ?gflow ls:hasGroupFlowStep ?gstep .
    ?gstep ls:hasQuestionGroup ?group .

    ?group ls:hasName ?gname .
    ?gname ls:nameText ?groupName .

    OPTIONAL {
        ?group ls:hasQuestionFlow ?qflow .
        ?qflow ls:hasQuestionStep ?qstep .
        ?qstep ls:hasQuestion ?question .
        ?question ls:hasContent ?qcontent .
        ?qcontent ls:text ?questionText .
    }
}
LIMIT 100"""
        }
    ]

    return jsonify({
        "status": "success",
        "templates": templates
    })


@app.route('/api/test', methods=['GET'])
def test_connection():
    """Testa la connessione e mostra statistiche del repository"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)

        # Query per contare tutti i triple
        count_query = """
            SELECT (COUNT(*) as ?count)
            WHERE {
                ?s ?p ?o
            }
        """

        # Query per contare le classi
        classes_query = """
            PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?class (COUNT(?instance) as ?count)
            WHERE {
                ?instance a ?class .
            }
            GROUP BY ?class
            ORDER BY DESC(?count)
        """

        # Query per trovare tutti i namespace
        namespaces_query = """
            SELECT DISTINCT ?namespace
            WHERE {
                {
                    ?s ?p ?o .
                    BIND(REPLACE(STR(?s), "(.*[/#])[^/#]*$", "$1") AS ?namespace)
                }
                UNION
                {
                    ?s ?p ?o .
                    BIND(REPLACE(STR(?p), "(.*[/#])[^/#]*$", "$1") AS ?namespace)
                }
            }
            LIMIT 20
        """

        count_results = client.execute_query(count_query)
        total_triples = count_results["results"]["bindings"][0]["count"]["value"]

        classes_results = client.execute_query(classes_query)
        classes = []
        for binding in classes_results["results"]["bindings"]:
            classes.append({
                "class": binding["class"]["value"],
                "count": binding["count"]["value"]
            })

        namespaces_results = client.execute_query(namespaces_query)
        namespaces = [b["namespace"]["value"] for b in namespaces_results["results"]["bindings"]]

        return jsonify({
            "status": "success",
            "connection": "OK",
            "repository": REPOSITORY,
            "total_triples": total_triples,
            "classes": classes,
            "namespaces": namespaces
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "help": "Verifica che GraphDB sia in esecuzione e che il repository contenga dati"
        }), 500


@app.route('/api/config', methods=['POST'])
def set_config():
    """Configura l'endpoint GraphDB"""
    global GRAPHDB_URL, REPOSITORY
    data = request.json
    GRAPHDB_URL = data.get('graphdb_url', GRAPHDB_URL)
    REPOSITORY = data.get('repository', REPOSITORY)
    return jsonify({"status": "ok", "graphdb_url": GRAPHDB_URL, "repository": REPOSITORY})


@app.route('/api/groups', methods=['GET'])
def get_groups():
    """Recupera tutti i gruppi"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        groups = client.get_all_groups()
        return jsonify({"status": "success", "groups": groups})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Recupera tutte le domande"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        questions = client.get_all_questions()
        return jsonify({"status": "success", "questions": questions})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/group/<path:group_uri>/questions', methods=['GET'])
def get_group_questions(group_uri):
    """Recupera le domande di un gruppo specifico"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        questions = client.get_questions_by_group(group_uri)
        return jsonify({"status": "success", "questions": questions})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/question/<path:question_uri>/answers', methods=['GET'])
def get_question_answers(question_uri):
    """Recupera le opzioni di risposta per una domanda"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        answers = client.get_answer_options(question_uri)
        return jsonify({"status": "success", "answers": answers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/export/json', methods=['POST'])
def export_json():
    """Esporta il questionario in formato JSON"""
    try:
        data = request.json
        groups = data.get('groups', [])
        questions = data.get('questions', [])

        json_output = SurveyExporter.to_json(groups, questions)

        return jsonify({
            "status": "success",
            "data": json_output
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """Esporta il questionario in formato CSV"""
    try:
        data = request.json
        groups = data.get('groups', [])
        questions = data.get('questions', [])

        csv_output = SurveyExporter.to_csv(groups, questions)

        return jsonify({
            "status": "success",
            "data": csv_output
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/export/lss', methods=['POST'])
def export_lss():
    """Esporta il questionario in formato LSS XML"""
    try:
        data = request.json
        groups = data.get('groups', [])
        questions = data.get('questions', [])

        lss_output = SurveyExporter.to_lss_xml(groups, questions)

        return jsonify({
            "status": "success",
            "data": lss_output
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/download/<format>', methods=['POST'])
def download_export(format):
    """Download del file esportato"""
    try:
        data = request.json
        groups = data.get('groups', [])
        questions = data.get('questions', [])

        if format == 'json':
            content = SurveyExporter.to_json(groups, questions)
            mimetype = 'application/json'
            filename = 'survey_export.json'
        elif format == 'csv':
            content = SurveyExporter.to_csv(groups, questions)
            mimetype = 'text/csv'
            filename = 'survey_export.csv'
        elif format == 'lss':
            content = SurveyExporter.to_lss_xml(groups, questions)
            mimetype = 'application/xml'
            filename = 'survey_export.lss'
        else:
            return jsonify({"status": "error", "message": "Formato non supportato"}), 400

        # Create in-memory file
        buffer = io.BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/limesurvey/create', methods=['POST'])
def create_limesurvey():
    """Crea una nuova survey su LimeSurvey"""
    try:
        data = request.json
        survey_title = data.get('title', 'New Survey')
        groups = data.get('groups', [])
        questions = data.get('questions', [])

        print(f"\n{'=' * 70}")
        print(f"Creating survey: {survey_title}")
        print(f"Groups: {len(groups)}, Questions: {len(questions)}")
        print(f"{'=' * 70}\n")

        # Validate
        if not survey_title or survey_title.strip() == "":
            return jsonify({
                "status": "error",
                "message": "Survey title is required"
            }), 400

        if len(groups) == 0 and len(questions) == 0:
            return jsonify({
                "status": "error",
                "message": "Seleziona almeno un gruppo o una domanda"
            }), 400

        # Inizializza client LimeSurvey
        print(f"Connecting to LimeSurvey at: {LIMESURVEY_URL}")
        ls_client = LimeSurveyAPI(LIMESURVEY_URL, LIMESURVEY_USERNAME, LIMESURVEY_PASSWORD)

        # Crea la survey
        print(f"Step 1: Creating survey '{survey_title}'...")
        survey_id = ls_client.create_survey(survey_title)
        print(f"✓ Survey created with ID: {survey_id}")

        # Mappa per tracciare gli ID dei gruppi creati
        group_map = {}

        # Aggiungi gruppi selezionati con le loro domande
        print(f"\nStep 2: Creating {len(groups)} groups...")
        for idx, group in enumerate(groups):
            order = group.get('order', idx + 1)
            print(f"  Creating group {idx + 1}/{len(groups)}: {group.get('name', 'Unnamed')}")
            print(group.get('name', f'Group {idx + 1}'),group.get('description', ''),"name senza +1",group.get('name') )
            try:
                group_id = ls_client.add_group( survey_id,group.get('name', f'Group {idx + 1}'),group.get('description', ''))
                group_map[group['uri']] = group_id
                print(f"  ✓ Group created with ID: {group_id}")

                # Aggiungi le domande di questo gruppo
                group_questions = group.get('questions', [])
                if group_questions:
                    print(f"    Adding {len(group_questions)} questions to this group...")
                    for q_idx, question in enumerate(group_questions):
                        q_order = question.get('order', q_idx + 1)
                        try:
                            q_id = ls_client.add_question(
                                survey_id,
                                group_id,
                                question.get('variableCod', f"Q{question.get('id', q_idx)}"),
                                question.get('text', ''),
                                question.get('questionType', 'T'),
                                question.get('isMandatory') == '1',
                                q_order
                            )
                            print(f"    ✓ Question {question.get('variableCod', 'Q?')} added (ID: {q_id})")
                        except Exception as e:
                            print(f"    ✗ Failed to add question: {e}")

            except Exception as e:
                print(f"  ✗ Failed to create group: {e}")
                raise

        # Aggiungi domande standalone (senza groupUri o non appartenenti a gruppi selezionati)
        selected_group_uris = [g['uri'] for g in groups]
        standalone_questions = [
            q for q in questions
            if not q.get('groupUri') or q.get('groupUri') not in selected_group_uris
        ]

        if standalone_questions:
            print(f"\nStep 3: Creating default group for {len(standalone_questions)} standalone questions...")
            default_group_id = ls_client.add_group(
                survey_id,
                "Altre Domande",
                "Domande senza gruppo specifico",
                len(groups) + 1
            )
            print(f"✓ Default group created with ID: {default_group_id}")

            for idx, question in enumerate(standalone_questions):
                order = question.get('order', idx + 1)
                print(f"  Adding question {idx + 1}/{len(standalone_questions)}: {question.get('variableCod', 'Q?')}")

                try:
                    q_id = ls_client.add_question(
                        survey_id,
                        default_group_id,
                        {
                            'code': question.get('variableCod', f"Q{question.get('id', idx)}"),
                            'text': question.get('text', ''),
                            'type': question.get('questionType', 'T'),
                            'mandatory': question.get('isMandatory') == '1'
                        },
                        order
                    )
                    print(f"  ✓ Question added (ID: {q_id})")
                except Exception as e:
                    print(f"  ✗ Failed to add question: {e}")

        # Rilascia la sessione
        print(f"\nStep 4: Releasing session...")
        ls_client.release_session_key()

        survey_url = LIMESURVEY_URL.replace('/admin/remotecontrol', '') + f"/admin/survey/sa/view/surveyid/{survey_id}"

        print(f"\n{'=' * 70}")
        print(f"✓ SUCCESS! Survey created successfully")
        print(f"Survey ID: {survey_id}")
        print(f"URL: {survey_url}")
        print(f"{'=' * 70}\n")

        return jsonify({
            "status": "success",
            "survey_id": survey_id,
            "message": f"Survey '{survey_title}' creata con successo con {len(groups)} gruppi!",
            "url": survey_url
        })

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"✗ ERROR: {str(e)}")
        print(f"{'=' * 70}\n")

        import traceback
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e),
            "help": "Verifica che LimeSurvey RemoteControl sia abilitato in config.php: $config['RPCInterface'] = 'json';"
        }), 500


@app.route('/api/limesurvey/config', methods=['POST'])
def set_limesurvey_config():
    """Configura le credenziali LimeSurvey"""
    global LIMESURVEY_URL, LIMESURVEY_USERNAME, LIMESURVEY_PASSWORD
    data = request.json
    LIMESURVEY_URL = data.get('url', LIMESURVEY_URL)
    LIMESURVEY_USERNAME = data.get('username', LIMESURVEY_USERNAME)
    LIMESURVEY_PASSWORD = data.get('password', LIMESURVEY_PASSWORD)
    return jsonify({"status": "ok"})


@app.route('/api/limesurvey/test', methods=['GET'])
def test_limesurvey():
    """Testa la connessione a LimeSurvey"""
    try:
        ls_client = LimeSurveyAPI(LIMESURVEY_URL, LIMESURVEY_USERNAME, LIMESURVEY_PASSWORD)
        session_key = ls_client.get_session_key()

        # Get list of surveys
        surveys = ls_client._call("list_surveys", [session_key])
        ls_client.release_session_key()

        return jsonify({
            "status": "success",
            "message": "Connessione riuscita!",
            "surveys_count": len(surveys) if surveys else 0
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("GraphDB Survey Builder - Flask Application")
    print("=" * 70)
    print(f"GraphDB URL: {GRAPHDB_URL}")
    print(f"Repository: {REPOSITORY}")
    print("\nServer starting on http://localhost:5005")
    print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5005)