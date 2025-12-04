"""
Convertitore RML conforme all'ontologia LimeSurvey
Versione corretta basata su limesurvey.ttl
"""

import json
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
from pathlib import Path

# Namespace
LS = Namespace("https://w3id.org/fossr/ontology/limesurvey/")
EX = Namespace("http://w3id.org/fossr/data/")


def load_json(filepath):
    """Carica il file JSON"""
    print(f"📄 Caricamento JSON: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Caricate {len(data)} questions")
    return data


def convert_questions_to_rdf(json_data, output_file):
    """
    Converte il JSON delle questions in RDF seguendo l'ontologia LimeSurvey CORRETTA
    """
    print("\n⚙️  Conversione in RDF...")

    # Crea il grafo RDF
    g = Graph()
    g.bind("ls", LS)
    g.bind("ex", EX)
    g.bind("xsd", XSD)

    stats = {
        'questions': 0,
        'subquestions': 0,
        'answeroptions': 0,
        'attributes': 0
    }

    for question in json_data:
        qid = question.get('qid')
        if not qid:
            continue

        # URI della question
        question_uri = EX[f"question_{qid}"]

        # === QUESTION PRINCIPALE ===
        g.add((question_uri, RDF.type, LS.Question))

        # Identifier entity
        if question.get('qid'):
            id_uri = EX[f"identifier_question_{qid}"]
            g.add((id_uri, RDF.type, LS.Identifier))
            g.add((id_uri, LS.id, Literal(int(question['qid']), datatype=XSD.int)))
            g.add((question_uri, LS.hasId, id_uri))

        # Survey ID entity
        if question.get('sid'):
            sid_uri = EX[f"identifier_survey_{question['sid']}"]
            g.add((sid_uri, RDF.type, LS.Identifier))
            g.add((sid_uri, LS.id, Literal(int(question['sid']), datatype=XSD.int)))
            g.add((question_uri, LS.hasSurveyId, sid_uri))

        # Group reference
        if question.get('gid'):
            group_uri = EX[f"group_{question['gid']}"]
            g.add((question_uri, LS.hasGroup, group_uri))

        # Question Type entity
        if question.get('type'):
            type_uri = EX[f"questiontype_{question['type']}"]
            g.add((type_uri, RDF.type, LS.QuestionType))
            g.add((question_uri, LS.hasType, type_uri))

        # Variable entity
        if question.get('title'):
            var_uri = EX[f"variable_{question['title']}"]
            g.add((var_uri, RDF.type, LS.Variable))
            g.add((var_uri, LS.variableCod, Literal(question['title'])))
            g.add((question_uri, LS.hasVariable, var_uri))

        # Name entity
        if question.get('title'):
            name_uri = EX[f"name_question_{qid}"]
            g.add((name_uri, RDF.type, LS.Name))
            g.add((name_uri, LS.nameText, Literal(question['title'])))
            g.add((question_uri, LS.hasName, name_uri))

        # Content entity
        if question.get('question_text'):
            content_uri = EX[f"content_question_{qid}"]
            g.add((content_uri, RDF.type, LS.Content))
            g.add((content_uri, LS.text, Literal(question['question_text'])))
            g.add((question_uri, LS.hasContent, content_uri))

        # DATA PROPERTIES (proprietà dirette secondo l'ontologia)
        if question.get('mandatory'):
            # isMandatory è xsd:integer secondo l'ontologia
            mandatory_val = 1 if question['mandatory'] == 'Y' else 0
            g.add((question_uri, LS.isMandatory, Literal(mandatory_val, datatype=XSD.integer)))

        if question.get('encrypted'):
            encrypted_val = 1 if question['encrypted'] == 'Y' else 0
            g.add((question_uri, LS.isEncrypted, Literal(encrypted_val, datatype=XSD.integer)))

        if question.get('scale_id'):
            g.add((question_uri, LS.scaleId, Literal(int(question['scale_id']), datatype=XSD.integer)))

        if question.get('hasAnswerOption'):
            g.add((question_uri, LS.hasAnswerOption, Literal(question['hasAnswerOption'])))

        stats['questions'] += 1

        # === COMPONENT ATTRIBUTES ===
        # Usa hasComponentAttribute per attributi strutturali
        comp_attrs = ['other', 'question_order', 'same_default', 'relevance',
                      'question_theme_name', 'modulename', 'same_script']

        for attr_name in comp_attrs:
            if question.get(attr_name) is not None:
                attr_uri = EX[f"attribute_question_{qid}_{attr_name}"]
                g.add((attr_uri, RDF.type, LS.ComponentAttribute))
                g.add((attr_uri, LS.componentName, Literal(attr_name)))
                g.add((attr_uri, LS.componentValue, Literal(str(question[attr_name]))))
                g.add((question_uri, LS.hasComponentAttribute, attr_uri))

        # === SUBQUESTIONS ===
        subquestions = question.get('subquestions', [])
        if isinstance(subquestions, list):
            for subq in subquestions:
                subq_qid = subq.get('qid')
                if not subq_qid:
                    continue

                # SubQuestion è una classe separata nell'ontologia
                subq_uri = EX[f"subquestion_{subq_qid}"]

                g.add((subq_uri, RDF.type, LS.Subquestion))

                # hasSubquestion collega Question a Subquestion
                g.add((question_uri, LS.hasSubquestion, subq_uri))

                # Identifier
                if subq.get('qid'):
                    id_uri = EX[f"identifier_subquestion_{subq_qid}"]
                    g.add((id_uri, RDF.type, LS.Identifier))
                    g.add((id_uri, LS.id, Literal(int(subq['qid']), datatype=XSD.int)))
                    g.add((subq_uri, LS.hasId, id_uri))

                # Variable
                if subq.get('title'):
                    var_uri = EX[f"variable_{subq['title']}"]
                    g.add((var_uri, RDF.type, LS.Variable))
                    g.add((var_uri, LS.variableCod, Literal(subq['title'])))
                    g.add((subq_uri, LS.hasVariable, var_uri))

                # Name
                if subq.get('title'):
                    name_uri = EX[f"name_subquestion_{subq_qid}"]
                    g.add((name_uri, RDF.type, LS.Name))
                    g.add((name_uri, LS.nameText, Literal(subq['title'])))
                    g.add((subq_uri, LS.hasName, name_uri))

                # Content
                if subq.get('question'):
                    content_uri = EX[f"content_subquestion_{subq_qid}"]
                    g.add((content_uri, RDF.type, LS.Content))
                    g.add((content_uri, LS.text, Literal(subq['question'])))
                    g.add((subq_uri, LS.hasContent, content_uri))

                # Scale ID come ComponentAttribute
                if subq.get('scale_id'):
                    attr_uri = EX[f"attribute_subquestion_{subq_qid}_scale_id"]
                    g.add((attr_uri, RDF.type, LS.ComponentAttribute))
                    g.add((attr_uri, LS.componentName, Literal("scale_id")))
                    g.add((attr_uri, LS.componentValue, Literal(subq['scale_id'])))
                    g.add((subq_uri, LS.hasSubAttribute, attr_uri))

                stats['subquestions'] += 1

        # === ANSWER OPTIONS ===
        answeroption = question.get('AnswerOption', [])
        if isinstance(answeroption, list):
            for ans in answeroption:
                code = ans.get('code')
                if not code:
                    continue

                ans_uri = EX[f"answerOption_{qid}_{code}"]

                g.add((ans_uri, RDF.type, LS.AnswerOption))

                # CORRETTO: Question hasAnswerOption AnswerOption
                g.add((question_uri, LS.hasAnswerOption, ans_uri))

                # componentValue (il code dell'answer)
                if ans.get('code'):
                    g.add((ans_uri, LS.componentValue, Literal(ans['code'])))

                # Content entity per il testo
                if ans.get('answer'):
                    content_uri = EX[f"content_answer_{qid}_{code}"]
                    g.add((content_uri, RDF.type, LS.Content))
                    g.add((content_uri, LS.text, Literal(ans['answer'])))
                    g.add((ans_uri, LS.hasContent, content_uri))

                # DATA PROPERTIES secondo l'ontologia
                if ans.get('order'):
                    g.add((ans_uri, LS.answerOrder, Literal(int(ans['order']), datatype=XSD.integer)))

                if ans.get('assessment_value'):
                    g.add((ans_uri, LS.assessmentValue, Literal(int(ans['assessment_value']), datatype=XSD.integer)))

                if ans.get('scale_id'):
                    g.add((ans_uri, LS.answerScaleId, Literal(int(ans['scale_id']), datatype=XSD.integer)))

                stats['answeroptions'] += 1

        # === ATTRIBUTES (attributes extra dal JSON) ===
        attributes = question.get('attributes', [])
        if isinstance(attributes, list):
            for attr in attributes:
                name = attr.get('name')
                if not name:
                    continue

                attr_uri = EX[f"attribute_question_{qid}_{name}"]

                g.add((attr_uri, RDF.type, LS.ComponentAttribute))
                g.add((attr_uri, LS.componentName, Literal(name)))

                if attr.get('value') is not None:
                    g.add((attr_uri, LS.componentValue, Literal(str(attr['value']))))

                g.add((question_uri, LS.hasComponentAttribute, attr_uri))

                stats['attributes'] += 1

    # Salva il grafo
    print(f"\n💾 Salvataggio in: {output_file}")
    g.serialize(destination=output_file, format='turtle')

    print("\n✅ CONVERSIONE COMPLETATA!")
    print(f"\n📊 Statistiche:")
    print(f"   - Questions: {stats['questions']}")
    print(f"   - SubQuestions: {stats['subquestions']}")
    print(f"   - Answer Options: {stats['answeroption']}")
    print(f"   - Attributes: {stats['attributes']}")
    print(f"   - Totale triple: {len(g)}")

    return g


