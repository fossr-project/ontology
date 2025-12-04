import requests
import json
import csv
import os
from pathlib import Path
from typing import Optional, Union, List
from pyrml import Mapper, PyRML
from rdflib import Graph
from datetime import datetime
import base64
from typing import Optional, List, Dict, Any


def normalizzaJson(input_file):
    # Carica il JSON originale
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Definisci tutti i campi possibili per una question
    base_fields = {
        'qid', 'parent_qid', 'sid', 'gid', 'type', 'title', 'preg',
        'other', 'mandatory', 'encrypted', 'question_order', 'scale_id',
        'same_default', 'relevance', 'question_theme_name', 'modulename',
        'same_script', 'defaultvalue', 'available_answers', 'question_text'
    }

    normalized_data = []

    for question in data:
        normalized_q = {}

        # Copia tutti i campi base
        for field in base_fields:
            normalized_q[field] = question.get(field, None)

        # === NORMALIZZA SUBQUESTIONS ===
        subquestions = question.get('subquestions', [])
        if isinstance(subquestions, str) or subquestions is None:
            normalized_q['subquestions'] = []
        elif isinstance(subquestions, dict):
            subq_list = []
            for qid, subq in subquestions.items():
                normalized_subq = {
                    'qid': qid,
                    'parent_qid': question['qid'],
                    'title': subq.get('title', ''),
                    'question': subq.get('question', ''),
                    'scale_id': subq.get('scale_id', '0')
                }
                subq_list.append(normalized_subq)
            normalized_q['subquestions'] = subq_list
        else:
            normalized_q['subquestions'] = list(subquestions)

        # === NORMALIZZA ANSWEROPTIONS ===
        answeroptions = question.get('answeroptions', [])
        if isinstance(answeroptions, str) or answeroptions is None:
            normalized_q['answeroptions'] = []
        elif isinstance(answeroptions, dict):
            answer_list = []
            for code, answer in answeroptions.items():
                if isinstance(answer, dict):
                    normalized_answer = {
                        'code': code,
                        'parent_qid': question['qid'],
                        'answer': answer.get('answer', ''),
                        'assessment_value': answer.get('assessment_value', '0'),
                        'scale_id': answer.get('scale_id', '0'),
                        'order': answer.get('order', '0')
                    }
                    answer_list.append(normalized_answer)
            normalized_q['answeroptions'] = answer_list
        else:
            normalized_q['answeroptions'] = list(answeroptions)

        # === NORMALIZZA ATTRIBUTES ===
        attributes = question.get('attributes', {})
        if isinstance(attributes, str) or attributes is None:
            normalized_q['attributes'] = []
        elif isinstance(attributes, dict):
            attr_list = []
            for name, value in attributes.items():
                attr_list.append({
                    'name': name,
                    'value': str(value) if value is not None else '',
                    'parent_qid': question['qid']
                })
            normalized_q['attributes'] = attr_list
        else:
            normalized_q['attributes'] = list(attributes)

        # === NORMALIZZA ATTRIBUTES_LANG ===
        attributes_lang = question.get('attributes_lang', {})
        if isinstance(attributes_lang, str) or attributes_lang is None:
            normalized_q['attributes_lang'] = []
        elif isinstance(attributes_lang, dict):
            attr_lang_list = []
            for name, value in attributes_lang.items():
                attr_lang_list.append({
                    'name': name,
                    'value': str(value) if value is not None else '',
                    'parent_qid': question['qid']
                })
            normalized_q['attributes_lang'] = attr_lang_list
        else:
            normalized_q['attributes_lang'] = list(attributes_lang)

        # Estrai question_text se non esiste
        if not normalized_q.get('question_text'):
            # Prova a estrarre da available_answers se è un dict
            avail_ans = question.get('available_answers', '')
            if isinstance(avail_ans, dict):
                # Prendi il primo valore
                normalized_q['question_text'] = list(avail_ans.values())[0] if avail_ans else ''
            else:
                normalized_q['question_text'] = ''

        normalized_data.append(normalized_q)

    output_file="questions_normalized.json"
    # Salva il JSON normalizzato
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized_data, f, indent=2, ensure_ascii=False)

    print(f"✓ JSON normalizzato salvato in: {output_file}")
    print(f"✓ Totale questions processate: {len(normalized_data)}")

    # Statistiche
    total_subq = sum(len(q['subquestions']) for q in normalized_data)
    total_ans = sum(len(q['answeroptions']) for q in normalized_data)
    total_attr = sum(len(q['attributes']) for q in normalized_data)

    print(f"✓ Totale subquestions: {total_subq}")
    print(f"✓ Totale answeroptions: {total_ans}")
    print(f"✓ Totale attributes: {total_attr}")


