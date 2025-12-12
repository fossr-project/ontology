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
REPOSITORY = "test_repo"

# Configurazione LimeSurvey
LIMESURVEY_URL = "http://localhost/limesurvey/index.php/admin/remotecontrol"
LIMESURVEY_USERNAME = "sara"
LIMESURVEY_PASSWORD = "sara"



# Generatore XML .lsq
#Genera file .lsq XML da dati completi della question
# ============================================
# NUOVO: Generatore .lsq XML
# ============================================

def generate_lsq_xml(question_data: Dict) -> str:
    """
    Genera file .lsq XML completo da dati GraphDB
    CORRETTO: rispetta validazione rigorosa di LimeSurvey
    """

    print(f"DEBUG: Generating .lsq XML for question {question_data.get('qid', 'unknown')}")

    root = ET.Element("document")
    ET.SubElement(root, "LimeSurveyDocType").text = "Question"
    ET.SubElement(root, "DBVersion").text = "623"

    # Languages
    languages = ET.SubElement(root, "languages")
    ET.SubElement(languages, "language").text = "it"

    # ===== QUESTIONS (main question) =====
    questions_elem = ET.SubElement(root, "questions")
    fields_elem = ET.SubElement(questions_elem, "fields")

    field_names = ["qid", "parent_qid", "sid", "gid", "type", "title", "preg", "other",
                   "mandatory", "encrypted", "question_order", "scale_id", "same_default",
                   "relevance", "question_theme_name", "modulename", "same_script"]

    for fname in field_names:
        ET.SubElement(fields_elem, "fieldname").text = fname

    rows_elem = ET.SubElement(questions_elem, "rows")
    row_elem = ET.SubElement(rows_elem, "row")

    # IMPORTANTE: NON usare CDATA in modo manuale, ET lo gestisce
    attrs = question_data.get('attributes', {})

    # QID - può essere vuoto per auto-generazione
    qid_elem = ET.SubElement(row_elem, "qid")
    qid_elem.text = ""  # Lascia vuoto per auto-generazione

    # Parent QID - DEVE essere 0 (numero, non stringa)
    parent_qid_elem = ET.SubElement(row_elem, "parent_qid")
    parent_qid_elem.text = "0"

    # SID - lascia vuoto, verrà assegnato da LimeSurvey
    sid_elem = ET.SubElement(row_elem, "sid")
    sid_elem.text = ""

    # GID - lascia vuoto, verrà assegnato da LimeSurvey
    gid_elem = ET.SubElement(row_elem, "gid")
    gid_elem.text = ""

    # TYPE - MAX 1 CARATTERE! Importantissimo
    question_type = question_data.get('type', 'T')
    if len(question_type) > 1:
        question_type = question_type[0]  # Prendi solo primo carattere
    type_elem = ET.SubElement(row_elem, "type")
    type_elem.text = question_type

    # TITLE (variableCod)
    title = question_data.get('title', 'Q1')
    # Valida: deve iniziare con lettera, solo alfanumerici
    import re
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', title):
        title = 'Q' + re.sub(r'[^a-zA-Z0-9_]', '', title)
        if not title[0].isalpha():
            title = 'Q' + title
    title_elem = ET.SubElement(row_elem, "title")
    title_elem.text = title

    # PREG - vuoto
    preg_elem = ET.SubElement(row_elem, "preg")

    # OTHER - DEVE essere Y o N (non "N" con CDATA)
    other_elem = ET.SubElement(row_elem, "other")
    other_elem.text = "N"

    # MANDATORY - DEVE essere Y o N
    mandatory = attrs.get('mandatory', 'N')
    if mandatory not in ['Y', 'N']:
        mandatory = 'Y' if mandatory == '1' else 'N'
    mandatory_elem = ET.SubElement(row_elem, "mandatory")
    mandatory_elem.text = mandatory

    # ENCRYPTED - DEVE essere Y o N
    encrypted_elem = ET.SubElement(row_elem, "encrypted")
    encrypted_elem.text = "N"

    # QUESTION_ORDER - numero
    question_order = attrs.get('question_order', '1')
    question_order_elem = ET.SubElement(row_elem, "question_order")
    question_order_elem.text = str(question_order)

    # SCALE_ID - DEVE essere numero
    scale_id_elem = ET.SubElement(row_elem, "scale_id")
    scale_id_elem.text = "0"

    # SAME_DEFAULT - DEVE essere 0 o 1 (numero)
    same_default_elem = ET.SubElement(row_elem, "same_default")
    same_default_elem.text = "0"

    # RELEVANCE
    relevance = attrs.get('relevance', '1')
    relevance_elem = ET.SubElement(row_elem, "relevance")
    relevance_elem.text = str(relevance)

    # QUESTION_THEME_NAME
    question_theme = attrs.get('question_theme_name', '')
    theme_elem = ET.SubElement(row_elem, "question_theme_name")
    theme_elem.text = question_theme if question_theme else ""

    # MODULENAME - vuoto
    module_elem = ET.SubElement(row_elem, "modulename")

    # SAME_SCRIPT - DEVE essere 0 o 1 (numero)
    same_script_elem = ET.SubElement(row_elem, "same_script")
    same_script_elem.text = "0"

    # ===== SUBQUESTIONS =====
    subquestions = question_data.get('subquestions', [])
    if subquestions:
        print(f"DEBUG: Adding {len(subquestions)} subquestions to XML")
        subq_elem = ET.SubElement(root, "subquestions")
        subq_fields = ET.SubElement(subq_elem, "fields")

        subq_field_names = ["qid", "parent_qid", "sid", "gid", "type", "title", "preg",
                            "other", "mandatory", "encrypted", "question_order", "scale_id",
                            "same_default", "relevance", "question_theme_name", "modulename",
                            "same_script", "id", "question", "help", "script", "language"]

        for fname in subq_field_names:
            ET.SubElement(subq_fields, "fieldname").text = fname

        subq_rows = ET.SubElement(subq_elem, "rows")

        for sub_idx, sub in enumerate(subquestions):
            subq_row = ET.SubElement(subq_rows, "row")

            # QID - vuoto
            ET.SubElement(subq_row, "qid")

            # PARENT_QID - vuoto, verrà collegato automaticamente
            ET.SubElement(subq_row, "parent_qid")

            # SID - vuoto
            ET.SubElement(subq_row, "sid")

            # GID - vuoto
            ET.SubElement(subq_row, "gid")

            # TYPE
            sub_type_elem = ET.SubElement(subq_row, "type")
            sub_type_elem.text = "T"

            # TITLE - DEVE iniziare con lettera!
            sub_title = sub.get('title', f'SQ{sub_idx + 1}')
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', sub_title):
                sub_title = 'SQ' + re.sub(r'[^a-zA-Z0-9_]', '', sub_title)
                if not sub_title[0].isalpha():
                    sub_title = 'SQ' + sub_title
            sub_title_elem = ET.SubElement(subq_row, "title")
            sub_title_elem.text = sub_title

            # PREG - vuoto
            ET.SubElement(subq_row, "preg")

            # OTHER
            sub_other_elem = ET.SubElement(subq_row, "other")
            sub_other_elem.text = "N"

            # MANDATORY
            sub_mand_elem = ET.SubElement(subq_row, "mandatory")
            sub_mand_elem.text = "N"

            # ENCRYPTED
            sub_enc_elem = ET.SubElement(subq_row, "encrypted")
            sub_enc_elem.text = "N"

            # QUESTION_ORDER
            sub_order = sub.get('order', str(sub_idx))
            sub_order_elem = ET.SubElement(subq_row, "question_order")
            sub_order_elem.text = str(sub_order)

            # SCALE_ID
            sub_scale_elem = ET.SubElement(subq_row, "scale_id")
            sub_scale_elem.text = "0"

            # SAME_DEFAULT
            sub_default_elem = ET.SubElement(subq_row, "same_default")
            sub_default_elem.text = "0"

            # RELEVANCE
            sub_rel_elem = ET.SubElement(subq_row, "relevance")
            sub_rel_elem.text = "1"

            # QUESTION_THEME_NAME - vuoto
            ET.SubElement(subq_row, "question_theme_name")

            # MODULENAME - vuoto
            ET.SubElement(subq_row, "modulename")

            # SAME_SCRIPT
            sub_script_elem = ET.SubElement(subq_row, "same_script")
            sub_script_elem.text = "0"

            # ID - vuoto
            ET.SubElement(subq_row, "id")

            # QUESTION (testo)
            sub_text = sub.get('text', '')
            sub_question_elem = ET.SubElement(subq_row, "question")
            sub_question_elem.text = sub_text

            # HELP - vuoto
            ET.SubElement(subq_row, "help")

            # SCRIPT - vuoto
            ET.SubElement(subq_row, "script")

            # LANGUAGE
            sub_lang_elem = ET.SubElement(subq_row, "language")
            sub_lang_elem.text = "it"

    # ===== QUESTION_L10NS =====
    ql10ns_elem = ET.SubElement(root, "question_l10ns")
    ql10ns_fields = ET.SubElement(ql10ns_elem, "fields")

    l10n_field_names = ["id", "qid", "question", "help", "script", "language"]
    for fname in l10n_field_names:
        ET.SubElement(ql10ns_fields, "fieldname").text = fname

    ql10ns_rows = ET.SubElement(ql10ns_elem, "rows")
    ql10ns_row = ET.SubElement(ql10ns_rows, "row")

    # ID - vuoto
    ET.SubElement(ql10ns_row, "id")

    # QID - vuoto
    ET.SubElement(ql10ns_row, "qid")

    # QUESTION (testo domanda)
    question_text = question_data.get('questionText', '')
    question_elem = ET.SubElement(ql10ns_row, "question")
    question_elem.text = question_text

    # HELP - vuoto
    ET.SubElement(ql10ns_row, "help")

    # SCRIPT - vuoto o da dati
    script_text = question_data.get('script', '')
    script_elem = ET.SubElement(ql10ns_row, "script")
    script_elem.text = script_text if script_text else ""

    # LANGUAGE
    lang_elem = ET.SubElement(ql10ns_row, "language")
    lang_elem.text = "it"

    # ===== QUESTION_ATTRIBUTES =====
    qattrs_elem = ET.SubElement(root, "question_attributes")
    qattrs_fields = ET.SubElement(qattrs_elem, "fields")

    ET.SubElement(qattrs_fields, "fieldname").text = "qid"
    ET.SubElement(qattrs_fields, "fieldname").text = "attribute"
    ET.SubElement(qattrs_fields, "fieldname").text = "value"
    ET.SubElement(qattrs_fields, "fieldname").text = "language"

    qattrs_rows = ET.SubElement(qattrs_elem, "rows")

    # Aggiungi attributi base necessari
    default_attributes = {
        'hidden': '0',
        'page_break': '0',
        'random_order': '0',
        'array_filter': '',
        'array_filter_exclude': '',
        'exclude_all_others': '',
        'hide_tip': '0',
        'time_limit': '',
        'time_limit_action': '1',
        'save_as_default': 'N'
    }

    # Merge con attributi dal GraphDB
    all_attributes = {**default_attributes, **attrs}

    # Rimuovi attributi che non devono andare in question_attributes
    excluded_attrs = ['mandatory', 'question_order', 'relevance', 'question_theme_name']
    for excluded in excluded_attrs:
        all_attributes.pop(excluded, None)

    for attr_name, attr_value in all_attributes.items():
        qattr_row = ET.SubElement(qattrs_rows, "row")

        qattr_qid = ET.SubElement(qattr_row, "qid")
        qattr_qid.text = ""

        qattr_name = ET.SubElement(qattr_row, "attribute")
        qattr_name.text = str(attr_name)

        qattr_value = ET.SubElement(qattr_row, "value")
        qattr_value.text = str(attr_value) if attr_value else ""

        # LANGUAGE - vuoto per attributi generali, "it" per localizzati
        qattr_lang = ET.SubElement(qattr_row, "language")
        if attr_name in ['prefix', 'suffix', 'em_validation_q_tip', 'em_validation_sq_tip']:
            qattr_lang.text = "it"
        else:
            qattr_lang.text = ""

    # ===== ANSWERS (Answer Options) =====
    answer_options = question_data.get('answerOptions', [])
    if answer_options:
        print(f"DEBUG: Adding {len(answer_options)} answer options to XML")

        answers_elem = ET.SubElement(root, "answers")
        answers_fields = ET.SubElement(answers_elem, "fields")

        answer_field_names = ["qid", "code", "answer", "sortorder", "assessment_value", "scale_id", "language"]
        for fname in answer_field_names:
            ET.SubElement(answers_fields, "fieldname").text = fname

        answers_rows = ET.SubElement(answers_elem, "rows")

        for ans in answer_options:
            ans_row = ET.SubElement(answers_rows, "row")

            # QID - vuoto
            ET.SubElement(ans_row, "qid")

            # CODE
            ans_code = ans.get('code', '')
            code_elem = ET.SubElement(ans_row, "code")
            code_elem.text = str(ans_code)

            # ANSWER (testo)
            ans_text = ans.get('text', '')
            answer_elem = ET.SubElement(ans_row, "answer")
            answer_elem.text = ans_text

            # SORTORDER - numero
            sort_order = ans.get('sortOrder', '0')
            sort_elem = ET.SubElement(ans_row, "sortorder")
            sort_elem.text = str(sort_order)

            # ASSESSMENT_VALUE - numero
            assessment = ans.get('assessmentValue', '0')
            assess_elem = ET.SubElement(ans_row, "assessment_value")
            assess_elem.text = str(assessment)

            # SCALE_ID - numero
            scale = ans.get('scaleId', '0')
            scale_elem = ET.SubElement(ans_row, "scale_id")
            scale_elem.text = str(scale)

            # LANGUAGE
            lang_elem = ET.SubElement(ans_row, "language")
            lang_elem.text = "it"
    print("ciao    ", ET.tostring(root))
    # Converti in stringa XML
    xml_str = ET.tostring(root, encoding='unicode', method='xml')

    # Pretty print con minidom
    try:
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding=None)

        # Rimuovi righe vuote extra
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        final_xml = '\n'.join(lines)

    except Exception as e:
        print(f"DEBUG: minidom parsing failed, using raw XML: {e}")
        final_xml = xml_str

    print(f"DEBUG: Generated .lsq XML ({len(final_xml)} bytes)")

    return final_xml

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

    def import_question(self, survey_id: int, group_id: int, lsq_base64: str,
                        mandatory: str = 'N') -> int:
        """
        Importa una domanda da file .lsq in formato Base64
        Usa la funzione import_question del RemoteControl API
        """
        session_key = self.get_session_key()

        print(f"DEBUG: Importing question to survey {survey_id}, group {group_id}")
        print(f"DEBUG: Base64 length: {len(lsq_base64)} chars")

        params = [
            session_key,
            survey_id,
            group_id,
            lsq_base64,
            'lsq',  # formato file
            mandatory  # obbligatorietà
        ]

        try:
            result = self._call("import_question", params)

            print(f"DEBUG: import_question result type: {type(result)}")
            print(f"DEBUG: import_question result: {result}")

            # Gestisci diverse risposte possibili
            if isinstance(result, dict):
                if 'status' in result and result['status'] == 'Error':
                    error_msg = result.get('message', 'Unknown error')
                    raise Exception(f"LimeSurvey import error: {error_msg}")

                # Potrebbe ritornare un dict con newqid
                if 'newqid' in result:
                    qid = int(result['newqid'])
                    print(f"DEBUG: Question imported successfully with ID: {qid}")
                    return qid

                # O un dict con qid
                if 'qid' in result:
                    qid = int(result['qid'])
                    print(f"DEBUG: Question imported successfully with ID: {qid}")
                    return qid

            # Se è direttamente un intero
            if isinstance(result, (int, str)):
                qid = int(result)
                print(f"DEBUG: Question imported successfully with ID: {qid}")
                return qid

            # Se non riesci a capire il formato, lancia errore
            raise Exception(f"Unexpected import_question response format: {result}")

        except Exception as e:
            print(f"DEBUG: import_question failed: {e}")
            raise


    def activate_survey(self, survey_id: int):
        """Attiva la survey"""
        session_key = self.get_session_key()
        result = self._call("activate_survey", [session_key, survey_id])
        print(f"Survey {survey_id} activated")
        return result

