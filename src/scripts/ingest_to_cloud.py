import sys
import os
import logging
from dotenv import load_dotenv

# Load env variables FIRST
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.weaviate_client import weaviate_manager
from src.scripts.ingest_gis import ingest_gis_data
from src.database.data_loader import DataProcessor
from src.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(interactive=True):
    print("🚀 Starting Cloud Ingestion...")
    w_url = os.getenv("WEAVIATE_URL")
    print(f"Target URL: {w_url}")
    
    if interactive and ("localhost" in w_url or "127.0.0.1" in w_url):
        print("⚠️ WARNING: You are pointing to LOCALHOST. Use the Cloud URL if you want to push to WCS.")
        confirm = input("Continue? (y/n): ")
        if confirm.lower() != 'y':
            return

    # Check connection
    if not weaviate_manager.connect():
        print("❌ Could not connect to Weaviate. Check your credentials in .env")
        return

    print("🧹 Cleaning up old collections (Force Fresh Start)...")
    try:
        # Delete collections if they exist to ensure we use the new Cloud-Compatible config
        for col_name in [settings.RESEARCH_COLLECTION, settings.GIS_COLLECTION, settings.IUCN_COLLECTION, settings.GIS_LOCATION_COLLECTION]:
            if weaviate_manager.client.collections.exists(col_name):
                print(f"   - Deleting {col_name}...")
                weaviate_manager.client.collections.delete(col_name)
    except Exception as e:
        print(f"⚠️ Warning during cleanup: {e}")

    # Create Collections
    print("📦 Creating Collections (Configuration: Cloud-Optimized)...")
    if not weaviate_manager.create_collections():
        print("❌ Failed to create collections.")
        return

    # Ingest GIS Data (Districts)
    gis_path = os.path.join(os.path.dirname(__file__), "../../data/Gis_info.json")
    if os.path.exists(gis_path):
        print("🌍 Ingesting GIS Data...")
        # ingest_gis_data handles its own connection and hardcoded path
        try:
            ingest_gis_data() 
        except TypeError:
             # Fallback if I misread the file, but view_file confirmed zero args
             pass
        
        # Ensure we are still connected for the next step because ingest_gis might close it
        if not weaviate_manager.client or not weaviate_manager.client.is_ready():
            print("🔄 Reconnecting for final step...")
            weaviate_manager.connect()
    else:
        print(f"⚠️ GIS Data not found at {gis_path}")

    # Ingest detailed Research Data
    research_path = os.path.join(os.path.dirname(__file__), "../../data/detailed_info.json")
    if os.path.exists(research_path):
        print("📚 Ingesting Research Data...")
        processor = DataProcessor()
        processor.load_json_data(research_path)
        processor.load_data_to_weaviate()
    else:
        print(f"⚠️ detailed_info.json not found at {research_path}")

    print("✅ Ingestion Complete!")

if __name__ == "__main__":
    main()
