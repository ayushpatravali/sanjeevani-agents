import sys
import os
import logging
from dotenv import load_dotenv

# Load env variables FIRST
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.weaviate_client import weaviate_manager
from src.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("☁️ Testing Cloud Connection & Data...")
    
    if not weaviate_manager.connect():
        print("❌ Connect failed.")
        return

    print("✅ Connected!")
    
    collections = [settings.RESEARCH_COLLECTION, settings.GIS_COLLECTION, settings.IUCN_COLLECTION, settings.GIS_LOCATION_COLLECTION]
    
    for name in collections:
        if weaviate_manager.client.collections.exists(name):
            col = weaviate_manager.client.collections.get(name)
            # Count objects (approximate or iterate)
            # In v4, we use aggregate.over_all(total_count=True)
            try:
                count = col.aggregate.over_all(total_count=True).total_count
                print(f"📦 Collection '{name}': {count} objects")
            except Exception as e:
                print(f"⚠️ Could not count '{name}': {e}")
        else:
            print(f"❌ Collection '{name}' DOES NOT EXIST.")

if __name__ == "__main__":
    main()