def pulisciCSV(input_file):
    temp_file = "tmp_cleaned_raw.csv"
    output_file = "list_groups_20251014_105921.csv"

    # 1. Normalizza TUTTE le virgolette doppie interne prima della lettura
    with open(input_file, encoding="utf-8") as f_in, open(temp_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            # sostituisci "" con ' (più sicuro nel CSV)
            line = line.replace('""', "'")
            f_out.write(line)

    # 2. Ricostruzione robusta delle righe
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

    # 3. Scrivi il CSV finale
    with open(output_file, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        for line in rows:
            writer.writerow(next(csv.reader([line])))

def ensure_dict(value):
    """Ritorna un dizionario se possibile, altrimenti un dizionario vuoto."""
    return value if isinstance(value, dict) else {}

def appiattisci_json(j, prefisso=""):#j è un json
    risultato = {}
    for k, v in j.items():
        nuova_chiave = f"{prefisso}{k}" if not prefisso else f"{prefisso}_{k}"
        if isinstance(v, dict):
            # Ricorsione per appiattire sottodizionari
            risultato.update(appiattisci_json(v, nuova_chiave))
        else:
            risultato[nuova_chiave] = v
    return risultato

def dividi_dizionario(data, prefisso=""):
    risultato=[]
    qid = data["qid"]
    sid = data["sid"]
    gid = data["gid"]
    parent_qid = data["parent_qid"]
    print("sono dentro dividi dizionario")
    # --- 1️⃣ QUESTIONS ---
    questions = [{
        "qid": qid,
        "sid": sid,
        "gid": gid,
        "parent_qid": parent_qid,
        "title": data["title"],
        "type": data["type"],
        "mandatory": data["mandatory"],
        "same_script": data["same_script"],
        "modulename":data["modulename"],
        "relevance": data["relevance"],
        "question_theme_name": data["question_theme_name"],
        "defaultvalue": data["defaultvalue"]
    }]

    # --- 2️⃣ SUBQUESTIONS ---
    subquestions = [
        {"qid": qid,
        "parent_qid": parent_qid,"sub_id": k, **v}

        for k, v in ensure_dict(data.get("subquestions", {})).items()
    ]

    # --- 3️⃣ AVAILABLE ANSWERS ---
    available_answers = [
        {"qid": qid,
        "parent_qid": parent_qid,"code": k, "text": v}
        for k, v in ensure_dict(data.get("available_answers")).items()
    ]

    # --- 4️⃣ ATTRIBUTES ---
    attributes = [
        {"qid": qid,
        "parent_qid": parent_qid, "attribute": k, "value": v}
        for k, v in ensure_dict(data.get("attributes", {})).items()
    ]

    # --- 5️⃣ ATTRIBUTES LANG ---
    attributes_lang = [
        {"qid": qid,
        "parent_qid": parent_qid,
        "attribute": k, "value": v}
        for k, v in ensure_dict(data.get("attributes_lang", {})).items()
    ]

    # --- 6️⃣ ANSWER OPTIONS ---
    answeroptions = [
        {"qid": qid,
        "parent_qid": parent_qid, "ao_code": k, **v}
        for k, v in ensure_dict(data.get("answeroptions", {})).items()
    ]
    risultato = [questions,subquestions,available_answers,attributes, attributes_lang, answeroptions]
    print("dividi dizionario ",risultato)
    return risultato


def appiattisci_dizionario(d,parent_key='', sep='_'):#d è un dizionario
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            # Se il valore è un dizionario, ricorsione
            items.extend(appiattisci_dizionario(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Se è una lista, aggiungi un indice
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(appiattisci_dizionario(item, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            # Valore semplice
            items.append((new_key, v))

    return dict(items)



def ex(data, api, operation):
    if operation == 'list_surveys':
        result = api.list_surveys()
        result = [appiattisci_json(item) for item in result]
    elif operation == 'get_survey_properties':
        result1 = api.get_survey_properties(data['survey_id'])
        result1 = appiattisci_dizionario(result1)
        result = []
        result.append(result1)
    elif operation == 'get_question_properties':
        result1 = api.get_question_properties(data['question_id'])#restituisce un dizionario
        result = dividi_dizionario(result1)#restituisce la lista di liste
        return result
    elif operation == 'list_questions':
        result = api.list_questions(data['survey_id'])
        result = [appiattisci_json(item) for item in result]
    elif operation == 'list_groups':
        result = api.list_groups(data['survey_id'])
        result = [appiattisci_json(item) for item in result]
    elif operation == 'list_participants':
        result = api.list_participants(data['survey_id'])
        result = [appiattisci_json(item) for item in result]

    elif operation == 'get_summary':
        result = api.get_summary(data['survey_id'])
    return result




class LimeSurveyAPI:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.session_key = None

    def _call(self, method, params):
        payload = {
            'method': method,
            'params': params,
            'id': 1
        }
        response = requests.post(
            self.url,
            json=payload,
            headers={'content-type': 'application/json'}
        )
        result = response.json()
        return result.get('result')

    def get_session_key(self):
        self.session_key = self._call('get_session_key', [self.username, self.password])
        if isinstance(self.session_key, dict) and 'status' in self.session_key:
            raise Exception(self.session_key.get('status'))
        return self.session_key

    def list_surveys(self):
        if not self.session_key:
            self.get_session_key()
        return self._call('list_surveys', [self.session_key])

    def get_survey_properties(self, survey_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('get_survey_properties', [self.session_key, survey_id])

    def list_questions(self,survey_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('list_questions', [self.session_key,survey_id])
    def list_groups(self, survey_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('list_groups', [self.session_key,survey_id])
    def list_participants(self, survey_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('list_participants', [self.session_key, survey_id])

    def export_responses(self, survey_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('export_responses', [self.session_key, survey_id, 'json'])

    def get_summary(self, survey_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('get_summary', [self.session_key, survey_id])

    def release_session_key(self):
        if self.session_key:
            self._call('release_session_key', [self.session_key])

    def get_question_properties(self, question_id):
        if not self.session_key:
            self.get_session_key()
        return self._call('get_question_properties', [self.session_key,  question_id])

    def connect(self):
        """Connetti e ottieni session key"""
        self.get_session_key()
        return self

    def disconnect(self):
        """Disconnetti e rilascia session key"""
        self.release_session_key()

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

class LimeSurveyExporter:

    def __init__(self, url: str, username: str, password: str, output_dir: str = 'exports'):

        self.url = url
        self.username = username
        self.password = password
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_api(self) -> LimeSurveyAPI:
        return LimeSurveyAPI(self.url, self.username, self.password)
   # def _save_to_json(self, data:List):

    def _save_to_json(self, data: List[Dict],filename:str) -> Path:
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Dati vuoti o non validi per l'export Json")
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ JSON trasformato salvato in: {filepath}")
        print(f"✅ Processate {len(data)} question(s)")

        return filepath
    def _save_to_csv(self, data: List[Dict], operation: str) -> Path:
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("Dati vuoti o non validi per l'export CSV")

            # Genera nome file con timestamp
        filename = f'{operation}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = self.output_dir / filename

            # Scrivi CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=',')
            writer.writeheader()
            writer.writerows(data)

        return filepath

    def export_surveys(self) -> Path:

        api = self._get_api()
        try:
            api.connect()
            data = api.list_surveys()
            return self._save_to_csv(data, 'list_surveys')
        finally:
            api.disconnect()

    def export_groups(self, survey_id: int) -> Path:

        api = self._get_api()
        try:
            api.connect()
            data = api.list_groups(survey_id)
            return self._save_to_csv(data, f'list_groups_{survey_id}')
        finally:
            api.disconnect()

    def export_questions(self, survey_id: int) -> Path:

        api = self._get_api()
        try:
            api.connect()
            data = api.list_questions(survey_id)
            return self._save_to_csv(data, f'list_questions_{survey_id}')
        finally:
            api.disconnect()

    def export_participants(self, survey_id: int) -> Path:

        api = self._get_api()
        try:
            api.connect()
            data = api.list_participants(survey_id)
            return self._save_to_csv(data, f'list_participants_{survey_id}')
        finally:
            api.disconnect()

    def export_responses(self, survey_id: int) -> Path:

        api = self._get_api()
        try:
            api.connect()
            data = api.export_responses(survey_id)
            return self._save_to_csv(data, f'export_responses_{survey_id}')
        finally:
            api.disconnect()

    def export_one_question_properties(self, question_id) -> list:
        api = self._get_api()
        try:
            api.connect()
            data = api.get_question_properties(question_id)
            print(data)
        except Exception as e:
            print(f"✗ Errore export question properties: {e}")
        finally:
            api.disconnect()
    def export_question_properties(self, question_id,api)->list:
        try:
            #data = dividi_dizionario(api.get_question_properties(question_id))#restituisce una lista di liste
            data=api.get_question_properties(question_id)#restituisce un json
        except Exception as e:
            print(f"✗ Errore export question properties: {e}")
        finally:
            return data

    def export_all_question_properties_survey(self,survey_id)->Path:
        api = self._get_api()
        try:
            api.connect()
            data1 = api.list_questions(survey_id)
            print("sono all'inizio")
            data = []
            k=0

            for e in data1:#ciclo sulle domande della survey
                risultato_intermedio=self.export_question_properties(e['qid'],api)#ritorna un json annidato
                print(risultato_intermedio)
                data.append(risultato_intermedio)
            #     k=k+1
            #     if k==1:
            #         for i in range(len(risultato_intermedio)):
            #             data.append(risultato_intermedio[i])
            #             print("ris int",risultato_intermedio[i],"lista data",data)
            #     else:
            #         for i in range(0,len(risultato_intermedio)):
            #             if risultato_intermedio[i] !=[]:
            #                 data[i].append(risultato_intermedio[i][0])
            #             print("ris int",risultato_intermedio[i],"lista data",data)
            #
            # i=0
            # for e in data:
            #     i=i+1
            #     print("dentro if")
            #     self._save_to_csv(e, f'export_all_question_properties_survey_{survey_id}_{i}')
            #     print( "f'export_all_question_properties_survey_{survey_id}_{i}",i,survey_id)
            self._save_to_json(data, "questions.json")
            print("f'export_all_question_properties_survey_{survey_id}", survey_id)
        except Exception as e:
            print(f"✗ Errore export export_all_question_properties_survey: {e}")
        finally:
            return f'export_all_question_properties_survey_{survey_id}'



    def export_all(self, survey_id: int) -> Dict[str, Path]:
        """
        Esporta tutti i dati di un sondaggio (gruppi, domande, partecipanti, risposte)

        Args:
            survey_id: ID del sondaggio

        Returns:
            Dizionario con i path dei file creati
        """
        results = {}

        try:
            results['groups'] = self.export_groups(survey_id)
            print(f"✓ Gruppi esportati: {results['groups']}")
        except Exception as e:
            print(f"✗ Errore export gruppi: {e}")

        try:
            results['questions'] = self.export_questions(survey_id)
            print(f"✓ Domande esportate: {results['questions']}")
        except Exception as e:
            print(f"✗ Errore export domande: {e}")

        try:
            results['participants'] = self.export_participants(survey_id)
            print(f"✓ Partecipanti esportati: {results['participants']}")
        except Exception as e:
            print(f"✗ Errore export partecipanti: {e}")

        try:
            results['responses'] = self.export_responses(survey_id)
            print(f"✓ Risposte esportate: {results['responses']}")
        except Exception as e:
            print(f"✗ Errore export risposte: {e}")

        return results

    def export_operation(self, operation: str, survey_id: Optional[int] = None) -> Path:

        operation_map = {
            'list_surveys': lambda: self.export_surveys(),
            'list_groups': lambda: self.export_groups(survey_id),
            'list_questions': lambda: self.export_questions(survey_id),
            'list_participants': lambda: self.export_participants(survey_id),
            'export_responses': lambda: self.export_responses(survey_id),
            'export_all_question_properties_survey':lambda: self.export_all_question_properties_survey(survey_id),
            'export_question_properties': lambda: self.export_question_properties(question_id=1),
            'export_one_question_properties' : lambda: self.export_one_question_properties(question_id=1)
        }

        if operation not in operation_map:
            raise ValueError(f"Operazione '{operation}' non supportata")

        if operation != 'list_surveys' and survey_id is None:
            raise ValueError(f"L'operazione '{operation}' richiede un survey_id")

        return operation_map[operation]()


class GraphDBManager:
    """
    Gestisce la connessione e le operazioni con GraphDB
    """

    def __init__(self, base_url="http://localhost:7200", username=None, password=None):
        """
        Inizializza il manager per GraphDB

        Args:
            base_url: URL base di GraphDB (default: http://localhost:7200)
            username: Username per l'autenticazione (opzionale)
            password: Password per l'autenticazione (opzionale)
        """
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()
        if self.auth:
            self.session.auth = self.auth

    def create_repository(self, repo_id, repo_title=None, repo_type="graphdb",ruleset="owl-horst-optimized"):
        """
        Crea un nuovo repository in GraphDB

        Args:
            repo_id: ID del repository
            repo_title: Titolo del repository (opzionale)
            repo_type: Tipo di repository (default: graphdb)
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
            print(f"✓ Repository '{repo_id}' creato con successo")
            return True
        elif response.status_code == 409:
            print(f"⚠ Repository '{repo_id}' già esistente")
            return True
        else:
            print(f"✗ Errore nella creazione del repository: {response.status_code}")
            print(f"  Dettagli: {response.text}")
            return False

    def delete_repository(self, repo_id):
        """Elimina un repository esistente"""
        url = f"{self.base_url}/rest/repositories/{repo_id}"
        response = self.session.delete(url)

        if response.status_code == 200:
            print(f"✓ Repository '{repo_id}' eliminato con successo")
            return True
        else:
            print(f"✗ Errore nell'eliminazione del repository: {response.status_code}")
            return False

    def list_repositories(self):
        """Elenca tutti i repository disponibili"""
        url = f"{self.base_url}/rest/repositories"
        response = self.session.get(url)

        if response.status_code == 200:
            repos = response.json()
            print(f"\nRepository disponibili ({len(repos)}):")
            for repo in repos:
                print(f"  - {repo['id']}: {repo.get('title', 'N/A')}")
            return repos
        else:
            print(f"✗ Errore nel recupero dei repository: {response.status_code}")
            return []

    def upload_file(self, repo_id, file_path, context=None, file_format=None):
        """
        Carica un file RDF nel repository

        Args:
            repo_id: ID del repository
            file_path: Percorso del file da caricare
            context: Named graph in cui caricare i dati (opzionale)
            file_format: Formato del file (auto-detect se None)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"✗ File non trovato: {file_path}")
            return False

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

        url = f"{self.base_url}/repositories/{repo_id}/statements"
        if context:
            url += f"?context=<{context}>"

        headers = {"Content-Type": file_format}

        with open(file_path, 'rb') as f:
            response = self.session.post(url, data=f, headers=headers)

        if response.status_code in [200, 201, 204]:
            print(f"✓ File '{file_path.name}' caricato con successo in '{repo_id}'")
            return True
        else:
            print(f"✗ Errore nel caricamento del file: {response.status_code}")
            print(f"  Dettagli: {response.text}")
            return False

    def upload_graph(self, repo_id, rdf_graph: Graph, context=None, file_format='text/turtle'):
        """
        Carica un grafo RDFLib direttamente nel repository

        Args:
            repo_id: ID del repository
            rdf_graph: Grafo RDFLib da caricare
            context: Named graph in cui caricare i dati (opzionale)
            file_format: Formato di serializzazione (default: text/turtle)
        """
        # Serializza il grafo in una stringa
        rdf_data = rdf_graph.serialize(format='turtle')

        url = f"{self.base_url}/repositories/{repo_id}/statements"
        if context:
            url += f"?context=<{context}>"

        headers = {"Content-Type": file_format}

        response = self.session.post(url, data=rdf_data.encode('utf-8'), headers=headers)

        if response.status_code in [200, 201, 204]:
            print(f"✓ Grafo RDF caricato con successo in '{repo_id}' ({len(rdf_graph)} triple)")
            return True
        else:
            print(f"✗ Errore nel caricamento del grafo: {response.status_code}")
            print(f"  Dettagli: {response.text}")
            return False

    def execute_sparql_query(self, repo_id, query):
        """Esegue una query SPARQL"""
        url = f"{self.base_url}/repositories/{repo_id}"
        headers = {"Accept": "application/sparql-results+json"}
        params = {"query": query}

        response = self.session.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Errore nell'esecuzione della query: {response.status_code}")
            print(f"  Dettagli: {response.text}")
            return None

    def clear_repository(self, repo_id, context=None):
        """Svuota un repository o un named graph specifico"""
        url = f"{self.base_url}/repositories/{repo_id}/statements"
        if context:
            url += f"?context=<{context}>"

        response = self.session.delete(url)

        if response.status_code in [200, 204]:
            target = f"named graph '{context}'" if context else "repository"
            print(f"✓ {target} svuotato con successo")
            return True
        else:
            print(f"✗ Errore nello svuotamento: {response.status_code}{response.text}")
            return False


class RMLConverter:
    """
    Classe per convertire file CSV in RDF usando RML mapping
    """

    def __init__(self, strict_mode: bool = False):
        """
        Inizializza il converter RML

        Args:
            strict_mode: Se True, abilita la modalità strict per RML (default: False)
        """
        PyRML.RML_STRICT = strict_mode
        self.mapper: Mapper = PyRML.get_mapper()
        self.rdf_graph: Optional[Graph] = None

    def convert_rml_file(self, rml_file_path: Union[str, Path]) -> Graph:
        """
        Converte un file RML mapping in un grafo RDF

        Args:
            rml_file_path: Percorso del file RML mapping

        Returns:
            Graph: Grafo RDF risultante dalla conversione
        """
        rml_file_path = Path(rml_file_path)

        if not rml_file_path.exists():
            raise FileNotFoundError(f"File RML non trovato: {rml_file_path}")

        print(f"📂 Caricamento file RML: {rml_file_path}")

        try:
            self.rdf_graph = self.mapper.convert(str(rml_file_path))
            print(f"✓ Conversione completata: {len(self.rdf_graph)} triple generate")
            return self.rdf_graph
        except Exception as e:
            print(f"✗ Errore durante la conversione: {str(e)}")
            raise

    def save_to_file(self, output_file: Union[str, Path], format: str = 'turtle') -> bool:
        """
        Salva il grafo RDF in un file

        Args:
            output_file: Percorso del file di output
            format: Formato di serializzazione (turtle, xml, n3, nt, json-ld)
        """
        if self.rdf_graph is None:
            raise ValueError("Nessun grafo RDF disponibile. Esegui prima convert_rml_file()")

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.rdf_graph.serialize(destination=str(output_file), format=format)
            print(f"✓ File salvato: {output_file} (formato: {format})")
            return True
        except Exception as e:
            print(f"✗ Errore nel salvataggio del file: {str(e)}")
            return False

    def get_triples_count(self) -> int:
        """Restituisce il numero di triple nel grafo"""
        if self.rdf_graph is None:
            return 0
        return len(self.rdf_graph)

    def print_triples(self, limit: Optional[int] = None):
        """Stampa le triple del grafo"""
        if self.rdf_graph is None:
            print("⚠ Nessun grafo RDF disponibile")
            return

        print(f"\n📊 Triple nel grafo (totale: {len(self.rdf_graph)}):")
        print("-" * 80)

        for i, (s, p, o) in enumerate(self.rdf_graph):
            if limit and i >= limit:
                print(f"\n... ({len(self.rdf_graph) - limit} triple rimanenti)")
                break
            print(f"{s} {p} {o}")

    def get_graph(self) -> Optional[Graph]:
        """Restituisce il grafo RDF corrente"""
        return self.rdf_graph


class RMLtoGraphDBPipeline:
    """
    Pipeline completa: RML -> RDF -> GraphDB
    """

    def __init__(self, graphdb_url="http://localhost:7200",
                 username=None, password=None, strict_mode=False):
        """
        Inizializza la pipeline completa

        Args:
            graphdb_url: URL di GraphDB
            username: Username per GraphDB (opzionale)
            password: Password per GraphDB (opzionale)
            strict_mode: Modalità strict per RML (default: False)
        """
        self.rml_converter = RMLConverter(strict_mode=strict_mode)
        self.graphdb = GraphDBManager(graphdb_url, username, password)

    def process_and_upload(self, rml_file: Union[str, Path],
                           repo_id: str,
                           context: Optional[str] = None,
                           save_local: bool = False,
                           output_file: Optional[Union[str, Path]] = None) -> bool:
        """
        Processo completo: converte RML e carica direttamente in GraphDB

        Args:
            rml_file: File RML mapping
            repo_id: ID del repository GraphDB
            context: Named graph per i dati (opzionale)
            save_local: Se True, salva anche localmente il file TTL
            output_file: Nome del file locale (se save_local=True)

        Returns:
            bool: True se l'operazione è completata con successo
        """
        try:
            print("\n" + "=" * 80)
            print("🚀 AVVIO PIPELINE RML -> GraphDB")
            print("=" * 80)

            # Step 1: Converti RML in RDF
            print("\n[Step 1/3] Conversione RML -> RDF")
            self.rml_converter.convert_rml_file(rml_file)

            # Step 2: Salva localmente (opzionale)
            if save_local:
                print("\n[Step 2/3] Salvataggio file locale")
                if output_file is None:
                    output_file = Path(rml_file).stem + "_output.ttl"
                self.rml_converter.save_to_file(output_file)
            else:
                print("\n[Step 2/3] Salvataggio file locale - SALTATO")

            # Step 3: Carica in GraphDB
            print("\n[Step 3/3] Caricamento in GraphDB")
            graph = self.rml_converter.get_graph()
            success = self.graphdb.upload_graph(repo_id, graph, context=context)

            if success:
                print("\n" + "=" * 80)
                print("✅ PIPELINE COMPLETATA CON SUCCESSO!")
                print(f"   Triple caricate: {len(graph)}")
                print(f"   Repository: {repo_id}")
                if context:
                    print(f"   Named Graph: {context}")
                print("=" * 80)

            return success

        except Exception as e:
            print(f"\n❌ ERRORE NELLA PIPELINE: {str(e)}")
            return False

    def batch_process(self, rml_files: List[Union[str, Path]],
                      repo_id: str,
                      contexts: Optional[List[str]] = None) -> dict:
        """
        Processa multipli file RML e li carica in GraphDB

        Args:
            rml_files: Lista di file RML da processare
            repo_id: ID del repository GraphDB
            contexts: Lista di named graphs (opzionale, uno per file)

        Returns:
            dict: Statistiche del processo batch
        """
        results = {
            'success': [],
            'failed': [],
            'total_triples': 0
        }

        if contexts is None:
            contexts = [None] * len(rml_files)

        for i, (rml_file, context) in enumerate(zip(rml_files, contexts), 1):
            print(f"\n{'=' * 80}")
            print(f"📦 Processamento file {i}/{len(rml_files)}: {rml_file}")
            print(f"{'=' * 80}")

            success = self.process_and_upload(rml_file, repo_id, context)

            if success:
                results['success'].append(str(rml_file))
                results['total_triples'] += self.rml_converter.get_triples_count()
            else:
                results['failed'].append(str(rml_file))

        # Riepilogo
        print(f"\n{'=' * 80}")
        print("📊 RIEPILOGO PROCESSO BATCH")
        print(f"{'=' * 80}")
        print(f"✓ File processati con successo: {len(results['success'])}")
        print(f"✗ File falliti: {len(results['failed'])}")
        print(f"📈 Totale triple caricate: {results['total_triples']}")
        if results['failed']:
            print(f"\nFile falliti:")
            for f in results['failed']:
                print(f"  - {f}")
        print(f"{'=' * 80}\n")

        return results

    def setup_repository(self, repo_id: str, repo_title: Optional[str] = None,
                         clear_if_exists: bool = False,
                         ontology_file: Optional[Union[str, Path]] = None,
                         ontology_context: Optional[str] = None) -> bool:
        """
        Configura un repository GraphDB e carica l'ontologia

        Args:
            repo_id: ID del repository
            repo_title: Titolo del repository (opzionale)
            clear_if_exists: Se True, svuota il repository se esiste già
            ontology_file: File dell'ontologia da caricare (opzionale)
            ontology_context: Named graph per l'ontologia (opzionale)

        Returns:
            bool: True se configurato con successo
        """
        success = self.graphdb.create_repository(repo_id, repo_title)

        if success and clear_if_exists:
            print(f"🧹 Pulizia repository esistente...")
            self.graphdb.clear_repository(repo_id)

        # Carica l'ontologia se specificata
        if success and ontology_file:
            print(f"\n📚 Caricamento ontologia...")
            success = self.load_ontology(repo_id, ontology_file, ontology_context)

        return success

    def load_ontology(self, repo_id: str, ontology_file: Union[str, Path],
                      context: Optional[str] = None) -> bool:
        """
        Carica un file di ontologia nel repository

        Args:
            repo_id: ID del repository
            ontology_file: File dell'ontologia (TTL, RDF/XML, OWL, etc.)
            context: Named graph per l'ontologia (opzionale)

        Returns:
            bool: True se caricato con successo
        """
        ontology_file = Path(ontology_file)

        if not ontology_file.exists():
            print(f"✗ File ontologia non trovato: {ontology_file}")
            return False

        print(f"📚 Caricamento ontologia: {ontology_file}")

        # Se non specificato, usa un context di default per l'ontologia
        if context is None:
            context = "http://www.w3.org/2002/07/owl#ontology"
        self.graphdb.create_repository("test_repo","test_repo")
        success = self.graphdb.upload_file(repo_id, ontology_file, context=context)

        if success:
            print(f"✓ Ontologia caricata nel named graph: {context}")

        return success


# Esempio di utilizzo completo
if __name__ == "__main__":

    # ============================================
    # ESEMPIO 1: Pipeline semplice
    # ============================================
    print("\n🔷 ESEMPIO 1: Pipeline Semplice")
   # s = input("inserisci il numero di survey")
    #esporto survey properties, group, question e question_properties


    a=LimeSurveyExporter(
        url="http://127.0.0.1/limesurvey/index.php/admin/remotecontrol",
        username="sara",
        password="sara"
    )
   # filepath = a.export_all_question_properties_survey(survey_id=694511)
    #print(f"Salvato in: {filepath}")

    # Export completo di un sondaggio
    #fileProperties=a.export_question(survey_id=694511)
    #fileProperties=a.export_one_question_properties(446)
    pipeline = RMLtoGraphDBPipeline(
        graphdb_url="http://localhost:7200",
        username="admin",
        password="admin"
     )
     #response = requests.get("http://localhost:7200/rest/repositories/")
    # #print("Status code:", response.status_code)
    # #print("Content-Type:", response.headers.get('Content-Type'))
    # #print("Response text:", response.text[:500])  # Primi 500 caratteri
    # # Setup repository
   # pipeline.setup_repository(
   #     repo_id="test_repo",
   #     repo_title="LimeSurvey Knowledge Graph",
   #     clear_if_exists=True
    # )
    pipeline.load_ontology(
        repo_id="test_repo",
        ontology_file="limesurvey.ttl",
        context="http://example.org/ontology"
     )
    from requests import get
    try:
         response = get("http://localhost:7200/rest/repositories")
         if response.status_code == 200:
             print("✓ GraphDB raggiungibile")
             print(f"Repository esistenti: {response.json()}")
         else:
             print(f"✗ Errore: {response.status_code}")
    except Exception as e:
         print(f"✗ GraphDB non raggiungibile: {e}")
    #
    #
    # # Processa e carica
    #pulisciCSV( "list_groups_694511_20251119_085223.csv")
   # pipeline.process_and_upload(
   #      rml_file="RMLGroup2.ttl",
   #      repo_id="test_repo",
   #      context="http://example.org/groups",
   #      save_local=True,
   #      output_file="output2_groups.ttl"
   #)
    pipeline.process_and_upload(
         rml_file="RMLQuestion.ttl",
        repo_id="test_repo",
        context="http://example.org/question",
        save_local=True,
        output_file="prova.ttl"
    )
    converter = RMLConverter()
#    normalizzaJson("questionspiccolo.json")
 #   pipeline.process_and_upload(
 #       rml_file="RMLQuestionFromJson.ttl",
 #       repo_id="test_repo",
 #       context="http://example.org/question",
 #       save_local=True,
  #      output_file="output.ttl"
  #  )

    # ============================================
    # ESEMPIO 2: Processo batch multipli file
    # ============================================
    # print("\n🔷 ESEMPIO 2: Processo Batch")
    #
    # pipeline2 = RMLtoGraphDBPipeline(graphdb_url="http://localhost:7200")
    #
    # # Setup repository
    # pipeline2.setup_repository("survey_complete", "Survey Complete Data")
    #
    # # Processa multipli file
    # results = pipeline2.batch_process(
    #     rml_files=[
    #         "groupLime.ttl",
    #         "questionsLime.ttl",
    #         "answersLime.ttl"
    #     ],
    #     repo_id="survey_complete",
    #     contexts=[
    #         "http://example.org/groups",
    #         "http://example.org/questions",
    #         "http://example.org/answers"
    #     ]
    # )
    #
    # # ============================================
    # # ESEMPIO 3: Uso separato dei componenti
    # # ============================================
    # print("\n🔷 ESEMPIO 3: Uso Separato")
    #
    # # Converti RML

    # converter.convert_rml_file("groupLime.ttl")
    # converter.print_triples(limit=5)
    # converter.save_to_file("local_output.ttl")
    #
    # # Carica in GraphDB
    #graphdb = GraphDBManager("http://localhost:7200")
    #graphdb.create_repository("test_repo")
    #graphdb.upload_graph("test_repo", converter.get_graph())
    #
    # # Query SPARQL
    # query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
    # results = graphdb.execute_sparql_query("test_repo", query)
    # if results:
    #     count = results['results']['bindings'][0]['count']['value']
    #     print(f"\n✓ Totale triple nel repository: {count}")