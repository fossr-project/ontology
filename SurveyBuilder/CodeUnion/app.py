from flask import Flask, render_template, request, jsonify, send_file
import requests
import json
import csv
import os
import io
from typing import Optional, Union
from datetime import datetime
import base64
import pandas as pd
import sys
from pathlib import Path

# Aggiungi lib/ al PYTHONPATH
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

# Ora importa pyrml normalmente
from pyrml import Mapper, PyRML

# from pyrml import Mapper, PyRML
from rdflib import Graph
from typing import Dict, List, Any
from xml.dom import minidom
from SPARQLWrapper import SPARQLWrapper, JSON
import subprocess
import logging

logger = logging.getLogger(__name__)

import xml.etree.ElementTree as ET

# Configurazione GraphDB
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY = "test_repo"

# Configurazione LimeSurvey
LIMESURVEY_URL = "http://localhost/limesurvey/index.php/admin/remotecontrol"
LIMESURVEY_USERNAME = "sara"
LIMESURVEY_PASSWORD = "sara"


# FUNZIONI PER BUILDER SURVEY
def generate_lsq_xml(question_data: Dict) -> str:
    """
    Genera file .lsq XML completo da dati GraphDB
    BASATO SU ESEMPIO FUNZIONANTE DA LIMESURVEY
    """

    print(f"DEBUG: Generating .lsq XML for question {question_data.get('qid', 'unknown')}")

    # Normalizza struttura dati
    subquestions = data_structure(question_data, 'subquestions')
    answer_options = data_structure(question_data, 'answerOptions')

    question_data['subquestions'] = subquestions
    question_data['answerOptions'] = answer_options

    print(f"DEBUG: Normalized - {len(subquestions)} subquestions, {len(answer_options)} answer options")

    # USA QID REALE dal GraphDB
    main_qid = str(question_data.get('qid', ''))
    main_sid = str(question_data.get('sid', ''))
    main_gid = str(question_data.get('gid', ''))

    print(f"DEBUG: Using QID={main_qid}, SID={main_sid}, GID={main_gid}")

    root = ET.Element("document")
    ET.SubElement(root, "LimeSurveyDocType").text = "Question"
    ET.SubElement(root, "DBVersion").text = "623"

    languages = ET.SubElement(root, "languages")
    ET.SubElement(languages, "language").text = "it"

    # ===== MAIN QUESTION =====
    questions_elem = ET.SubElement(root, "questions")
    fields_elem = ET.SubElement(questions_elem, "fields")

    field_names = ["qid", "parent_qid", "sid", "gid", "type", "title", "preg", "other",
                   "mandatory", "encrypted", "question_order", "scale_id", "same_default",
                   "relevance", "question_theme_name", "modulename", "same_script"]

    for fname in field_names:
        ET.SubElement(fields_elem, "fieldname").text = fname

    rows_elem = ET.SubElement(questions_elem, "rows")
    row_elem = ET.SubElement(rows_elem, "row")

    attrs = question_data.get('attributes', {})

    # QID dal GraphDB
    qid_elem = ET.SubElement(row_elem, "qid")
    qid_elem.text = main_qid

    # Parent QID = 0
    parent_qid_elem = ET.SubElement(row_elem, "parent_qid")
    parent_qid_elem.text = "0"

    # SID dal GraphDB
    sid_elem = ET.SubElement(row_elem, "sid")
    sid_elem.text = main_sid

    # GID dal GraphDB
    gid_elem = ET.SubElement(row_elem, "gid")
    gid_elem.text = main_gid

    # TYPE
    question_type = question_data.get('type', 'T')
    if len(question_type) > 1:
        question_type = question_type[0]
    type_elem = ET.SubElement(row_elem, "type")
    type_elem.text = question_type
    print(f"DEBUG: Question type: {question_type}")

    # TITLE
    title = question_data.get('title', 'Q1')
    import re
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', title):
        title = 'Q' + re.sub(r'[^a-zA-Z0-9_]', '', title)
        if not title[0].isalpha():
            title = 'Q' + title
    title_elem = ET.SubElement(row_elem, "title")
    title_elem.text = title

    # PREG
    ET.SubElement(row_elem, "preg")

    # OTHER
    other_elem = ET.SubElement(row_elem, "other")
    other_elem.text = "N"

    # MANDATORY
    mandatory = attrs.get('mandatory', 'N')
    if mandatory not in ['Y', 'N']:
        mandatory = 'Y' if mandatory == '1' else 'N'
    mandatory_elem = ET.SubElement(row_elem, "mandatory")
    mandatory_elem.text = mandatory

    # ENCRYPTED
    encrypted_elem = ET.SubElement(row_elem, "encrypted")
    encrypted_elem.text = "N"

    # QUESTION_ORDER
    question_order = attrs.get('question_order', '1')
    question_order_elem = ET.SubElement(row_elem, "question_order")
    question_order_elem.text = str(question_order)

    # SCALE_ID
    scale_id_elem = ET.SubElement(row_elem, "scale_id")
    scale_id_elem.text = "0"

    # SAME_DEFAULT
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

    # MODULENAME
    ET.SubElement(row_elem, "modulename")

    # SAME_SCRIPT
    same_script_elem = ET.SubElement(row_elem, "same_script")
    same_script_elem.text = "0"

    # ===== SUBQUESTIONS =====
    if subquestions and len(subquestions) > 0:
        print(f"DEBUG: Adding {len(subquestions)} subquestions to XML")
        subq_elem = ET.SubElement(root, "subquestions")
        subq_fields = ET.SubElement(subq_elem, "fields")

        # ESATTAMENTE come nell'esempio funzionante!
        subq_field_names = ["qid", "parent_qid", "sid", "gid", "type", "title", "preg",
                            "other", "mandatory", "encrypted", "question_order", "scale_id",
                            "same_default", "relevance", "question_theme_name", "modulename",
                            "same_script", "id", "question", "help", "script", "language"]

        for fname in subq_field_names:
            ET.SubElement(subq_fields, "fieldname").text = fname

        subq_rows = ET.SubElement(subq_elem, "rows")

        for sub_idx, sub in enumerate(subquestions):
            subq_row = ET.SubElement(subq_rows, "row")

            # QID della subquestion
            sub_qid = sub.get('qid', f"{main_qid}{sub_idx + 1}")
            qid_sub = ET.SubElement(subq_row, "qid")
            qid_sub.text = str(sub_qid)

            # PARENT_QID - Collegato alla main question!
            parent_qid_sub = ET.SubElement(subq_row, "parent_qid")
            parent_qid_sub.text = main_qid

            # SID - Stesso della main
            sid_sub = ET.SubElement(subq_row, "sid")
            sid_sub.text = main_sid

            # GID - Stesso della main
            gid_sub = ET.SubElement(subq_row, "gid")
            gid_sub.text = main_gid

            # TYPE - Sempre "T" per subquestions!
            sub_type_elem = ET.SubElement(subq_row, "type")
            sub_type_elem.text = "T"

            # TITLE
            sub_title = sub.get('title', f'SQ{sub_idx + 1}')
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', sub_title):
                sub_title = 'SQ' + re.sub(r'[^a-zA-Z0-9_]', '', sub_title)
                if not sub_title[0].isalpha():
                    sub_title = 'SQ' + sub_title
            sub_title_elem = ET.SubElement(subq_row, "title")
            sub_title_elem.text = sub_title

            # PREG
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

            # QUESTION_THEME_NAME
            ET.SubElement(subq_row, "question_theme_name")

            # MODULENAME
            ET.SubElement(subq_row, "modulename")

            # SAME_SCRIPT
            sub_script_elem = ET.SubElement(subq_row, "same_script")
            sub_script_elem.text = "0"

            # ID (campo separato)
            id_elem = ET.SubElement(subq_row, "id")
            id_elem.text = str(sub_qid)

            # QUESTION (testo subquestion - IMPORTANTE!)
            sub_text = sub.get('text', sub.get('title', ''))
            sub_question_elem = ET.SubElement(subq_row, "question")
            sub_question_elem.text = sub_text

            # HELP
            ET.SubElement(subq_row, "help")

            # SCRIPT
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

    # ID - Stesso del QID
    id_l10n = ET.SubElement(ql10ns_row, "id")
    id_l10n.text = main_qid

    # QID
    qid_l10n = ET.SubElement(ql10ns_row, "qid")
    qid_l10n.text = main_qid

    # QUESTION (testo main question - IMPORTANTE!)
    question_text = question_data.get('questionText', '')
    question_elem = ET.SubElement(ql10ns_row, "question")
    question_elem.text = question_text

    # HELP
    ET.SubElement(ql10ns_row, "help")

    # SCRIPT
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

    # Attributi default necessari
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

    # Rimuovi attributi che non vanno in question_attributes
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

        qattr_lang = ET.SubElement(qattr_row, "language")
        if attr_name in ['prefix', 'suffix', 'em_validation_q_tip', 'em_validation_sq_tip']:
            qattr_lang.text = "it"
        else:
            qattr_lang.text = ""

    # ===== ANSWERS (Answer Options) =====
    if answer_options and len(answer_options) > 0:
        print(f"DEBUG: Adding {len(answer_options)} answer options to XML")

        answers_elem = ET.SubElement(root, "answers")
        answers_fields = ET.SubElement(answers_elem, "fields")

        answer_field_names = ["qid", "code", "answer", "sortorder", "assessment_value", "scale_id", "language"]
        for fname in answer_field_names:
            ET.SubElement(answers_fields, "fieldname").text = fname

        answers_rows = ET.SubElement(answers_elem, "rows")

        for ans_idx, ans in enumerate(answer_options):
            ans_row = ET.SubElement(answers_rows, "row")

            # ✅ QID - Collegato alla main question
            ans_qid = ET.SubElement(ans_row, "qid")
            ans_qid.text = main_qid

            # CODE
            ans_code = ans.get('code', str(ans_idx + 1))
            code_elem = ET.SubElement(ans_row, "code")
            code_elem.text = str(ans_code)

            # ANSWER (testo)
            ans_text = ans.get('text', '')
            answer_elem = ET.SubElement(ans_row, "answer")
            answer_elem.text = ans_text

            # SORTORDER
            sort_order = ans.get('sortOrder', str(ans_idx))
            sort_elem = ET.SubElement(ans_row, "sortorder")
            sort_elem.text = str(sort_order)

            # ASSESSMENT_VALUE
            assessment = ans.get('assessmentValue', '0')
            assess_elem = ET.SubElement(ans_row, "assessment_value")
            assess_elem.text = str(assessment)

            # SCALE_ID
            scale = ans.get('scaleId', '0')
            scale_elem = ET.SubElement(ans_row, "scale_id")
            scale_elem.text = str(scale)

            # LANGUAGE
            lang_elem = ET.SubElement(ans_row, "language")
            lang_elem.text = "it"
    # ===== CONVERTI IN STRINGA XML =====
    print(f"DEBUG: XML structure created - root has {len(root)} children")

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

    # ✅ QUESTO RETURN È FONDAMENTALE!
    return final_xml