class GraphDBClient:


    def __init__(self, endpoint: str, repository: str):
        self.endpoint = f"{endpoint}/repositories/{repository}"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)

    def execute_query(self, query: str) -> Dict[str, Any]:
            #Esegue una query SPARQL e ritorna i risultati"""
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            return results
        except Exception as e:
            raise Exception(f"Errore query SPARQL: {str(e)}")

        # ... [mantieni tutti i metodi esistenti] ...

    def get_complete_question_data(self, question_uri: str) -> Dict[str, Any]:

        query = f"""
                PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
                PREFIX ns1: <https://w3id.org/fossr/ontology/limesurvey/>

                SELECT DISTINCT 
                  ?qid ?sid ?gid ?type ?title ?questionText ?script
                  ?attrName ?attrValue
                  ?parentQid
                  ?subQuestion ?subQid ?subTitle ?subQuestionText ?subOrder
                  ?answer ?answerCode ?answerText ?answerSortOrder ?answerAssessmentValue ?answerScaleId
                WHERE {{
                  <{question_uri}> a ls:Question .
                  <{question_uri}> ls:hasId ?idNode .
                  ?idNode ls:id ?qid .

                  OPTIONAL {{
                    <{question_uri}> ls:hasSurveyId ?sidNode .
                    ?sidNode ls:id ?sid .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasGroup ?groupNode .
                    ?groupNode ns1:hasId ?gidNode .
                    ?gidNode ns1:id ?gid .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasType ?typeNode .
                    ?typeNode ls:code ?type .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasVariable ?varNode .
                    ?varNode ls:variableCod ?title .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasContent ?contentNode .
                    ?contentNode ls:text ?questionText .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasContent ?contentNode .
                    ?contentNode ls:script ?script .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasComponentAttribute ?attr .
                    ?attr ls:componentName ?attrName .
                    ?attr ls:componentValue ?attrValue .
                  }}

                  OPTIONAL {{
                    <{question_uri}> ls:hasParentQuestion ?parentQuestion .
                    ?parentQuestion ls:hasId ?parentIdNode .
                    ?parentIdNode ls:id ?parentQid .
                  }}

                  OPTIONAL {{
                    ?subQuestion ls:hasParentQuestion <{question_uri}> .
                    ?subQuestion ls:hasId ?subIdNode .
                    ?subIdNode ls:id ?subQid .

                    OPTIONAL {{
                      ?subQuestion ls:hasVariable ?subVarNode .
                      ?subVarNode ls:variableCod ?subTitle .
                    }}

                    OPTIONAL {{
                      ?subQuestion ls:hasContent ?subContentNode .
                      ?subContentNode ls:text ?subQuestionText .
                    }}

                    OPTIONAL {{
                      ?subQuestion ls:hasComponentAttribute ?subOrderAttr .
                      ?subOrderAttr ls:componentName "question_order" .
                      ?subOrderAttr ls:componentValue ?subOrder .
                    }}
                  }}

                  OPTIONAL {{
                    ?answer a ls:AnswerOption .
                    <{question_uri}> ls:hasAnswerOption ?answer .

                    OPTIONAL {{
                      ?answer ls:componentValue ?answerCode .
                    }}

                    OPTIONAL {{
                      ?answer ls:hasContent ?answerContentNode .
                      ?answerContentNode ls:text ?answerText .
                    }}

                    OPTIONAL {{
                      ?answer ls:hasComponentAttribute ?answerAttr1 .
                      ?answerAttr1 ls:componentName "sortorder" .
                      ?answerAttr1 ls:componentValue ?answerSortOrder .
                    }}

                    OPTIONAL {{
                      ?answer ls:hasComponentAttribute ?answerAttr2 .
                      ?answerAttr2 ls:componentName "assessment_value" .
                      ?answerAttr2 ls:componentValue ?answerAssessmentValue .
                    }}

                    OPTIONAL {{
                      ?answer ls:hasComponentAttribute ?answerAttr3 .
                      ?answerAttr3 ls:componentName "scale_id" .
                      ?answerAttr3 ls:componentValue ?answerScaleId .
                    }}
                  }}
                }}
                ORDER BY ?qid ?subOrder ?answerSortOrder
            """

        print(f"DEBUG: Fetching complete data for question: {question_uri}")
        results = self.execute_query(query)
        return self._parse_complete_question_data(results)

    def _parse_complete_question_data(self, results: Dict) -> Dict[str, Any]:
            #"""Parser per organizzare tutti i dati della question"""
        bindings = results["results"]["bindings"]

        if not bindings:
            print("DEBUG: No data found for question")
            return None

            # Dati base dalla prima riga
        first_row = bindings[0]

        question_data = {
            "qid": first_row.get("qid", {}).get("value", "0"),
            "sid": first_row.get("sid", {}).get("value", "0"),
            "gid": first_row.get("gid", {}).get("value", "0"),
            "type": first_row.get("type", {}).get("value", "T"),
            "title": first_row.get("title", {}).get("value", "Q1"),
            "questionText": first_row.get("questionText", {}).get("value", ""),
            "script": first_row.get("script", {}).get("value", ""),
            "parentQid": first_row.get("parentQid", {}).get("value", "0"),
            "attributes": {},
            "subquestions": [],
            "answerOptions": []
        }

            # Usa set per evitare duplicati
        subquestions_map = {}
        answers_map = {}

            # Raccogli attributes, subquestions, answer options
        for row in bindings:
                # Attributes
            if "attrName" in row and row["attrName"].get("value"):
                attr_name = row["attrName"]["value"]
                attr_value = row.get("attrValue", {}).get("value", "")
                question_data["attributes"][attr_name] = attr_value

                # Subquestions
            if "subQid" in row and row["subQid"].get("value"):
                sub_qid = row["subQid"]["value"]
                if sub_qid not in subquestions_map:
                    subquestions_map[sub_qid] = {
                        "qid": sub_qid,
                        "title": row.get("subTitle", {}).get("value", ""),
                        "text": row.get("subQuestionText", {}).get("value", ""),
                        "order": row.get("subOrder", {}).get("value", "0")
                    }

                # Answer Options
            if "answer" in row and row["answer"].get("value"):
                answer_uri = row["answer"]["value"]
                if answer_uri not in answers_map:
                    answers_map[answer_uri] = {
                        "code": row.get("answerCode", {}).get("value", ""),
                        "text": row.get("answerText", {}).get("value", ""),
                        "sortOrder": row.get("answerSortOrder", {}).get("value", "0"),
                        "assessmentValue": row.get("answerAssessmentValue", {}).get("value", "0"),
                        "scaleId": row.get("answerScaleId", {}).get("value", "0")
                    }

            # Converti in liste
        question_data["subquestions"] = list(subquestions_map.values())
        question_data["answerOptions"] = list(answers_map.values())

            # Ordina subquestions e answers
        question_data["subquestions"].sort(key=lambda x: int(x.get("order", "0")))
        question_data["answerOptions"].sort(key=lambda x: int(x.get("sortOrder", "0")))

        print(f"DEBUG: Parsed question data:")
        print(f"  - QID: {question_data['qid']}")
        print(f"  - Type: {question_data['type']}")
        print(f"  - Subquestions: {len(question_data['subquestions'])}")
        print(f"  - Answer options: {len(question_data['answerOptions'])}")
        print(f"  - Attributes: {len(question_data['attributes'])}")

        return question_data

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
        query = """
            PREFIX ns1: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
            PREFIX data: <https://w3id.org/fossr/data/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

                 SELECT ?question ?questionId ?questionText ?variableCod ?isMandatory ?questionType
                        ?answerOptions ?answerCode ?answerText ?answerSortOrder ?answerAssessmentValue ?answerScaleId
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

                     OPTIONAL {
                         ?question ls:hasAnswerOption ?answerOptions .

                         OPTIONAL {
                             ?answerOptions ls:componentValue ?answerCode .
                         }

                         OPTIONAL {
                             ?answerOptions ls:hasContent ?answerContentNode .
                             ?answerContentNode ls:text ?answerText .
                         }

                         OPTIONAL {
                             ?answerOptions ls:hasComponentAttribute ?answerAttr1 .
                             ?answerAttr1 ls:componentName "sortorder" .
                             ?answerAttr1 ls:componentValue ?answerSortOrder .
                         }

                         OPTIONAL {
                             ?answerOptions ls:hasComponentAttribute ?answerAttr2 .
                             ?answerAttr2 ls:componentName "assessment_value" .
                             ?answerAttr2 ls:componentValue ?answerAssessmentValue .
                         }

                         OPTIONAL {
                             ?answerOptions ls:hasComponentAttribute ?answerAttr3 .
                             ?answerAttr3 ls:componentName "scale_id" .
                             ?answerAttr3 ls:componentValue ?answerScaleId .
                         }
                     }
                 }
                 ORDER BY ?questionId ?answerSortOrder
             """

        print(f"DEBUG: Executing questions query...")
        results = self.execute_query(query)

        # Raggruppa i risultati per domanda
        questions_dict = {}

        print(f"DEBUG: Found {len(results['results']['bindings'])} result rows")

        for binding in results["results"]["bindings"]:
            question_uri = binding["question"]["value"]

            # Se la domanda non è ancora nel dizionario, creala
            if question_uri not in questions_dict:
                questions_dict[question_uri] = {
                    "uri": question_uri,
                    "id": binding.get("questionId", {}).get("value", "N/A"),
                    "text": binding.get("questionText", {}).get("value", "No text"),
                    "variableCod": binding.get("variableCod", {}).get("value", ""),
                    "isMandatory": binding.get("isMandatory", {}).get("value", "0"),
                    "questionType": binding.get("questionType", {}).get("value", "L"),
                    "type": "question",
                    "answers": []
                }

            # Se c'è un'answer option, aggiungila alla lista
            if "answer" in binding:
                answer = {
                    "uri": binding["answer"]["value"],
                    "code": binding.get("answerCode", {}).get("value", ""),
                    "text": binding.get("answerText", {}).get("value", ""),
                    "sortOrder": binding.get("answerSortOrder", {}).get("value", ""),
                    "assessmentValue": binding.get("answerAssessmentValue", {}).get("value", ""),
                    "scaleId": binding.get("answerScaleId", {}).get("value", "0")
                }

                # Evita duplicati (possono verificarsi con OPTIONAL multipli)
                if answer not in questions_dict[question_uri]["answers"]:
                    questions_dict[question_uri]["answers"].append(answer)

        # Converti il dizionario in lista
        questions = list(questions_dict.values())

        print(f"DEBUG: Found {len(questions)} unique questions")


        return questions

    def get_all_questions_old(self) -> List[Dict[str, Any]]:
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


    def get_questions_by_group_old(self, group_uri: str) -> List[Dict[str, Any]]:
        """Recupera le domande di un gruppo specifico tramite QuestionFlow"""
        query = f"""
        PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
        PREFIX ns1: <https://w3id.org/fossr/ontology/limesurvey/>
        PREFIX data: <https://w3id.org/fossr/data/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT DISTINCT
            ?group 
            ?question ?questionId ?questionText ?variableCod ?questionType ?questionOrder
            ?parentQid
            ?subQuestion ?subQid ?subTitle ?subQuestionText ?subOrder
            ?answerOption ?answerCode ?answerText ?answerSortOrder ?answerAssessmentValue ?answerScaleId
        WHERE {{
            OPTIONAL {{
                ?question ns1:hasGroup <{group_uri}> .

                OPTIONAL {{
                    ?question ls:hasId ?Identifier .
                    ?Identifier ls:id ?questionId .
                }}

                OPTIONAL {{
                    ?question ls:hasContent ?Content .
                    ?Content ls:text ?questionText .
                }}

                OPTIONAL {{ 
                    ?question ls:hasVariable ?var . 
                    ?var ls:variableCod ?variableCod .
                }}

                OPTIONAL {{
                    ?question ls:hasType ?type .
                    ?type ls:code ?questionType .
                }}

                OPTIONAL {{
                    ?group ls:hasQuestionFlow ?flow .
                    ?flow ls:hasQuestionStep ?step .
                    ?step ls:hasQuestion ?question .
                    ?step ls:questionOrder ?questionOrder .
                }}

                OPTIONAL {{
                    ?question ls:hasParentQuestion ?parentQuestion .
                    ?parentQuestion ls:hasId ?parentIdNode .
                    ?parentIdNode ls:id ?parentQid .
                }}

                OPTIONAL {{
                    {{
                        ?subQuestion ls:hasParentQuestion ?question .
                        ?subQuestion ls:hasId ?subIdNode .
                        ?subIdNode ls:id ?subQid .

                        OPTIONAL {{
                            ?subQuestion ls:hasVariable ?subVarNode .
                            ?subVarNode ls:variableCod ?subTitle .
                        }}

                        OPTIONAL {{
                            ?subQuestion ls:hasContent ?subContentNode .
                            ?subContentNode ls:text ?subQuestionText .
                        }}

                        OPTIONAL {{
                            ?subQuestion ls:hasComponentAttribute ?subAttr .
                            ?subAttr ls:componentName "question_order" .
                            ?subAttr ls:componentValue ?subOrder .
                        }}
                    }}
                }}

                OPTIONAL {{
                    {{
                        ?question ls:hasAnswerOption ?ans .
                        BIND(?ans AS ?answerOption)

                        OPTIONAL {{ ?answerOption ls:componentValue ?answerCode . }}

                        OPTIONAL {{
                            ?answerOption ls:hasContent ?answerContentNode .
                            ?answerContentNode ls:text ?answerText .
                        }}

                        OPTIONAL {{
                            ?answerOption ls:hasComponentAttribute ?answerAttr1 .
                            ?answerAttr1 ls:componentName "sortorder" .
                            ?answerAttr1 ls:componentValue ?answerSortOrder .
                        }}

                        OPTIONAL {{
                            ?answerOption ls:hasComponentAttribute ?answerAttr2 .
                            ?answerAttr2 ls:componentName "assessment_value" .
                            ?answerAttr2 ls:componentValue ?answerAssessmentValue .
                        }}

                        OPTIONAL {{
                            ?answerOption ls:hasComponentAttribute ?answerAttr3 .
                            ?answerAttr3 ls:componentName "scale_id" .
                            ?answerAttr3 ls:componentValue ?answerScaleId .
                        }}
                    }}
                }}
            }}
        }}
        ORDER BY
            ?group
            ?questionOrder
            ?questionId
            ?subQid
            ?answerSortOrder
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


def get_complete_question_data(self, question_uri: str) -> Dict[str, Any]:
    """Recupera TUTTI i dati di una domanda per generare .lsq"""
    query = f"""
        PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT 
          ?qid ?sid ?gid ?type ?title ?questionText ?script
          ?attrName ?attrValue
          ?parentQid
          ?subQuestion ?subQid ?subTitle ?subQuestionText ?subOrder
          ?answer ?answerCode ?answerText ?answerSortOrder ?answerAssessmentValue ?answerScaleId
        WHERE {{
          <{question_uri}> a ls:Question .
          <{question_uri}> ls:hasId ?idNode .
          ?idNode ls:id ?qid .

          OPTIONAL {{
            <{question_uri}> ls:hasSurveyId ?sidNode .
            ?sidNode ls:id ?sid .
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasGroup ?groupNode .
            BIND(STRAFTER(STR(?groupNode), "group/") AS ?gid)
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasType ?typeNode .
            BIND(STRAFTER(STR(?typeNode), "questiontype/") AS ?type)
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasVariable ?varNode .
            ?varNode ls:variableCod ?title .
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasContent ?contentNode .
            ?contentNode ls:text ?questionText .
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasContent ?contentNode .
            ?contentNode ls:script ?script .
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasComponentAttribute ?attr .
            ?attr ls:componentName ?attrName .
            ?attr ls:componentValue ?attrValue .
          }}

          OPTIONAL {{
            <{question_uri}> ls:hasParentQuestion ?parentQuestion .
            ?parentQuestion ls:hasId ?parentIdNode .
            ?parentIdNode ls:id ?parentQid .
          }}

          OPTIONAL {{
            ?subQuestion ls:hasParentQuestion <{question_uri}> .
            ?subQuestion ls:hasId ?subIdNode .
            ?subIdNode ls:id ?subQid .

            OPTIONAL {{
              ?subQuestion ls:hasVariable ?subVarNode .
              ?subVarNode ls:variableCod ?subTitle .
            }}

            OPTIONAL {{
              ?subQuestion ls:hasContent ?subContentNode .
              ?subContentNode ls:text ?subQuestionText .
            }}

            OPTIONAL {{
              ?subQuestion ls:hasComponentAttribute ?subAttr .
              ?subAttr ls:componentName "question_order" .
              ?subAttr ls:componentValue ?subOrder .
            }}
          }}

          OPTIONAL {{
            ?answer a ls:AnswerOption .
            <{question_uri}> ls:hasAnswerOption ?answer .

            OPTIONAL {{
              ?answer ls:componentValue ?answerCode .
            }}

            OPTIONAL {{
              ?answer ls:hasContent ?answerContentNode .
              ?answerContentNode ls:text ?answerText .
            }}

            OPTIONAL {{
              ?answer ls:hasComponentAttribute ?answerAttr1 .
              ?answerAttr1 ls:componentName "sortorder" .
              ?answerAttr1 ls:componentValue ?answerSortOrder .
            }}

            OPTIONAL {{
              ?answer ls:hasComponentAttribute ?answerAttr2 .
              ?answerAttr2 ls:componentName "assessment_value" .
              ?answerAttr2 ls:componentValue ?answerAssessmentValue .
            }}

            OPTIONAL {{
              ?answer ls:hasComponentAttribute ?answerAttr3 .
              ?answerAttr3 ls:componentName "scale_id" .
              ?answerAttr3 ls:componentValue ?answerScaleId .
            }}
          }}
        }}
        ORDER BY ?qid ?subQid ?answerSortOrder
    """

    results = self.execute_query(query)
    return self._parse_complete_question_data(results)


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

    def _parse_complete_question_data(self, results: Dict) -> Dict[str, Any]:
        """Parser per organizzare tutti i dati della question"""
        bindings = results["results"]["bindings"]

        if not bindings:
            return None

        # Dati base dalla prima riga
        first_row = bindings[0]

        question_data = {
            "qid": first_row.get("qid", {}).get("value"),
            "sid": first_row.get("sid", {}).get("value"),
            "gid": first_row.get("gid", {}).get("value"),
            "type": first_row.get("type", {}).get("value", "T"),
            "title": first_row.get("title", {}).get("value"),
            "questionText": first_row.get("questionText", {}).get("value"),
            "script": first_row.get("script", {}).get("value", ""),
            "parentQid": first_row.get("parentQid", {}).get("value", "0"),
            "attributes": {},
            "subquestions": {},
            "answerOptions": {}
        }

        # Raccogli attributes, subquestions, answer options
        for row in bindings:
            # Attributes
            if "attrName" in row:
                attr_name = row["attrName"]["value"]
                attr_value = row.get("attrValue", {}).get("value", "")
                question_data["attributes"][attr_name] = attr_value

            # Subquestions
            if "subQid" in row:
                sub_qid = row["subQid"]["value"]
                if sub_qid not in question_data["subquestions"]:
                    question_data["subquestions"][sub_qid] = {
                        "qid": sub_qid,
                        "title": row.get("subTitle", {}).get("value", ""),
                        "text": row.get("subQuestionText", {}).get("value", ""),
                        "order": row.get("subOrder", {}).get("value", "0")
                    }

            # Answer Options
            if "answer" in row:
                answer_uri = row["answer"]["value"]
                if answer_uri not in question_data["answerOptions"]:
                    question_data["answerOptions"][answer_uri] = {
                        "code": row.get("answerCode", {}).get("value", ""),
                        "text": row.get("answerText", {}).get("value", ""),
                        "sortOrder": row.get("answerSortOrder", {}).get("value", "0"),
                        "assessmentValue": row.get("answerAssessmentValue", {}).get("value", "0"),
                        "scaleId": row.get("answerScaleId", {}).get("value", "0")
                    }

        return question_data



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
        graphdb_client = GraphDBClient(GRAPHDB_URL, REPOSITORY)

        # Crea la survey
        print(f"Step 1: Creating survey '{survey_title}'...")
        survey_id = ls_client.create_survey(survey_title)
        print(f"✓ Survey created with ID: {survey_id}")
        imported_questions_count = 0
        failed_questions = []

        # Step 2: Crea gruppi e importa domande
        print(f"\nStep 2: Creating groups and importing questions...")

        for group_idx, group in enumerate(groups):
            group_name = group.get('name', f'Group {group_idx + 1}')
            group_desc = group.get('description', '')
            group_order = group.get('order', group_idx + 1)

            print(f"\n  [{group_idx + 1}/{len(groups)}] Creating group: {group_name}")

            try:
                # Crea gruppo
                group_id = ls_client.add_group(
                    survey_id,
                    group_name,
                    group_desc,
                    group_order
                )
                print(f"  ✓ Group created with ID: {group_id}")

                # Trova domande di questo gruppo
                group_questions = [q for q in questions if q.get('groupUri') == group['uri']]

                if not group_questions:
                    print(f"  ⚠ No questions for this group")
                    continue

                print(f"  📊 Importing {len(group_questions)} questions...")

                # Importa ogni domanda
                for q_idx, question in enumerate(group_questions):
                    question_uri = question.get('uri')
                    question_title = question.get('variableCod', f"Q{q_idx + 1}")

                    print(f"    [{q_idx + 1}/{len(group_questions)}] Processing: {question_title}")

                    try:
                        # Ottieni dati completi se disponibili
                        if 'completeData' in question and question['completeData']:
                            complete_data = question['completeData']
                            print(f"      Using complete data from frontend")
                        else:
                            # Altrimenti recuperali dal GraphDB
                            print(f"      Fetching complete data from GraphDB...")
                            complete_data = graphdb_client.get_complete_question_data(question_uri)

                        if not complete_data:
                            print(f"      ✗ No data available, skipping")
                            failed_questions.append(f"{question_title}: No data available")
                            continue

                        # Aggiorna IDs per la nuova survey
                        complete_data['sid'] = str(survey_id)
                        complete_data['gid'] = str(group_id)

                        # Genera .lsq XML
                        print(f"      Generating .lsq XML...")
                        lsq_xml = generate_lsq_xml(complete_data)

                        # Converti in Base64
                        lsq_base64 = base64.b64encode(lsq_xml.encode('utf-8')).decode('utf-8')
                        print(f"      .lsq size: {len(lsq_xml)} bytes, Base64: {len(lsq_base64)} chars")

                        # Importa usando import_question
                        mandatory = complete_data.get('attributes', {}).get('mandatory', 'N')
                        print(f"      Importing to LimeSurvey (mandatory: {mandatory})...")

                        new_qid = ls_client.import_question(
                            survey_id=survey_id,
                            group_id=group_id,
                            lsq_base64=lsq_base64,
                            mandatory=mandatory
                        )

                        print(f"      ✓ Question imported successfully (new ID: {new_qid})")
                        imported_questions_count += 1

                    except Exception as e:
                        error_msg = f"{question_title}: {str(e)}"
                        print(f"      ✗ Failed: {e}")
                        failed_questions.append(error_msg)
                        continue

            except Exception as e:
                print(f"  ✗ Failed to create group: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Step 3: Rilascia sessione
        print(f"\nStep 3: Releasing session...")
        ls_client.release_session_key()

        # Genera URL
        survey_url = LIMESURVEY_URL.replace('/admin/remotecontrol', '') + f"/admin/survey/sa/view/surveyid/{survey_id}"

        print(f"\n{'=' * 70}")
        print(f"✓ Survey creation completed!")
        print(f"Survey ID: {survey_id}")
        print(f"Groups created: {len(groups)}")
        print(f"Questions imported: {imported_questions_count}/{len(questions)}")
        if failed_questions:
            print(f"Failed questions: {len(failed_questions)}")
            for failed in failed_questions:
                print(f"  - {failed}")


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


        response_data = {
            "status": "success",
            "survey_id": survey_id,
            "message": f"Survey '{survey_title}' creata con successo!",
            "url": survey_url,
            "importedQuestions": imported_questions_count,
            "totalQuestions": len(questions)
            }

        if failed_questions:
            response_data["failedQuestions"] = failed_questions
            response_data["message"] += f" ({imported_questions_count}/{len(questions)} domande importate)"

        return jsonify(response_data)

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"✗ ERROR: {str(e)}")
        print(f"{'=' * 70}\n")

    import traceback

    traceback.print_exc()

    return jsonify({
        "status": "error",
        "message": str(e)
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


@app.route('/api/question/<path:question_uri>/complete', methods=['GET'])
def get_complete_question(question_uri):
    """Recupera dati completi di una domanda per generare .lsq"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        question_data = client.get_complete_question_data(question_uri)

        if not question_data:
            return jsonify({
                "status": "error",
                "message": "Question not found"
            }), 404

        return jsonify({
            "status": "success",
            "data": question_data
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/generate_lsq', methods=['POST'])
def generate_lsq_endpoint():
    """Genera file .lsq da question URIs"""
    try:
        data = request.json
        question_uris = data.get('questionUris', [])

        if not question_uris:
            return jsonify({
                "status": "error",
                "message": "No questions provided"
            }), 400

        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        lsq_files = []

        for uri in question_uris:
            question_data = client.get_complete_question_data(uri)
            if question_data:
                lsq_xml = generate_lsq_xml(question_data)
                lsq_base64 = base64.b64encode(lsq_xml.encode('utf-8')).decode('utf-8')

                lsq_files.append({
                    "questionUri": uri,
                    "qid": question_data["qid"],
                    "title": question_data["title"],
                    "lsqBase64": lsq_base64
                })

        return jsonify({
            "status": "success",
            "lsqFiles": lsq_files
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