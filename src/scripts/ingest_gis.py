import json
import os
import sys
import logging
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.weaviate_client import weaviate_manager
from src.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_gis_data():
    """Ingest GIS data from JSON to Weaviate"""
    
    # 1. Connect
    if not weaviate_manager.connect():
        logger.error("Failed to connect to Weaviate")
        return
        
    # 2. Create Collections (including new GISLocation)
    if not weaviate_manager.create_collections():
        logger.error("Failed to create collections")
        return
        
    collection = weaviate_manager.client.collections.get(settings.GIS_LOCATION_COLLECTION)
    
    # 3. Load JSON
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "Gis_info.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        return

    # 4. Ingest
    logger.info(f"Ingesting data for {len(data)} districts...")
    
    with collection.batch.dynamic() as batch:
        for district_name, info in data.items():
            try:
                # Extract plants list (combine botanical and common names)
                plants_list = []
                for p in info.get("plants", []):
                    plants_list.append(p.get("botanical_name", ""))
                    plants_list.append(p.get("common_name", ""))
                
                # Clean list
                plants_list = [p for p in plants_list if p]
                
                # Extract soils
                soils_str = ", ".join([s.get("common_soil_name", "") for s in info.get("soils", [])])
                
                # Create object
                obj = {
                    "district": district_name,
                    "location": {
                        "latitude": info.get("latitude"),
                        "longitude": info.get("longitude")
                    },
                    "plants": plants_list,
                    "soils": soils_str
                }
                
                batch.add_object(properties=obj)
                
            except Exception as e:
                logger.error(f"Error processing {district_name}: {e}")
                
    logger.info("Ingestion complete!")
    weaviate_manager.close()

if __name__ == "__main__":
    ingest_gis_data()