# Configura Flask con le directory corrette
app = Flask(__name__,
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# Disabilita cache per development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True


# ==================== FUNZIONI DI UTILITÀ ====================
def data_structure(data, field_name):
    """Converte dict in list se necessario"""
    field_data = data.get(field_name, [])

    if isinstance(field_data, dict):
        return list(field_data.values())
    elif isinstance(field_data, list):
        return field_data
    else:
        return []
def transform_limesurvey_json(questions):
    """
    Trasforma subquestions e answeroptions da oggetti ad array.

    Args:
        questions: Lista di question dal JSON LimeSurvey

    Returns:
        Lista trasformata
    """
    for question in questions:
        qid = question.get('qid')

        # ===== TRASFORMA SUBQUESTIONS =====
        subquestions = question.get('subquestions')

        if isinstance(subquestions, dict) and subquestions:
            # Converti oggetto in array
            subqs_array = []

            for sub_qid, subq_data in subquestions.items():
                # Crea nuovo oggetto subquestion
                subq = {
                    'qid': sub_qid,  # Usa chiave come qid
                    'parent_qid': qid,  # Aggiungi parent
                    **subq_data  # Copia tutti gli altri dati
                }
                subqs_array.append(subq)

            # Sostituisci oggetto con array
            question['subquestions'] = subqs_array

            print(f"✓ Trasformata question {qid}: {len(subqs_array)} subquestions")

        elif subquestions == "No available answers":
            # Converti stringa in array vuoto
            question['subquestions'] = []

        # ===== TRASFORMA ANSWEROPTIONS =====
        answeroptions = question.get('answeroptions')

        if isinstance(answeroptions, dict) and answeroptions:
            # Converti oggetto in array
            answers_array = []

            for code, answer_data in answeroptions.items():
                # Crea nuovo oggetto answer
                answer = {
                    'code': code,  # Usa chiave come code
                    'parent_qid': qid,  # Aggiungi parent
                    **answer_data  # Copia tutti gli altri dati
                }
                answers_array.append(answer)

            # Sostituisci oggetto con array
            question['answeroptions'] = answers_array

            print(f"✓ Trasformata question {qid}: {len(answers_array)} answeroptions")

        elif answeroptions == "No available answer options":
            # Converti stringa in array vuoto
            question['answeroptions'] = []

        # ===== TRASFORMA ATTRIBUTES =====
        attributes = question.get('attributes')

        if isinstance(attributes, dict) and attributes:
            # Converti oggetto in array
            attrs_array = []

            for attr_name, attr_value in attributes.items():
                # Salta attributes vuoti o null
                if attr_value in [None, "", "0"]:
                    continue

                attr = {
                    'name': attr_name,
                    'value': str(attr_value),
                    'parent_qid': qid
                }
                attrs_array.append(attr)

            question['attributes'] = attrs_array

            if attrs_array:
                print(f"✓ Trasformata question {qid}: {len(attrs_array)} attributes")

    return questions


def split_limesurvey_json(input_file):
    """
    Separa JSON in 4 file distinti:
    - questions_only.json
    - subquestions_only.json
    - answeroptions_only.json
    - attributes_only.json
    """

    print(f"📂 Caricamento: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"✓ Caricate {len(questions)} questions")
    print()
    questions = transform_limesurvey_json(questions)
    # ====== FILE 1: QUESTIONS ONLY ======
    print("🔄 Elaborazione questions...")
    questions_output = []

    for q in questions:
        # Rimuovi nested arrays - li mapperemo separatamente
        q_clean = {
            k: v for k, v in q.items()
            if k not in ['subquestions', 'answeroptions', 'attributes', 'attributes_lang', 'available_answers']
        }
        questions_output.append(q_clean)

    with open('questions_only.json', 'w', encoding='utf-8') as f:
        json.dump(questions_output, f, indent=2, ensure_ascii=False)

    print(f"✓ Salvato: questions_only.json ({len(questions_output)} questions)")

    # ====== FILE 2: SUBQUESTIONS ONLY ======
    print("🔄 Elaborazione subquestions...")
    subquestions_output = []

    for q in questions:
        subqs = q.get('subquestions', [])
        if isinstance(subqs, list):
            for sq in subqs:
                if sq:  # Solo se non None o vuoto
                    subquestions_output.append(sq)

    with open('subquestions_only.json', 'w', encoding='utf-8') as f:
        json.dump(subquestions_output, f, indent=2, ensure_ascii=False)

    print(f"✓ Salvato: subquestions_only.json ({len(subquestions_output)} subquestions)")

    # ====== FILE 3: ANSWEROPTIONS ONLY ======
    print("🔄 Elaborazione answer options...")
    answeroptions_output = []

    for q in questions:
        answers = q.get('answeroptions', [])
        if isinstance(answers, list):
            for ao in answers:
                if ao:  # Solo se non None o vuoto
                    answeroptions_output.append(ao)

    with open('answeroptions_only.json', 'w', encoding='utf-8') as f:
        json.dump(answeroptions_output, f, indent=2, ensure_ascii=False)

    print(f"✓ Salvato: answeroptions_only.json ({len(answeroptions_output)} answeroptions)")

    # ====== FILE 4: ATTRIBUTES ONLY ======
    print("🔄 Elaborazione attributes...")
    attributes_output = []

    for q in questions:
        attrs = q.get('attributes', [])
        if isinstance(attrs, list):
            for attr in attrs:
                if attr:  # Solo se non None o vuoto
                    attributes_output.append(attr)

    with open('attributes_only.json', 'w', encoding='utf-8') as f:
        json.dump(attributes_output, f, indent=2, ensure_ascii=False)

    print(f"✓ Salvato: attributes_only.json ({len(attributes_output)} attributes)")

    print()
    print("=" * 70)
    print("✅ SPLIT COMPLETATO!")
    print("=" * 70)
    print()
    print("📊 Riepilogo:")
    print(f"  Questions:      {len(questions_output):4d}")
    print(f"  Subquestions:   {len(subquestions_output):4d}")
    print(f"  Answer Options: {len(answeroptions_output):4d}")
    print(f"  Attributes:     {len(attributes_output):4d}")
    print()
    print("📝 File creati:")
    print("  - questions_only.json")
    print("  - subquestions_only.json")
    print("  - answeroptions_only.json")
    print("  - attributes_only.json")
    print()
    print("🎯 Ora aggiorna il tuo RML per usare questi file:")
    print()
    print("  <#QuestionsSource>")
    print('    rml:source "questions_only.json" ;')
    print()
    print("  <#SubQuestionsSource>")
    print('    rml:source "subquestions_only.json" ;')
    print('    rml:iterator "$[*]" .  # ← Nota: root level!')
    print()
    print("  <#AnswerOptionsSource>")
    print('    rml:source "answeroptions_only.json" ;')
    print('    rml:iterator "$[*]" .  # ← Nota: root level!')
    print()
    print("  <#AttributesSource>")
    print('    rml:source "attributes_only.json" ;')
    print('    rml:iterator "$[*]" .  # ← Nota: root level!')
    print()


def clean_uri_path(path):
    """
    Pulisce un path per costruire URI validi senza doppi slash

    Args:
        path: stringa da pulire (es: "/123", "123", "")

    Returns:
        stringa pulita (es: "123", "123", "default")
    """
    if not path:
        return 'default'

    # Rimuovi spazi e slash iniziali/finali
    cleaned = str(path).strip().strip('/')

    # Se dopo la pulizia è vuoto, usa 'default'
    if not cleaned:
        return 'default'

    return cleaned


# ============================================
# HELPER: Clean URI path
# ============================================

def clean_uri_path(value):
    """
    Clean a string to be used in URIs.
    Removes special characters and normalizes spaces.
    """
    if not value:
        return ""

    # Remove leading/trailing whitespace
    value = value.strip()

    # Replace spaces with underscores
    value = value.replace(' ', '_')

    # Remove special characters (keep only alphanumeric, underscore, hyphen)
    import re
    value = re.sub(r'[^a-zA-Z0-9_-]', '', value)

    return value


def cambiaNomeCSV(input_file):
    output_file = "list_questions.csv"

    print(f"\n=== PULIZIA CSV QUESTIONS ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    try:
        # Leggi il CSV con pandas che gestisce correttamente newline e virgolette
        df = pd.read_csv(
            input_file,
            quoting=1,  # QUOTE_ALL
            encoding='utf-8',
            engine='python',  # Più flessibile con formati complessi
            on_bad_lines='warn'  # Avvisa ma non blocca su righe problematiche
        )

        print(f"✓ CSV letto: {len(df)} righe, {len(df.columns)} colonne")
        print(f"  Colonne: {list(df.columns)[:5]}...")  # Mostra prime 5

        # Pulisci i dati: rimuovi newline interni dalle celle
        for col in df.columns:
            if df[col].dtype == 'object':  # Solo colonne di testo
                # Sostituisci newline e carriage return con spazi
                df[col] = df[col].astype(str).str.replace('\n', ' ', regex=False)
                df[col] = df[col].str.replace('\r', ' ', regex=False)
                # Rimuovi spazi multipli
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
                # Pulisci doppi apici
                df[col] = df[col].str.replace('""', '"', regex=False)
                # Trim spazi
                df[col] = df[col].str.strip()
                # Gestisci valori nan
                df[col] = df[col].replace('nan', '')

        # Verifica colonne richieste dall'RML
        required_cols = ['qid', 'question', 'type', 'title', 'gid']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"⚠️  Colonne mancanti: {missing_cols}")
            print(f"   Colonne disponibili: {list(df.columns)}")
            return False

        # Verifica che ci siano dati
        if len(df) == 0:
            print(f"❌ CSV vuoto!")
            return False

        # Salva il CSV pulito
        df.to_csv(
            output_file,
            index=False,
            encoding='utf-8',
            quoting=1,  # QUOTE_ALL per sicurezza
            lineterminator='\n'  # Unix line endings
        )

        # Verifica il file output
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"✓ CSV pulito salvato: {output_file}")
            print(f"  Righe nel file: {len(lines)} (incluso header)")
            print(f"  Prima riga (header): {lines[0][:80]}...")

        return True

    except pd.errors.ParserError as e:
        print(f"❌ Errore parsing CSV: {e}")
        return False

    except Exception as e:
        print(f"❌ Errore generico: {e}")
        import traceback
        traceback.print_exc()
        return False


def pulisciCSV(input_file):
    """Pulisce il CSV dei groups e risolve problemi con virgolette e newline"""
    output_file = "list_groups.csv"

    try:
        # Leggi il CSV usando pandas
        import pandas as pd

        df = pd.read_csv(input_file, quoting=1, escapechar='\\', encoding='utf-8')

        print(f"CSV letto: {len(df)} righe, {len(df.columns)} colonne")

        # Pulisci i dati
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('\n', ' ').str.replace('\r', ' ')
                df[col] = df[col].str.replace('""', "'")
                df[col] = df[col].str.strip()

        # Salva
        df.to_csv(output_file, index=False, encoding='utf-8', quoting=1)

        print(f"✓ CSV pulito salvato: {output_file}")
        return True

    except Exception as e:
        print(f"Errore in pulisciCSV (metodo pandas): {e}")
        print("Provo con metodo manuale...")

        # Fallback
        temp_file = "tmp_cleaned_raw.csv"

        with open(input_file, encoding="utf-8") as f_in, open(temp_file, "w", encoding="utf-8") as f_out:
            for line in f_in:
                line = line.replace('""', "'")
                f_out.write(line)

        rows = []
        buffer = ""
        in_quotes = False

        with open(temp_file, encoding="utf-8") as f:
            for raw_line in f:
                for ch in raw_line:
                    buffer += ch
                    if ch == '"':
                        in_quotes = not in_quotes
                    if ch == "\n" and not in_quotes:
                        rows.append(buffer.rstrip("\n"))
                        buffer = ""

        if buffer.strip():
            rows.append(buffer)

        with open(output_file, "w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out, quoting=csv.QUOTE_ALL)
            for line in rows:
                cleaned_row = []
                for cell in csv.reader([line]):
                    cleaned_cells = [c.replace('\n', ' ').replace('\r', ' ') for c in cell]
                    cleaned_row = cleaned_cells
                    break
                if cleaned_row:
                    writer.writerow(cleaned_row)

        print(f"✓ CSV pulito salvato (metodo manuale): {output_file}")
        return True


def appiattisci_json(j, prefisso=""):
    """Appiattisce un JSON in un dizionario flat"""
    risultato = {}
    for k, v in j.items():
        nuova_chiave = f"{prefisso}{k}" if not prefisso else f"{prefisso}_{k}"
        if isinstance(v, dict):
            risultato.update(appiattisci_json(v, nuova_chiave))
        else:
            risultato[nuova_chiave] = v
    return risultato


def appiattisci_dizionario(d, parent_key='', sep='_'):
    """Appiattisce un dizionario annidato"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(appiattisci_dizionario(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(appiattisci_dizionario(item, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)


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


# ==================== RML CONVERTER ====================

logger = logging.getLogger(__name__)


class RMLConversionError(Exception):
    """Custom exception for RML conversion errors."""
    pass


class RMLConverter:
    """
    RML Converter con subprocess isolation per pyrml locale.
    Ricrea un processo Python fresco per ogni conversione.
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize converter.

        Args:
            strict_mode: If True, enables RML strict mode validation.
        """
        self.strict_mode = strict_mode
        self.rdf_graph: Optional[Graph] = None

        logger.info(f"RMLConverter initialized (strict_mode={strict_mode}, subprocess mode)")

    def convert_rml_file(self, rml_file_path: Union[str, Path]) -> Graph:
        """
        Convert RML file using subprocess isolation.
        Each conversion runs in a fresh Python process.
        """
        # Validate
        if not rml_file_path:
            raise ValueError("RML file path cannot be empty")

        rml_path = Path(rml_file_path).resolve()

        if not rml_path.exists():
            raise FileNotFoundError(f"RML file not found: {rml_path}")

        logger.info(f"Converting RML: {rml_path}")
        print(f"🔄 Converting RML: {rml_path}")

        # Output file
        output_path = rml_path.parent / (rml_path.stem + '_output.ttl')

        try:
            # Convert in subprocess
            result = self._convert_in_subprocess(str(rml_path), str(output_path))

            if not result['success']:
                raise RMLConversionError(result.get('error', 'Unknown error'))

            # Load graph
            self.rdf_graph = Graph()
            self.rdf_graph.parse(str(output_path), format='turtle')

            logger.info(f"Conversion complete: {len(self.rdf_graph)} triples")
            print(f"✅ Conversion complete: {len(self.rdf_graph)} triples")

            return self.rdf_graph

        except Exception as e:
            error_msg = f"Failed to convert {rml_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RMLConversionError(error_msg) from e

    def _convert_in_subprocess(self, rml_file: str, output_file: str) -> dict:
        """Run conversion in isolated subprocess."""

        # Conversion script
        script = f"""
import sys
import json

try:
    from pyrml import PyRML

    PyRML.RML_STRICT = {self.strict_mode}
    mapper = PyRML.get_mapper()
    graph = mapper.convert(r'{rml_file}')
    graph.serialize(r'{output_file}', format='turtle')

    result = {{'success': True, 'triples': len(graph), 'output': r'{output_file}'}}
    print(json.dumps(result))
    sys.exit(0)

except Exception as e:
    import traceback
    result = {{'success': False, 'error': str(e), 'traceback': traceback.format_exc()}}
    print(json.dumps(result))
    sys.exit(1)
"""

        logger.debug(f"Running subprocess conversion: {rml_file}")
        print(f"🔧 Running isolated conversion...")

        try:
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.getcwd()
            )

            try:
                # ✅ FIX: Parsing robusto - trova l'ultima riga JSON
                stdout_lines = result.stdout.strip().split('\n')

                # Cerca l'ultima riga che inizia con '{'
                json_line = None
                for line in reversed(stdout_lines):
                    line = line.strip()
                    if line.startswith('{'):
                        json_line = line
                        break

                if not json_line:
                    error_msg = f"No JSON output\nstdout: {result.stdout}\nstderr: {result.stderr}"
                    return {'success': False, 'error': error_msg}

                output = json.loads(json_line)

                if output['success']:
                    print(f"✓ Subprocess: {output.get('triples', 0)} triples")
                else:
                    print(f"✗ Subprocess error: {output.get('error')}")

                return output

            except json.JSONDecodeError as e:
                error_msg = f"JSON parse error: {e}\nstdout: {result.stdout}\nstderr: {result.stderr}"
                return {'success': False, 'error': error_msg}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout (5 minutes)'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def save_to_file(self, output_file: Union[str, Path], format: str = 'turtle') -> bool:
        """Save current graph to file."""
        if self.rdf_graph is None:
            raise ValueError("No RDF graph available. Run convert_rml_file() first")

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.rdf_graph.serialize(destination=str(output_file), format=format)
            print(f"✓ Saved: {output_file}")
            return True
        except Exception as e:
            print(f"✗ Save error: {e}")
            return False

    def get_graph(self) -> Optional[Graph]:
        """Get current RDF graph."""
        return self.rdf_graph


# ==================== LIMESURVEY API ====================


class LimeSurveyAPI:
    """
    Client unificato per LimeSurvey RemoteControl API
    Combina funzionalità di lettura (export) e scrittura (creazione survey)
    """

    def __init__(self, url: str, username: str, password: str):
        """
        Inizializza il client LimeSurvey

        Args:
            url: URL del RemoteControl API (es: http://localhost/limesurvey/index.php/admin/remotecontrol)
            username: Username LimeSurvey
            password: Password LimeSurvey
        """
        self.url = url
        self.username = username
        self.password = password
        self.session_key = None

    def _call(self, method: str, params: List) -> Any:
        """
        Effettua una chiamata RPC all'API di LimeSurvey

        Args:
            method: Nome del metodo API da chiamare
            params: Lista di parametri per il metodo

        Returns:
            Risultato della chiamata API

        Raises:
            Exception: Se la chiamata fallisce o ritorna errore
        """
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

            # Verifica se la risposta è HTML (pagina di errore)
            if 'text/html' in response.headers.get('content-type', ''):
                print(f"DEBUG: Received HTML instead of JSON")
                print(f"DEBUG: First 500 chars: {response.text[:500]}")
                raise Exception(
                    f"LimeSurvey returned HTML instead of JSON. "
                    f"Check if RemoteControl is enabled and URL is correct. URL: {self.url}"
                )

            result = response.json()

            # Verifica errori RPC
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
        """
        Ottiene la session key per l'autenticazione

        Returns:
            Session key string

        Raises:
            Exception: Se l'autenticazione fallisce
        """
        if not self.session_key:
            self.session_key = self._call("get_session_key", [self.username, self.password])

            # Verifica errori nella session key
            if isinstance(self.session_key, dict) and 'status' in self.session_key:
                raise Exception(self.session_key.get('status'))

            if not self.session_key or self.session_key == "null":
                raise Exception("Failed to authenticate with LimeSurvey")

        return self.session_key

    def release_session_key(self):
        """Rilascia la session key corrente"""
        if self.session_key:
            self._call("release_session_key", [self.session_key])
            self.session_key = None

    # ==================== METODI DI LETTURA (EXPORT) ====================

    def list_surveys(self):
        """
        Elenca tutte le survey disponibili

        Returns:
            Lista di dizionari con informazioni sulle survey
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('list_surveys', [self.session_key])

    def get_survey_properties(self, survey_id: int):
        """
        Ottiene le proprietà di una survey

        Args:
            survey_id: ID della survey

        Returns:
            Dizionario con le proprietà della survey
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('get_survey_properties', [self.session_key, survey_id])

    def list_questions(self, survey_id: int):
        """
        Elenca tutte le domande di una survey

        Args:
            survey_id: ID della survey

        Returns:
            Lista di dizionari con informazioni sulle domande
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('list_questions', [self.session_key, survey_id])

    def list_groups(self, survey_id: int):
        """
        Elenca tutti i gruppi di una survey

        Args:
            survey_id: ID della survey

        Returns:
            Lista di dizionari con informazioni sui gruppi
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('list_groups', [self.session_key, survey_id])

    def list_participants(self, survey_id: int):
        """
        Elenca tutti i partecipanti di una survey

        Args:
            survey_id: ID della survey

        Returns:
            Lista di dizionari con informazioni sui partecipanti
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('list_participants', [self.session_key, survey_id])

    def export_responses(self, survey_id: int, format: str = 'json'):
        """
        Esporta le risposte di una survey

        Args:
            survey_id: ID della survey
            format: Formato di export (default: 'json')

        Returns:
            Risposte in formato specificato
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('export_responses', [self.session_key, survey_id, format])

    def get_summary(self, survey_id: int):
        """
        Ottiene un sommario statistico della survey

        Args:
            survey_id: ID della survey

        Returns:
            Dizionario con statistiche della survey
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('get_summary', [self.session_key, survey_id])

    def get_question_properties(self, question_id: int):
        """
        Ottiene le proprietà di una domanda specifica

        Args:
            question_id: ID della domanda

        Returns:
            Dizionario con le proprietà della domanda
        """
        if not self.session_key:
            self.get_session_key()
        return self._call('get_question_properties', [self.session_key, question_id])

    def export_all_question_properties_survey(self, survey_id):
        if not self.session_key:
            self.get_session_key()

        data1 = self.list_questions(survey_id)
        print("sono all'inizio")
        data = []
        k = 0

        for e in data1:  # ciclo sulle domande della survey
            risultato_intermedio = self.get_question_properties(e['qid'])
            print(risultato_intermedio)
            data.append(risultato_intermedio)

        # Save to JSON and return path
        output_path = self._save_to_json(data, "questions.json")
        print(f"✅ Exported {len(data)} questions to {output_path}")
        return output_path

    def _save_to_json(self, data: any, filename: str) -> str:
        """Save data to JSON file in exports directory"""
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        output_path = exports_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved JSON: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"✗ Error saving JSON: {e}")
            raise

    # ==================== METODI DI SCRITTURA (CREAZIONE) ====================

    def create_survey(self, title: str, language: str = "it", format: str = "G") -> int:
        """
        Crea una nuova survey

        Args:
            title: Titolo della survey
            language: Lingua della survey (default: "it")
            format: Formato della survey (default: "G" = Group by Group)

        Returns:
            ID della survey creata

        Raises:
            Exception: Se la creazione fallisce
        """
        session_key = self.get_session_key()

        print(f"DEBUG: Creating survey with title: {title}, language: {language}")

        # Genera un ID temporaneo (LimeSurvey lo sostituirà)
        import random
        temp_sid = random.randint(100000, 999999)

        # Chiamata API: session_key, sid, title, language, format
        survey_id = self._call("add_survey", [session_key, temp_sid, title, language, format])

        if not survey_id or survey_id == "null":
            raise Exception("Failed to create survey - no ID returned")

        print(f"DEBUG: Created survey with ID: {survey_id}")
        return int(survey_id)

    def add_group(self, survey_id: int, title: str, description: str = "", order: int = 0) -> int:
        """
        Aggiunge un gruppo a una survey

        Args:
            survey_id: ID della survey
            title: Titolo del gruppo
            description: Descrizione del gruppo (opzionale)
            order: Ordine del gruppo (opzionale)

        Returns:
            ID del gruppo creato
        """
        session_key = self.get_session_key()

        group_id = self._call("add_group", [session_key, survey_id, title, description])
        print(f"Created group '{title}' with ID: {group_id}")
        return int(group_id)

    def import_question(self, survey_id: int, group_id: int, lsq_base64: str,
                        mandatory: str = 'N') -> int:
        """
        Importa una domanda da file .lsq in formato Base64

        Args:
            survey_id: ID della survey
            group_id: ID del gruppo di destinazione
            lsq_base64: Contenuto del file .lsq in Base64
            mandatory: 'Y' o 'N' per obbligatorietà (default: 'N')

        Returns:
            ID della domanda importata

        Raises:
            Exception: Se l'import fallisce
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

            # Gestisci diverse possibili risposte
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

            # Se è direttamente un intero o stringa
            if isinstance(result, (int, str)):
                qid = int(result)
                print(f"DEBUG: Question imported successfully with ID: {qid}")
                return qid

            # Formato non riconosciuto
            raise Exception(f"Unexpected import_question response format: {result}")

        except Exception as e:
            print(f"DEBUG: import_question failed: {e}")
            raise

    def activate_survey(self, survey_id: int):
        """
        Attiva una survey (la rende disponibile per la compilazione)

        Args:
            survey_id: ID della survey da attivare

        Returns:
            Risultato dell'attivazione
        """
        session_key = self.get_session_key()
        result = self._call("activate_survey", [session_key, survey_id])
        print(f"Survey {survey_id} activated")
        return result

    # ==================== UTILITY METHODS ====================

    def __enter__(self):
        """Context manager entry - ottiene session key"""
        self.get_session_key()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - rilascia session key"""
        self.release_session_key()

    def __del__(self):
        """Destructor - assicura il rilascio della session key"""
        try:
            self.release_session_key()
        except:
            pass


# ==================== SURVEY EXPORTER ====================
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


# ==================== GRAPHDB MANAGER and CLIENT====================

class GraphDBManager:
    """Gestisce la connessione e le operazioni con GraphDB"""

    def __init__(self, base_url="http://localhost:7200", username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()
        if self.auth:
            self.session.auth = self.auth

    def create_repository(self, repo_id, repo_title=None, repo_type="graphdb", ruleset="owl-horst-optimized"):
        """
        Crea un nuovo repository GraphDB usando un template Turtle
        """
        if repo_title is None:
            repo_title = repo_id
        valid_rulesets = {
            "empty": "empty",
            "rdfs": "rdfs",
            "owl-horst": "owl-horst-optimized",
            "owl-horst-optimized": "owl-horst-optimized",
            "owl-max": "owl-max-optimized",
            "owl-max-optimized": "owl-max-optimized",
            "owl2-ql": "owl2-ql",
            "owl2-rl": "owl2-rl",
            "rdfsplus-optimized": "owl-horst-optimized"  # Fallback
        }

        # Valida e correggi il ruleset
        ruleset = valid_rulesets.get(ruleset, "owl-horst-optimized")

        config = {
            "id": repo_id,
            "title": repo_title,
            "type": "graphdb",
            "params": {
                "ruleset": {
                    "label": "Ruleset",
                    "name": "ruleset",
                    "value": "empty"

                },
                "disable-sameAs": {
                    "label": "Disable owl:sameAs",
                    "name": "disable-sameAs",
                    "value": "true"
                },
                "check-for-inconsistencies": {
                    "label": "Check for inconsistencies",
                    "name": "check-for-inconsistencies",
                    "value": "false"
                },
                "entity-id-size": {
                    "label": "Entity ID bit-size",
                    "name": "entity-id-size",
                    "value": "32"
                },
                "enable-context-index": {
                    "label": "Use context index",
                    "name": "enable-context-index",
                    "value": "true"
                },
                "enablePredicateList": {
                    "label": "Use predicate indices",
                    "name": "enablePredicateList",
                    "value": "true"
                },
                "enable-fts-index": {
                    "label": "Enable full-text search",
                    "name": "enable-fts-index",
                    "value": "false"
                },
                "fts-indexes": {
                    "label": "Full-text search indexes",
                    "name": "fts-indexes",
                    "value": "default, iri"
                },
                "fts-string-literals-index": {
                    "label": "String literals index",
                    "name": "fts-string-literals-index",
                    "value": "default"
                },
                "fts-iris-index": {
                    "label": "IRIs index",
                    "name": "fts-iris-index",
                    "value": "none"
                },
                "query-timeout": {
                    "label": "Query time-out (s)",
                    "name": "query-timeout",
                    "value": "0"
                },
                "throw-QueryEvaluationException-on-timeout": {
                    "label": "Throw exception on query timeout",
                    "name": "throw-QueryEvaluationException-on-timeout",
                    "value": "false"
                },
                "query-limit-results": {
                    "label": "Limit query results",
                    "name": "query-limit-results",
                    "value": "0"
                },
                "base-URL": {
                    "label": "Base URL",
                    "name": "base-URL",
                    "value": f"http://example.org/graphdb#{repo_id}/"
                },
                "defaultNS": {
                    "label": "Default namespaces for imports(';' delimited)",
                    "name": "defaultNS",
                    "value": ""
                },
                "imports": {
                    "label": "Imported RDF files(';' delimited)",
                    "name": "imports",
                    "value": ""
                },
                "repository-type": {
                    "label": "Repository type",
                    "name": "repository-type",
                    "value": "file-repository"
                },
                "storage-folder": {
                    "label": "Storage folder",
                    "name": "storage-folder",
                    "value": "storage"
                },
                "entity-index-size": {
                    "label": "Entity index size",
                    "name": "entity-index-size",
                    "value": "10000000"
                },
                "in-memory-literal-properties": {
                    "label": "Cache literal language tags",
                    "name": "in-memory-literal-properties",
                    "value": "true"
                },
                "enable-literal-index": {
                    "label": "Enable literal index",
                    "name": "enable-literal-index",
                    "value": "true"
                },
                "read-only": {
                    "label": "Read-only",
                    "name": "read-only",
                    "value": "false"
                }
            }
        }

        #         config = {
        #     "id": "repo_test",
        #     "title": "Repository creato via API JSON",
        #     "type": "graphdb",
        #     "sesameType":"graphdb:SailRepository",
        #     "params": {
        #         "ruleset": {"name": "ruleset", "value": "rdfsplus-optimized"},
        #         "base-URL": {"name": "base-URL", "value": "http://example.org/graph#"},
        #         "defaultNS": {"name": "defaultNS", "value": ""},  # <-- parametro necessario
        #         "storage-folder": {"name": "storage-folder", "value": "storage"},
        #         "entity-index-size": {"name": "entity-index-size", "value": "100000"},
        #         "enable-context-index": {"name": "enable-context-index", "value": "true"},
        #         "enablePredicateList": {"name": "enablePredicateList", "value": "false"},
        #         "check-for-inconsistencies": {"name": "check-for-inconsistencies", "value": "false"},
        #         "disable-sameAs": {"name": "disable-sameAs", "value": "false"},
        #         "query-timeout": {"name": "query-timeout", "value": "0"},
        #         "imports": {"name": "imports", "value": ""}
        #     }
        # }
        headers = {
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/rest/repositories"

        response = self.session.post(url, data=json.dumps(config), headers=headers)

        if response.status_code in [200, 201]:
            success_msg = f"Created '{repo_id}'"
            print(f"SUCCESS: {success_msg}")
            return {"success": True, "message": f"'{success_msg}' repository"}
        elif response.status_code == 409:
            print(f"⚠ Repository '{repo_id}' già esistente")
            return {"success": True, "message": f"Repository '{repo_id}' exist"}
        else:
            error_msg = f"Error HTTP {response.status_code}: {response.text}"
            print(f"Error: {error_msg}")
            return {"success": False, "message": f"Error: {response.status_code} - {error_msg}"}

    def delete_repository(self, repo_id):
        url = f"{self.base_url}/rest/repositories/{repo_id}"
        response = self.session.delete(url)
        if response.status_code == 200:
            return {"success": True, "message": f"Repository '{repo_id}' eliminato"}
        else:
            return {"success": False, "message": f"Errore: {response.status_code}"}

    def list_repositories(self):
        url = f"{self.base_url}/rest/repositories"
        response = self.session.get(url)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "message": f"Errore: {response.status_code}"}

    def upload_file(self, repo_id, file_path, context=None, file_format=None):
        file_path = Path(file_path)

        print(f"\n--- GraphDBManager.upload_file ---")
        print(f"Repository: {repo_id}")
        print(f"File: {file_path}")
        print(f"File exists: {file_path.exists()}")
        print(f"Context: {context}")

        if not file_path.exists():
            error_msg = f"File non trovato: {file_path}"
            print(f"ERRORE: {error_msg}")
            return {"success": False, "message": error_msg}

        if file_format is None:
            extension_map = {
                '.ttl': 'text/turtle',
                '.rdf': 'application/rdf+xml',
                '.owl': 'application/rdf+xml',
                '.nt': 'application/n-triples',
                '.nq': 'application/n-quads',
                '.jsonld': 'application/ld+json',
                '.trig': 'application/trig'
            }
            file_format = extension_map.get(file_path.suffix.lower(), 'text/turtle')

        print(f"File format: {file_format}")

        url = f"{self.base_url}/repositories/{repo_id}/statements"
        params = {}
        if context:
            params['context'] = f"<{context}>"

        print(f"URL GraphDB: {url}")
        print(f"Params: {params}")

        headers = {"Content-Type": file_format}

        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                print(f"File size: {len(file_content)} bytes")
                response = self.session.post(url, params=params, data=file_content, headers=headers)

            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text[:500] if response.text else 'empty'}")

            if response.status_code in [200, 201, 204]:
                success_msg = f"File '{file_path.name}' caricato in '{repo_id}'"
                print(f"SUCCESS: {success_msg}")
                return {"success": True, "message": success_msg}
            else:
                error_msg = f"Errore HTTP {response.status_code}: {response.text}"
                print(f"ERRORE: {error_msg}")
                return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Eccezione: {str(e)}"
            print(f"ERRORE: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": error_msg}

    def clear_repository(self, repo_id, context=None):
        url = f"{self.base_url}/repositories/{repo_id}/statements"
        params = {}
        if context:
            params['context'] = f"<{context}>"
        response = self.session.delete(url, params=params)
        if response.status_code in [200, 204]:
            target = f"named graph '{context}'" if context else "repository"
            return {"success": True, "message": f"{target} svuotato"}
        else:
            return {"success": False, "message": f"Errore: {response.status_code}"}

    def delete_by_subject(self, repo_id, subject_uri):
        url = f"{self.base_url}/repositories/{repo_id}/statements"
        params = {"subj": f"<{subject_uri}>"}
        response = self.session.delete(url, params=params)
        if response.status_code in [200, 204]:
            return {"success": True, "message": f"Dati eliminati per: {subject_uri}"}
        else:
            return {"success": False, "message": f"Errore: {response.status_code}"}


class GraphDBClient:

    def __init__(self, endpoint: str, repository: str):
        self.endpoint = f"{endpoint}/repositories/{repository}"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)

    def execute_query(self, query: str) -> Dict[str, Any]:
        # Esegue una query SPARQL e ritorna i risultati"""
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
        # """Parser per organizzare tutti i dati della question"""
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
        """Recupera tutti i gruppi con le loro domande (solo main questions)"""
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

                    # ✅ FIX: Filtra solo main questions (no subquestions)
                    FILTER NOT EXISTS { ?question ls:hasParentQuestion ?anyParent }

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

        groups = list(groups_dict.values())

        print(f"DEBUG: Found {len(groups)} groups")
        for g in groups:
            print(f"DEBUG: Group ID={g['id']}, Name={g['name']}, Questions={len(g['questions'])}")

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
                   ?subQid ?subTitle ?subQuestionText ?subOrder
            WHERE {
                ?question a ls:Question .

                # ✅ FILTRO: Solo main questions (non subquestions)
                FILTER NOT EXISTS { ?question ls:hasParentQuestion ?anyParent }

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

                # Answer Options
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

                # Subquestions
                OPTIONAL {
                    ?subQuestion ls:hasParentQuestion ?question .
                    ?subQuestion ls:hasId ?subIdNode .
                    ?subIdNode ls:id ?subQid .

                    OPTIONAL {
                        ?subQuestion ls:hasVariable ?subVarNode .
                        ?subVarNode ls:variableCod ?subTitle .
                    }

                    OPTIONAL {
                        ?subQuestion ls:hasContent ?subContentNode .
                        ?subContentNode ls:text ?subQuestionText .
                    }

                    OPTIONAL {
                        ?subQuestion ls:hasComponentAttribute ?subOrderAttr .
                        ?subOrderAttr ls:componentName "question_order" .
                        ?subOrderAttr ls:componentValue ?subOrder .
                    }
                }
            }
            ORDER BY ?questionId ?answerSortOrder ?subOrder
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
                    "answerOptions": [],
                    "subquestions": []
                }

            # Processa answer options
            if "answerOptions" in binding or "answerCode" in binding:
                answer_code = binding.get("answerCode", {}).get("value", "")
                answer_text = binding.get("answerText", {}).get("value", "")

                # Aggiungi solo se ha almeno code o text
                if answer_code or answer_text:
                    answer = {
                        "code": answer_code,
                        "text": answer_text,
                        "sortOrder": binding.get("answerSortOrder", {}).get("value", ""),
                        "assessmentValue": binding.get("answerAssessmentValue", {}).get("value", ""),
                        "scaleId": binding.get("answerScaleId", {}).get("value", "0")
                    }

                    # Evita duplicati
                    if not any(a["code"] == answer["code"] for a in questions_dict[question_uri]["answerOptions"]):
                        questions_dict[question_uri]["answerOptions"].append(answer)

            # Processa subquestions
            if "subQid" in binding and binding.get("subQid", {}).get("value"):
                sub_id = binding.get("subQid", {}).get("value", "")

                subquestion = {
                    "id": sub_id,
                    "title": binding.get("subTitle", {}).get("value", ""),
                    "text": binding.get("subQuestionText", {}).get("value", ""),
                    "order": binding.get("subOrder", {}).get("value", "")
                }

                # Evita duplicati
                if not any(s["id"] == sub_id for s in questions_dict[question_uri]["subquestions"]):
                    questions_dict[question_uri]["subquestions"].append(subquestion)

        # Converti il dizionario in lista
        questions = list(questions_dict.values())

        # ✅ Ordina answerOptions e subquestions per sortOrder/order
        for q in questions:
            if q["answerOptions"]:
                q["answerOptions"].sort(key=lambda x: int(x.get("sortOrder") or "0"))
            if q["subquestions"]:
                q["subquestions"].sort(key=lambda x: int(x.get("order") or "0"))

        print(f"DEBUG: Found {len(questions)} unique questions")
        print(f"DEBUG: Found {q['answerOptions']} answerOptions questions")
        print(f"DEBUG: Found {q['subquestions']} subquestions")
        # Log di debug dettagliato
        questions_with_answers = sum(1 for q in questions if len(q["answerOptions"]) > 0)
        questions_with_subs = sum(1 for q in questions if len(q["subquestions"]) > 0)
        questions_without_text = sum(1 for q in questions if q["text"] == "No text")

        print(f"DEBUG: {questions_with_answers} questions have answer options")
        print(f"DEBUG: {questions_with_subs} questions have subquestions")

        if questions_without_text > 0:
            print(f"⚠️  WARNING: {questions_without_text} questions without text!")
            # Mostra un esempio
            no_text_example = next((q for q in questions if q["text"] == "No text"), None)
            if no_text_example:
                print(f"   Example: ID={no_text_example['id']}, Type={no_text_example['questionType']}")

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


