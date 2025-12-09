import json
import os
import sys
import logging
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.weaviate_client import weaviate_manager
from src.config.settings import settings
import weaviate.classes.config as wvc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_data(detailed_path: str, gis_path: str) -> List[Dict[str, Any]]:
    detailed_data = load_json(detailed_path)
    gis_data = load_json(gis_path)
    
    merged_plants = []
    
    # Create a lookup for GIS data
    # GIS data is District -> Plants
    # We want Plant -> Districts
    plant_to_locations = {}
    
    for district, info in gis_data.items():
        lat = info.get('latitude')
        lng = info.get('longitude')
        soils = info.get('soils', [])
        soil_names = [s.get('common_soil_name', 'Unknown') for s in soils]
        
        for plant in info.get('plants', []):
            p_name = plant.get('botanical_name')
            if not p_name:
                continue
                
            # Normalize name (simple lowercase match)
            norm_name = p_name.lower().strip()
            
            if norm_name not in plant_to_locations:
                plant_to_locations[norm_name] = []
                
            plant_to_locations[norm_name].append({
                "district": district,
                "latitude": lat,
                "longitude": lng,
                "soils": ", ".join(soil_names)
            })
            
    # Now iterate through detailed data and attach locations
    for plant in detailed_data:
        bot_name = plant.get('botanical_name', '')
        common_names = plant.get('common_names', [])
        
        # Try to find matches in GIS data
        locations = []
        
        # Check botanical name
        if bot_name.lower().strip() in plant_to_locations:
            locations.extend(plant_to_locations[bot_name.lower().strip()])
            
        # Check common names (less reliable, but useful)
        # (Skipping for now to avoid false positives, botanical name is safer)
        
        # Deduplicate locations
        unique_locs = []
        seen = set()
        for loc in locations:
            key = f"{loc['district']}"
            if key not in seen:
                seen.add(key)
                unique_locs.append(loc)
                
        # Construct unified object
        unified_obj = {
            "plant_name": bot_name,
            "common_names": common_names,
            "description": plant.get('description', {}).get('overview', ''),
            "habitat": plant.get('description', {}).get('habitat', ''),
            "locations": unique_locs,
            # Create a string representation for keyword search
            "search_text": f"{bot_name} {' '.join(common_names)} {plant.get('description', {}).get('overview', '')}"
        }
        merged_plants.append(unified_obj)
        
    return merged_plants

def ingest_data(plants: List[Dict[str, Any]]):
    if not weaviate_manager.client:
        weaviate_manager.connect()
        
    collection_name = settings.GIS_LOCATION_COLLECTION
    
    # Delete existing collection if it exists
    if weaviate_manager.client.collections.exists(collection_name):
        logger.info(f"Deleting existing collection: {collection_name}")
        weaviate_manager.client.collections.delete(collection_name)
        
    # Create new collection
    logger.info(f"Creating collection: {collection_name}")
    weaviate_manager.client.collections.create(
        name=collection_name,
        properties=[
            wvc.Property(name="plant_name", data_type=wvc.DataType.TEXT),
            wvc.Property(name="common_names", data_type=wvc.DataType.TEXT_ARRAY),
            wvc.Property(name="description", data_type=wvc.DataType.TEXT),
            wvc.Property(name="habitat", data_type=wvc.DataType.TEXT),
            wvc.Property(name="search_text", data_type=wvc.DataType.TEXT),
            # We store locations as a JSON string because Weaviate doesn't support list of objects easily in v4 without complex referencing
            # Or we can use object array if supported, but JSON string is safer for simple retrieval
            wvc.Property(name="locations_json", data_type=wvc.DataType.TEXT),
        ]
        # We can add vectorizer config here if needed, but default is usually fine
    )
    
    collection = weaviate_manager.client.collections.get(collection_name)
    
    logger.info(f"Ingesting {len(plants)} plants...")
    
    with collection.batch.dynamic() as batch:
        for p in plants:
            batch.add_object(
                properties={
                    "plant_name": p["plant_name"],
                    "common_names": p["common_names"],
                    "description": p["description"],
                    "habitat": p["habitat"],
                    "search_text": p["search_text"],
                    "locations_json": json.dumps(p["locations"])
                }
            )
            
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    # settings.DATA_DIR might not be defined, use relative path
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
    detailed_path = os.path.join(data_dir, "detailed_info.json")
    gis_path = os.path.join(data_dir, "Gis_info.json")
    
    logger.info("Merging data...")
    merged = merge_data(detailed_path, gis_path)
    logger.info(f"Merged {len(merged)} plants.")
    
    ingest_data(merged)