def main():
    """Main function"""
    print("=" * 60)
    print("🔧 Convertitore JSON → RDF (LimeSurvey Ontology)")
    print("   Conforme a limesurvey.ttl")
    print("=" * 60)
    print()

    # File paths
    JSON_FILE = "questions_normalized.json"
    OUTPUT_FILE = "output.ttl"

    try:
        # Verifica che il file JSON esista
        if not Path(JSON_FILE).exists():
            print(f"❌ File non trovato: {JSON_FILE}")
            print("\nAssicurati di:")
            print("1. Aver normalizzato il JSON con lo script precedente")
            print("2. Essere nella directory corretta")
            return

        # Carica JSON
        data = load_json(JSON_FILE)

        # Converti in RDF
        graph = convert_questions_to_rdf(data, OUTPUT_FILE)

        print(f"\n🎉 File RDF creato: {OUTPUT_FILE}")
        print(f"   Dimensione: {Path(OUTPUT_FILE).stat().st_size / 1024:.2f} KB")

        print("\n📋 Verifica con questa query SPARQL:")
        print("""
PREFIX ls: <https://w3id.org/fossr/ontology/limesurvey/>

# Conta le questions
SELECT (COUNT(?q) as ?total) WHERE {
    ?q a ls:Question .
}

# Lista questions con answer options
SELECT ?q ?title ?answer ?answerText WHERE {
    ?q a ls:Question ;
       ls:hasVariable ?var ;
       ls:hasAnswerOption ?ans .
    ?var ls:variableCod ?title .
    ?ans ls:componentValue ?answer ;
         ls:hasContent ?content .
    ?content ls:text ?answerText .
} LIMIT 10
        """)

    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()