# ==================== ROUTES ====================

# Nota: La route '/' è definita alla fine del file (serve home.html)


def ex(data, api, operation):
    # Debug: print operation name
    print(f"🔍 ex() called with operation: '{operation}' (type: {type(operation)})")

    if operation == 'list_surveys':
        result = api.list_surveys()
        result = [appiattisci_json(item) for item in result]
    elif operation == 'get_survey_properties':
        result1 = api.get_survey_properties(data['survey_id'])
        result1 = appiattisci_dizionario(result1)
        result = [result1]
    elif operation == 'get_question_properties':
        result1 = api.get_question_properties(data['question_id'])
        result1 = appiattisci_dizionario(result1)
        result = [result1]
    elif operation == 'list_questions':
        result = api.list_questions(data['survey_id'])
        result = [appiattisci_json(item) for item in result]
    elif operation == 'list_groups':
        result = api.list_groups(data['survey_id'])
        result = [appiattisci_json(item) for item in result]
    elif operation == 'list_participants':
        result = api.list_participants(data['survey_id'])
        result = [appiattisci_json(item) for item in result]
    elif operation == 'question_properties':
        print(f"✅ Matched 'question_properties', calling export_all_question_properties_survey")
        # Export returns file path, not data
        file_path = api.export_all_question_properties_survey(data['survey_id'])
        print(f"✅ Export completed, file_path: {file_path}")
        # Return special marker for file export
        result = {'_file_export': True, 'file_path': file_path}
    elif operation == 'export_responses':
        responses = api.export_responses(data['survey_id'])
        if isinstance(responses, str):
            decoded = base64.b64decode(responses).decode('utf-8')
            result = json.loads(decoded).get("responses")
        else:
            result = responses
    elif operation == 'get_summary':
        result = api.get_summary(data['survey_id'])
    else:
        # ✅ FIX: Handle unknown operations
        print(f"❌ Unknown operation: '{operation}'")
        raise ValueError(f"Unknown operation: {operation}")

    print(f"✅ ex() returning result: {type(result)}")
    return result


