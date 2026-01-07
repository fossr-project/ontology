"""
Semantic Converter Service
Runs as a daemon and provides API endpoints for exporting surveys
"""

import os
import time
import logging
from flask import Flask, request, jsonify
from main import LimeSurveyExporter, RMLtoGraphDBPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app for API endpoints
app = Flask(__name__)

# Configuration from environment
LIMESURVEY_URL = os.getenv('LIMESURVEY_URL', 'http://limesurvey:8080/index.php/admin/remotecontrol')
LIMESURVEY_USERNAME = os.getenv('LIMESURVEY_USERNAME', 'admin')
LIMESURVEY_PASSWORD = os.getenv('LIMESURVEY_PASSWORD', 'admin')

GRAPHDB_URL = os.getenv('GRAPHDB_URL', 'http://graphdb:7200')
GRAPHDB_USERNAME = os.getenv('GRAPHDB_USERNAME', 'admin')
GRAPHDB_PASSWORD = os.getenv('GRAPHDB_PASSWORD', 'admin')
GRAPHDB_REPOSITORY = os.getenv('GRAPHDB_REPOSITORY', 'test_repo')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'semantic-converter',
        'timestamp': time.time()
    })


@app.route('/api/export/survey/<int:survey_id>', methods=['POST'])
def export_survey(survey_id):
    """
    Export a survey from LimeSurvey and convert to RDF
    """
    try:
        logger.info(f"Starting export for survey {survey_id}")
        
        # Initialize exporter
        exporter = LimeSurveyExporter(
            url=LIMESURVEY_URL,
            username=LIMESURVEY_USERNAME,
            password=LIMESURVEY_PASSWORD,
            output_dir='exports'
        )
        
        # Export data
        logger.info("Exporting survey properties...")
        exporter.export_all_question_properties_survey(survey_id)
        
        logger.info("Exporting groups...")
        exporter.export_groups(survey_id)
        
        logger.info("Exporting questions...")
        exporter.export_questions(survey_id)
        
        # Initialize pipeline
        pipeline = RMLtoGraphDBPipeline(
            graphdb_url=GRAPHDB_URL,
            username=GRAPHDB_USERNAME,
            password=GRAPHDB_PASSWORD
        )
        
        # Convert and upload groups
        logger.info("Converting and uploading groups...")
        pipeline.process_and_upload(
            rml_file="rml/RMLGroup2.ttl",
            repo_id=GRAPHDB_REPOSITORY,
            context=f"http://example.org/survey/{survey_id}/groups",
            save_local=True,
            output_file=f"output/groups_{survey_id}.ttl"
        )
        
        # Convert and upload questions
        logger.info("Converting and uploading questions...")
        pipeline.process_and_upload(
            rml_file="rml/RMLQuestion.ttl",
            repo_id=GRAPHDB_REPOSITORY,
            context=f"http://example.org/survey/{survey_id}/questions",
            save_local=True,
            output_file=f"output/questions_{survey_id}.ttl"
        )
        
        logger.info(f"✅ Survey {survey_id} exported successfully")
        
        return jsonify({
            'status': 'success',
            'survey_id': survey_id,
            'message': f'Survey {survey_id} exported and converted to RDF'
        })
        
    except Exception as e:
        logger.error(f"Error exporting survey {survey_id}: {e}")
        return jsonify({
            'status': 'error',
            'survey_id': survey_id,
            'message': str(e)
        }), 500


@app.route('/api/list/surveys', methods=['GET'])
def list_surveys():
    """List all surveys from LimeSurvey"""
    try:
        exporter = LimeSurveyExporter(
            url=LIMESURVEY_URL,
            username=LIMESURVEY_USERNAME,
            password=LIMESURVEY_PASSWORD
        )
        
        # This would need to be implemented in the exporter
        # For now, return a simple response
        return jsonify({
            'status': 'success',
            'message': 'Use LimeSurvey API directly to list surveys'
        })
        
    except Exception as e:
        logger.error(f"Error listing surveys: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Wait for dependencies to be ready
    logger.info("Waiting for LimeSurvey and GraphDB to be ready...")
    time.sleep(30)
    
    logger.info("🚀 Starting Semantic Converter Service")
    logger.info(f"LimeSurvey URL: {LIMESURVEY_URL}")
    logger.info(f"GraphDB URL: {GRAPHDB_URL}")
    logger.info(f"GraphDB Repository: {GRAPHDB_REPOSITORY}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False
    )