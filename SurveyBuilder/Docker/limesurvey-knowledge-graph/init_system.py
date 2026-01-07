"""
System Initialization Script
Runs once to setup GraphDB repository and load ontology
"""

import os
import sys
import time
import logging
from main import GraphDBManager, RMLtoGraphDBPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
GRAPHDB_URL = os.getenv('GRAPHDB_URL', 'http://graphdb:7200')
GRAPHDB_USERNAME = os.getenv('GRAPHDB_USERNAME', 'admin')
GRAPHDB_PASSWORD = os.getenv('GRAPHDB_PASSWORD', 'admin')
GRAPHDB_REPOSITORY = os.getenv('GRAPHDB_REPOSITORY', 'test_repo')

LIMESURVEY_URL = os.getenv('LIMESURVEY_URL')
LIMESURVEY_USERNAME = os.getenv('LIMESURVEY_USERNAME')
LIMESURVEY_PASSWORD = os.getenv('LIMESURVEY_PASSWORD')


def wait_for_graphdb(max_retries=30, delay=10):
    """Wait for GraphDB to be ready"""
    import requests
    
    logger.info(f"Waiting for GraphDB at {GRAPHDB_URL}...")
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{GRAPHDB_URL}/rest/repositories", timeout=5)
            if response.status_code == 200:
                logger.info("✅ GraphDB is ready!")
                return True
        except Exception as e:
            logger.info(f"Attempt {i+1}/{max_retries}: GraphDB not ready yet... ({e})")
        
        time.sleep(delay)
    
    logger.error("❌ GraphDB did not become ready in time")
    return False


def wait_for_limesurvey(max_retries=30, delay=10):
    """Wait for LimeSurvey to be ready"""
    import requests
    
    logger.info(f"Waiting for LimeSurvey at {LIMESURVEY_URL}...")
    
    # Extract base URL
    base_url = LIMESURVEY_URL.replace('/index.php/admin/remotecontrol', '')
    
    for i in range(max_retries):
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                logger.info("✅ LimeSurvey is ready!")
                return True
        except Exception as e:
            logger.info(f"Attempt {i+1}/{max_retries}: LimeSurvey not ready yet... ({e})")
        
        time.sleep(delay)
    
    logger.error("❌ LimeSurvey did not become ready in time")
    return False


def setup_graphdb():
    """Initialize GraphDB repository and load ontology"""
    try:
        logger.info("=" * 70)
        logger.info("INITIALIZING GRAPHDB REPOSITORY")
        logger.info("=" * 70)
        
        # Initialize GraphDB manager
        graphdb = GraphDBManager(
            base_url=GRAPHDB_URL,
            username=GRAPHDB_USERNAME,
            password=GRAPHDB_PASSWORD
        )
        
        # List existing repositories
        logger.info("\n📦 Checking existing repositories...")
        repos = graphdb.list_repositories()
        
        # Check if repository exists
        repo_exists = any(repo['id'] == GRAPHDB_REPOSITORY for repo in repos)
        
        if repo_exists:
            logger.info(f"⚠️  Repository '{GRAPHDB_REPOSITORY}' already exists")
            logger.info("Skipping creation (delete manually if you want to recreate)")
        else:
            # Create repository
            logger.info(f"\n🔨 Creating repository: {GRAPHDB_REPOSITORY}")
            success = graphdb.create_repository(
                repo_id=GRAPHDB_REPOSITORY,
                repo_title="LimeSurvey Knowledge Graph",
                ruleset="empty"
            )
            
            if not success:
                logger.error("❌ Failed to create repository")
                return False
            
            logger.info("✅ Repository created successfully")
        
        # Load ontology
        logger.info("\n📚 Loading LimeSurvey ontology...")
        ontology_path = "/app/ontology/limesurvey.ttl"
        
        if not os.path.exists(ontology_path):
            logger.error(f"❌ Ontology file not found: {ontology_path}")
            return False
        
        success = graphdb.upload_file(
            repo_id=GRAPHDB_REPOSITORY,
            file_path=ontology_path,
            context="http://example.org/ontology"
        )
        
        if not success:
            logger.error("❌ Failed to load ontology")
            return False
        
        logger.info("✅ Ontology loaded successfully")
        
        # Verify
        logger.info("\n🔍 Verifying repository...")
        query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
        result = graphdb.execute_sparql_query(GRAPHDB_REPOSITORY, query)
        
        if result:
            count = result['results']['bindings'][0]['count']['value']
            logger.info(f"✅ Repository contains {count} triples")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ GRAPHDB INITIALIZATION COMPLETE")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during GraphDB setup: {e}")
        import traceback
        traceback.print_exc()
        return False