@app.route('/api/execute', methods=['POST'])
def execute():
    try:
        data = request.json
        api = LimeSurveyAPI(data['url'], data['username'], data['password'])
        result = ex(data, api, data['operation'])
        api.release_session_key()

        # Check if it's a file export operation
        if isinstance(result, dict) and result.get('_file_export'):
            return jsonify({
                'success': True,
                'file_path': result['file_path'],
                'message': f'File exported to {result["file_path"]}'
            })
        else:
            return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export', methods=['GET'])
def export():
    try:
        data = request.args
        api = LimeSurveyAPI(data['url'], data['username'], data['password'])
        result = ex(data, api, data['operation'])
        api.release_session_key()

        # Check if it's a file export (returns file path directly)
        if isinstance(result, dict) and result.get('_file_export'):
            # File already created, just send it
            filepath = result['file_path']
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True,
                                 download_name=os.path.basename(filepath))
            else:
                return jsonify({'success': False, 'error': f'File not found: {filepath}'})

        # Normal data export - create CSV
        output_dir = 'exports'
        os.makedirs(output_dir, exist_ok=True)
        filename = f'{data["operation"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(output_dir, filename)

        if isinstance(result, list) and result:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=result[0].keys())
                writer.writeheader()
                writer.writerows(result)

        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/repositories', methods=['GET'])
def list_graphdb_repositories():
    try:
        graphdb = GraphDBManager(request.args.get('url', 'http://localhost:7200'))
        return jsonify(graphdb.list_repositories())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/repository/create', methods=['POST'])
def create_graphdb_repository():
    try:
        data = request.json
        print(f"\n=== CREAZIONE REPOSITORY ===\nData: {data}")

        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        result = graphdb.create_repository(
            data['repo_id'],
            data.get('repo_title', data['repo_id']),
            data.get('ruleset', 'empty')
        )

        print(f"Risultato: {result}\n===========================")
        return jsonify(result)
    except Exception as e:
        print(f"ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/repository/delete', methods=['POST'])
def delete_graphdb_repository():
    try:
        data = request.json
        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        return jsonify(graphdb.delete_repository(data['repo_id']))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/upload/ontology', methods=['POST'])
def upload_ontology():
    try:
        data = request.json
        print(f"\n=== UPLOAD ONTOLOGIA ===\nData: {data}")

        if not os.path.exists(data['ontology_file']):
            return jsonify({'success': False, 'error': f'File non trovato: {data["ontology_file"]}'})

        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        result = graphdb.upload_file(
            data['repo_id'],
            data['ontology_file'],
            data.get('context', 'http://www.w3.org/2002/07/owl#ontology')
        )

        print(f"Risultato: {result}\n======================")
        return jsonify(result)
    except Exception as e:
        print(f"ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/convert/csv-to-rdf', methods=['POST'])
def convert_csv_to_rdf():
    try:
        data = request.json
        csv_path = data['csv_path']
        data_type = data.get('data_type', 'generic')

        print(f"\n=== CONVERSIONE CSV -> RDF ===")
        print(f"CSV: {csv_path}, Tipo: {data_type}")

        if not os.path.exists(csv_path):
            return jsonify({'success': False, 'error': f'File CSV non trovato: {csv_path}'})

        rml_converter = RMLConverter(False)
        rml_file = []

        if data_type == "group":
            rml_file = ["RMLGroup2.ttl"]
            pulisciCSV(csv_path)
        elif data_type == "question":
            rml_file = ["RMLQuestion.ttl"]
            cambiaNomeCSV(csv_path)
        elif data_type == "question_properties":
            rml_file = ["2_subquestions.ttl", "1_questions.ttl", "3_answeroptions.ttl", "4_attributes.ttl"]
            split_limesurvey_json(csv_path)  # è un json
        else:
            return jsonify({'success': False, 'error': f'Tipo non supportato: {data_type}'})

        if not os.path.exists(rml_file[0]):
            return jsonify({'success': False, 'error': f'File RML non trovato: {rml_file[0]}'})
        rml_output_file = []
        k = 0
        for i in rml_file:
            rml_converter.convert_rml_file(i)
            rml_output_file.append(Path(i).stem + "_output.ttl")
            rml_converter.save_to_file(rml_output_file[k])
            k = k + 1

        print(f"✅ Conversione OK: {rml_output_file}\n===================")
        return jsonify({'success': True, 'message': 'CSV convertito in RDF', 'output_paths': rml_output_file})

    except Exception as e:
        print(f"ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/upload/file', methods=['POST'])
def upload_file_to_server():
    try:
        print("\n=== UPLOAD FILE ===")

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file'})

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'Nome file vuoto'})

        output_dir = 'exports'
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, file.filename)
        file.save(filepath)

        print(f"File salvato: {filepath} ({os.path.getsize(filepath)} bytes)\n=================")
        return jsonify({'success': True, 'filepath': filepath, 'filename': file.filename})
    except Exception as e:
        print(f"ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/upload/data', methods=['POST'])
def upload_survey_data():
    """
    Upload survey data to GraphDB.
    Supports both single file and multiple files.
    """
    try:
        data = request.json
        print(f"\n=== UPLOAD DATI ===")
        print(f"Data received: {data}")

        # Get GraphDB instance
        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))

        # Clean survey_id
        survey_id = clean_uri_path(data.get("survey_id", ""))
        print(f"Survey ID pulito: '{survey_id}'")

        # Context map
        context_map = {
            'groups': f'http://example.org/survey/{survey_id}/groups',
            'questions': f'http://example.org/survey/{survey_id}/questions',
            'question_properties': f'http://example.org/survey/{survey_id}/properties'
        }

        # Get context URI
        base_context = data.get('context', context_map.get(data['data_type']))

        # Check if single file or multiple files
        file_path = data.get('file_path')
        file_paths = data.get('file_paths')

        # ============================================
        # CASO 1: SINGOLO FILE (backward compatibility)
        # ============================================
        if data.get('data_type') != "question_properties":
            print(f"📄 Uploading single file: {file_path}")

            # Validate file exists
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'error': f'File non trovato: {file_path}'
                })

            # Validate file type
            if file_path.endswith('.csv') or file_path.endswith('.json'):
                return jsonify({
                    'success': False,
                    'error': 'CSV/JSON non supportato, converti in RDF prima'
                })

            # Upload single file
            result = graphdb.upload_file(
                data['repo_id'],
                file_path,
                base_context
            )

            print(f"✅ Single file uploaded: {result}")
            return jsonify(result)

        # ============================================
        # CASO 2: MULTIPLI FILE
        # ============================================
        elif data.get('data_type') == "question_properties":
            file_paths = []
            file_paths = file_path.split(",")
            print(f"📦 Uploading {len(file_paths)} files")

            results = []
            failed = []
            for fp in file_paths:
                print(f"\n📄 [ Processing: {fp}")

                # Validate file exists
                if not os.path.exists(fp):
                    error_msg = f'File non trovato: {fp}'
                    print(f"❌ {error_msg}")
                    failed.append({'file': fp, 'error': error_msg})
                    continue

                # Validate file type
                if fp.endswith('.csv') or fp.endswith('.json'):
                    error_msg = f'CSV/JSON non supportato: {fp}'
                    print(f"❌ {error_msg}")
                    failed.append({'file': fp, 'error': error_msg})
                    continue

                # Create unique context for each file (optional)
                # Puoi usare lo stesso context o creare uno per file
                file_name = os.path.basename(fp).replace('.ttl', '')
                context_uri = f"{base_context}/{file_name}"

                print(f"Context URI: {context_uri}")

                try:
                    # Upload file
                    result = graphdb.upload_file(
                        data['repo_id'],
                        fp,
                        context_uri
                    )

                    if result.get('success'):
                        print(f"✅ Uploaded successfully")
                        results.append({
                            'file': fp,
                            'success': True,
                            'triples': result.get('triples', 0),
                            'context': context_uri
                        })
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        print(f"❌ Upload failed: {error_msg}")
                        failed.append({
                            'file': fp,
                            'error': error_msg
                        })

                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Exception: {error_msg}")
                    failed.append({
                        'file': fp,
                        'error': error_msg
                    })

            # Summary
            print(f"\n=== UPLOAD SUMMARY ===")
            print(f"Total files: {len(file_paths)}")
            print(f"Successful: {len(results)}")
            print(f"Failed: {len(failed)}")
            print(f"======================\n")

            # Return results
            if failed:
                return jsonify({
                    'success': len(results) > 0,  # Partial success if at least one succeeded
                    'message': f'Uploaded {len(results)}/{len(file_path)} files',
                    'results': results,
                    'failed': failed
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'All {len(results)} files uploaded successfully',
                    'results': results
                })

        # ============================================
        # CASO 3: NESSUN FILE SPECIFICATO
        # ============================================
        else:
            return jsonify({
                'success': False,
                'error': 'Missing file_path'
            })

    except Exception as e:
        print(f"\n❌ ERRORE GENERALE: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/graphdb/delete/survey', methods=['POST'])
def delete_survey_data():
    try:
        data = request.json
        # Pulisci survey_id usando la funzione helper
        survey_id = clean_uri_path(data.get("survey_id", ""))

        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        return jsonify(graphdb.clear_repository(
            data['repo_id'],
            f'http://example.org/survey/{survey_id}'
        ))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/delete/question', methods=['POST'])
def delete_question_data():
    try:
        data = request.json
        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        return jsonify(graphdb.delete_by_subject(
            data['repo_id'],
            f'http://example.org/question/{data["question_id"]}'
        ))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/delete/group', methods=['POST'])
def delete_group_data():
    try:
        data = request.json
        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        return jsonify(graphdb.delete_by_subject(
            data['repo_id'],
            f'http://example.org/group/{data["group_id"]}'
        ))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/query', methods=['POST'])
def graphdb_query():
    """Esegue una query SPARQL su GraphDB"""
    try:
        data = request.json
        print(f"\n=== SPARQL QUERY ===")
        print(f"Repository: {data['repo_id']}")

        graphdb_url = data.get('graphdb_url', 'http://localhost:7200')
        repo_id = data['repo_id']
        query = data['query']

        graphdb = GraphDBManager(graphdb_url)
        url = f"{graphdb.base_url}/repositories/{repo_id}"

        response = graphdb.session.post(
            url,
            data=query,
            headers={
                'Content-Type': 'application/sparql-query',
                'Accept': 'application/sparql-results+json'
            }
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result_data = response.json()
            print(f"Results: {len(result_data.get('results', {}).get('bindings', []))} bindings")
            return jsonify({'success': True, 'data': result_data})
        else:
            print(f"Error: {response.text}")
            return jsonify({'success': False, 'error': f'HTTP {response.status_code}: {response.text}'})

    except Exception as e:
        print(f"ERRORE query: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/graphdb/clear', methods=['POST'])
def clear_repository():
    try:
        data = request.json
        graphdb = GraphDBManager(data.get('graphdb_url', 'http://localhost:7200'))
        return jsonify(graphdb.clear_repository(data['repo_id']))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# SURVEY BUILDER

# ==================== SURVEY BUILDER API ROUTES  ====================
#
@app.route('/api/surveybuilder/config', methods=['POST'])
def set_surveybuilder_config():
    """Configura l'endpoint GraphDB"""
    global GRAPHDB_URL, REPOSITORY
    data = request.json
    GRAPHDB_URL = data.get('graphdb_url', GRAPHDB_URL)
    REPOSITORY = data.get('repository', REPOSITORY)
    return jsonify({"status": "ok", "graphdb_url": GRAPHDB_URL, "repository": REPOSITORY})


@app.route('/api/surveybuilder/test', methods=['GET'])
def test_surveybuilder_connection():
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

            SELECT ?class (COUNT(?instance) as ?count)
            WHERE {
                ?instance a ?class .
            }
            GROUP BY ?class
            ORDER BY DESC(?count)
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

        return jsonify({
            "status": "success",
            "connection": "OK",
            "repository": REPOSITORY,
            "total_triples": total_triples,
            "classes": classes
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "help": "Verifica che GraphDB sia in esecuzione e che il repository contenga dati"
        }), 500


@app.route('/api/surveybuilder/groups', methods=['GET'])
def get_surveybuilder_groups():
    """Recupera tutti i gruppi con le loro domande"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        groups = client.get_all_groups()
        return jsonify({"status": "success", "groups": groups})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/surveybuilder/questions', methods=['GET'])
def get_surveybuilder_questions():
    """Recupera tutte le domande"""
    try:
        client = GraphDBClient(GRAPHDB_URL, REPOSITORY)
        questions = client.get_all_questions()
        return jsonify({"status": "success", "questions": questions})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/surveybuilder/export/json', methods=['POST'])
def export_surveybuilder_json():
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


@app.route('/api/surveybuilder/export/csv', methods=['POST'])
def export_surveybuilder_csv():
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


@app.route('/api/surveybuilder/sparql/query', methods=['POST'])
def execute_surveybuilder_sparql_query():
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


@app.route('/api/surveybuilder/sparql/templates', methods=['GET'])
def get_surveybuilder_sparql_templates():
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
        }
    ]

    return jsonify({
        "status": "success",
        "templates": templates
    })


@app.route('/api/surveybuilder/limesurvey/config', methods=['POST'])
def set_surveybuilder_limesurvey_config():
    """Configura le credenziali LimeSurvey"""
    global LIMESURVEY_URL, LIMESURVEY_USERNAME, LIMESURVEY_PASSWORD
    data = request.json
    LIMESURVEY_URL = data.get('url', LIMESURVEY_URL)
    LIMESURVEY_USERNAME = data.get('username', LIMESURVEY_USERNAME)
    LIMESURVEY_PASSWORD = data.get('password', LIMESURVEY_PASSWORD)
    return jsonify({"status": "ok"})


@app.route('/api/surveybuilder/limesurvey/create', methods=['POST'])
def create_surveybuilder_limesurvey():
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

        # ✅ DEBUG: Mostra struttura dati ricevuti
        print("DEBUG: Data structure received:")
        print(f"  - Groups count: {len(groups)}")
        if groups:
            print(f"  - First group keys: {list(groups[0].keys())}")
        print(f"  - Questions count: {len(questions)}")
        if questions:
            print(f"  - First question keys: {list(questions[0].keys())}")
            first_q = questions[0]
            print(f"  - First question has subquestions: {'subquestions' in first_q}")
            print(f"  - First question has answerOptions: {'answerOptions' in first_q}")
            if 'subquestions' in first_q:
                print(f"    - Subquestions count: {len(first_q.get('subquestions', []))}")
            if 'answerOptions' in first_q:
                print(f"    - AnswerOptions count: {len(first_q.get('answerOptions', []))}")

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
                    question_id = question.get('id', 'N/A')
                    question_title = question.get('variableCod', f"Q{q_idx + 1}")
                    question_type = question.get('questionType', 'Unknown')

                    print(f"\n    [{q_idx + 1}/{len(group_questions)}] Processing Question:")
                    print(f"      ID: {question_id}")
                    print(f"      Title: {question_title}")
                    print(f"      Type: {question_type}")
                    print(f"      URI: {question_uri}")

                    # ✅ DEBUG: Mostra dati question dal frontend
                    print(f"      Frontend data:")
                    print(f"        - Has text: {bool(question.get('text'))}")
                    print(f"        - Text preview: {question.get('text', '')[:50]}...")
                    print(f"        - Has subquestions: {'subquestions' in question}")
                    print(f"        - Has answerOptions: {'answerOptions' in question}")
                    if 'subquestions' in question:
                        subs = question.get('subquestions', [])
                        print(f"        - Subquestions count from frontend: {len(subs)}")
                        if subs:
                            print(f"        - First subquestion: {subs[0]}")
                    if 'answerOptions' in question:
                        ans = question.get('answerOptions', [])
                        print(f"        - AnswerOptions count from frontend: {len(ans)}")
                        if ans:
                            print(f"        - First answer: {ans[0]}")

                    try:
                        # Ottieni dati completi dal GraphDB
                        print(f"      Fetching complete data from GraphDB...")
                        complete_data = graphdb_client.get_complete_question_data(question_uri)

                        # ✅ DEBUG: Verifica dati da GraphDB
                        if not complete_data:
                            print(f"      ✗ ERROR: get_complete_question_data returned None/empty")
                            failed_questions.append(f"{question_title} (ID:{question_id}): No data from GraphDB")
                            continue

                        print(f"      ✓ GraphDB data retrieved:")
                        print(f"        - QID: {complete_data.get('qid', 'N/A')}")
                        print(f"        - Type: {complete_data.get('type', 'N/A')}")
                        print(f"        - Title: {complete_data.get('title', 'N/A')}")
                        print(f"        - Text: {complete_data.get('questionText', 'N/A')[:50]}...")
                        print(f"        - Subquestions: {len(complete_data.get('subquestions', {}))}")
                        print(f"        - AnswerOptions: {len(complete_data.get('answerOptions', {}))}")
                        print(f"        - Attributes: {len(complete_data.get('attributes', {}))}")

                        # ✅ DEBUG: Mostra subquestions dettaglio
                        if complete_data.get('subquestions'):
                            print(f"        - Subquestions detail:")
                            if complete_data.get('subquestions'):
                                for idx, sub_data in enumerate(complete_data['subquestions'][:3]):
                                    print(f"          - {idx}: {sub_data.get('title', 'N/A')}")

                        # ✅ DEBUG: Mostra answer options dettaglio
                        if complete_data.get('answerOptions'):
                            print(f"        - AnswerOptions detail:")
                            if complete_data.get('answerOptions'):
                                for ans_data in complete_data['answerOptions'][:3]:
                                    print(
                                        f"          - [{ans_data.get('code', 'N/A')}]: {ans_data.get('text', 'N/A')[:30]}...")
                        # Aggiorna IDs per la nuova survey
                        complete_data['sid'] = str(survey_id)
                        complete_data['gid'] = str(group_id)

                        # Genera .lsq XML
                        print(f"      Generating .lsq XML...")
                        try:
                            lsq_xml = generate_lsq_xml(complete_data)
                            print(f"      ✓ XML generated: {len(lsq_xml)} bytes")
                        except Exception as xml_error:
                            print(f"      ✗ ERROR generating XML: {xml_error}")
                            import traceback
                            traceback.print_exc()
                            failed_questions.append(f"{question_title} (ID:{question_id}): XML generation failed - {str(xml_error)}")
                            continue

                        # Converti in Base64
                        lsq_base64 = base64.b64encode(lsq_xml.encode('utf-8')).decode('utf-8')
                        print(f"      Base64 size: {len(lsq_base64)} chars")

                        # Importa usando import_question
                        mandatory = complete_data.get('attributes', {}).get('mandatory', 'N')
                        print(f"      Importing to LimeSurvey (mandatory: {mandatory})...")

                        try:
                            new_qid = ls_client.import_question(
                                survey_id=survey_id,
                                group_id=group_id,
                                lsq_base64=lsq_base64,
                                mandatory=mandatory
                            )

                            print(f"      ✓ Question imported successfully (new ID: {new_qid})")
                            imported_questions_count += 1

                        except Exception as import_error:
                            print(f"      ✗ ERROR importing to LimeSurvey: {import_error}")
                            import traceback
                            traceback.print_exc()
                            failed_questions.append(f"{question_title} (ID:{question_id}): LimeSurvey import failed - {str(import_error)}")
                            continue

                    except Exception as e:
                        error_msg = f"{question_title} (ID:{question_id}): {str(e)}"
                        print(f"      ✗ Failed with exception: {e}")
                        import traceback
                        traceback.print_exc()
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
            for fail in failed_questions[:5]:  # Mostra primi 5 falliti
                print(f"  - {fail}")

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
        print(f"✗ FATAL ERROR: {str(e)}")
        print(f"{'=' * 70}\n")
        import traceback
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ==================== HTML ROUTES ====================
@app.route('/')
def home():
    """Homepage"""
    return render_template('home.html')


@app.route('/limesurvey')
def limesurvey_page():
    """LimeSurvey Manager page"""
    return render_template('limesurvey.html')


@app.route('/graphdb')
def graphdb_page():
    """GraphDB Manager page"""
    return render_template('graphdb.html')


@app.route('/surveybuilder')
def surveybuilder_page():
    """Survey Builder page"""
    return render_template('surveybuilder.html')


if __name__ == '__main__':
    print("\nServer starting on http://localhost:5005")
    print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5005)