def import_sample_data():
    """Import sample surveys if available"""
    try:
        logger.info("\n" + "=" * 70)
        logger.info("IMPORTING SAMPLE DATA (OPTIONAL)")
        logger.info("=" * 70)
        
        samples_dir = "/app/samples"
        
        if not os.path.exists(samples_dir):
            logger.info("⚠️  No samples directory found, skipping sample import")
            return True
        
        # Check for CSV files
        csv_files = [f for f in os.listdir(samples_dir) if f.endswith('.csv')]
        
        if not csv_files:
            logger.info("⚠️  No CSV files found in samples directory")
            return True
        
        logger.info(f"📁 Found {len(csv_files)} sample files")
        
        # Initialize pipeline
        pipeline = RMLtoGraphDBPipeline(
            graphdb_url=GRAPHDB_URL,
            username=GRAPHDB_USERNAME,
            password=GRAPHDB_PASSWORD
        )
        
        # Import groups
        groups_csv = [f for f in csv_files if 'group' in f.lower()]
        if groups_csv:
            logger.info(f"\n📊 Importing groups from {groups_csv[0]}...")
            # You would need to update RML file to point to this CSV
            # For now, just log
            logger.info("⚠️  Manual RML mapping configuration required")
        
        # Import questions
        questions_csv = [f for f in csv_files if 'question' in f.lower()]
        if questions_csv:
            logger.info(f"\n❓ Importing questions from {questions_csv[0]}...")
            logger.info("⚠️  Manual RML mapping configuration required")
        
        logger.info("\n💡 To import sample data:")
        logger.info("   1. Update RML mappings to point to sample CSV files")
        logger.info("   2. Run the Semantic Converter manually")
        logger.info("   3. Or import surveys directly from LimeSurvey")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error importing sample data: {e}")
        return False


def main():
    """Main initialization routine"""
    logger.info("\n" + "=" * 70)
    logger.info("🚀 LIMESURVEY KNOWLEDGE GRAPH - SYSTEM INITIALIZATION")
    logger.info("=" * 70 + "\n")
    
    # Wait for services
    if not wait_for_graphdb():
        logger.error("❌ GraphDB not available, exiting")
        sys.exit(1)
    
    if not wait_for_limesurvey():
        logger.error("❌ LimeSurvey not available, exiting")
        sys.exit(1)
    
    # Additional delay to ensure services are fully ready
    logger.info("\n⏳ Waiting 10 seconds for services to stabilize...")
    time.sleep(10)
    
    # Setup GraphDB
    if not setup_graphdb():
        logger.error("❌ GraphDB setup failed")
        sys.exit(1)
    
    # Import sample data (optional)
    import_sample_data()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ SYSTEM INITIALIZATION COMPLETE")
    logger.info("=" * 70)
    logger.info("\n📍 Access Points:")
    logger.info(f"   - LimeSurvey:      http://localhost:8080")
    logger.info(f"   - GraphDB:         http://localhost:7200")
    logger.info(f"   - Survey Builder:  http://localhost:5005")
    logger.info("\n🔑 Default Credentials:")
    logger.info(f"   - LimeSurvey:  admin / admin")
    logger.info(f"   - GraphDB:     admin / admin")
    logger.info("\n🎉 System is ready to use!")
    logger.info("=" * 70 + "\n")
    
    # Exit successfully (this is a one-time init container)
    sys.exit(0)


if __name__ == '__main__':
    main()