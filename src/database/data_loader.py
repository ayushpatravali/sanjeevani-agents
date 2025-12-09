"""Data loading and processing for Weaviate"""
import json
import logging
from typing import List, Dict, Any
from ..database.weaviate_client import weaviate_manager
from ..config.settings import settings

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.plants_data: List[Dict[str, Any]] = []

    def load_json_data(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.plants_data = json.load(f)
            logger.info(f"Loaded {len(self.plants_data)} plants from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
            return False

    def create_research_documents(self) -> List[Dict[str, Any]]:
        documents = []
        for plant in self.plants_data:
            traditional_uses_text = "; ".join([
                f"{use.get('use', '')} - {use.get('context', '')}"
                for use in plant.get('traditional_uses', [])
            ])
            pharmacological_text = "; ".join([
                f"{activity.get('name', '')}: {activity.get('mechanism', '')} (Evidence: {activity.get('evidence', '')})"
                for activity in plant.get('pharmacological_activities', [])
            ])
            text_content = f"""
Plant: {plant.get('botanical_name', '')} ({', '.join(plant.get('common_names', []))})
Family: {plant.get('family', 'Unknown')}
Traditional Uses: {traditional_uses_text}
Major Constituents: {', '.join(plant.get('major_constituents', []))}
Pharmacological Activities: {pharmacological_text}
Modern Applications: {'; '.join(plant.get('modern_applications', []))}
Safety Information: {plant.get('safety', {}).get('acute_toxicity', 'Not specified')}
            """.strip()
            doc = {
                "plant_id": plant.get("id", ""),
                "botanical_name": plant.get("botanical_name", ""),
                "common_names": plant.get("common_names", []),
                "family": plant.get("family", "Unknown"),
                "traditional_uses": [f"{use.get('use', '')}: {use.get('context', '')}" for use in plant.get('traditional_uses', [])],
                "major_constituents": plant.get("major_constituents", []),
                "pharmacological_activities": pharmacological_text,
                "modern_applications": plant.get("modern_applications", []),
                "safety_info": plant.get('safety', {}).get('acute_toxicity', 'Not specified'),
                "text_content": text_content
            }
            documents.append(doc)
        return documents

    def create_gis_documents(self) -> List[Dict[str, Any]]:
        documents = []
        for plant in self.plants_data:
            description = plant.get('description', {})
            text_content = f"""
Plant: {plant.get('botanical_name', '')} ({', '.join(plant.get('common_names', []))})
Habitat: {description.get('habitat', 'Not specified')}
Distribution: Based on habitat description - {description.get('habitat', 'Not specified')}
Overview: {description.get('overview', 'Not specified')}
            """.strip()
            doc = {
                "plant_id": plant.get("id", ""),
                "botanical_name": plant.get("botanical_name", ""),
                "common_names": plant.get("common_names", []),
                "habitat": description.get('habitat', 'Not specified'),
                "distribution": description.get('habitat', 'Not specified'),
                "text_content": text_content
            }
            documents.append(doc)
        return documents

    def create_iucn_documents(self) -> List[Dict[str, Any]]:
        documents = []
        for plant in self.plants_data:
            iucn_info = plant.get('iucn_status', {})
            text_content = f"""
Plant: {plant.get('botanical_name', '')} ({', '.join(plant.get('common_names', []))})
IUCN Status: {iucn_info.get('status', 'Not Evaluated')}
Conservation Information: {iucn_info.get('status', 'Not Evaluated')}
            """.strip()
            doc = {
                "plant_id": plant.get("id", ""),
                "botanical_name": plant.get("botanical_name", ""),
                "common_names": plant.get("common_names", []),
                "iucn_status": iucn_info.get('status', 'Not Evaluated'),
                "threat_info": iucn_info.get('status', 'Not Evaluated'),
                "text_content": text_content
            }
            documents.append(doc)
        return documents

    def load_data_to_weaviate(self) -> bool:
        try:
            research_docs = self.create_research_documents()
            gis_docs = self.create_gis_documents()
            iucn_docs = self.create_iucn_documents()

            # Force refresh collection handles
            weaviate_manager.collections[settings.RESEARCH_COLLECTION] = weaviate_manager.client.collections.get(settings.RESEARCH_COLLECTION)
            weaviate_manager.collections[settings.GIS_COLLECTION] = weaviate_manager.client.collections.get(settings.GIS_COLLECTION)
            weaviate_manager.collections[settings.IUCN_COLLECTION] = weaviate_manager.client.collections.get(settings.IUCN_COLLECTION)

            research_collection = weaviate_manager.get_collection(settings.RESEARCH_COLLECTION)
            gis_collection = weaviate_manager.get_collection(settings.GIS_COLLECTION)
            iucn_collection = weaviate_manager.get_collection(settings.IUCN_COLLECTION)

            logger.info(f"Live collection handles after refresh: {research_collection}, {gis_collection}, {iucn_collection}")

           
            if research_collection is None or gis_collection is None or iucn_collection is None:
                logger.error(f"One or more collections is None. Found: {weaviate_manager.collections.keys()}")
                return False

            with research_collection.batch.dynamic() as batch:
                for doc in research_docs:
                    batch.add_object(properties=doc)
            logger.info(f"Loaded {len(research_docs)} documents to Research collection")

            with gis_collection.batch.dynamic() as batch:
                for doc in gis_docs:
                    batch.add_object(properties=doc)
            logger.info(f"Loaded {len(gis_docs)} documents to GIS collection")

            with iucn_collection.batch.dynamic() as batch:
                for doc in iucn_docs:
                    batch.add_object(properties=doc)
            logger.info(f"Loaded {len(iucn_docs)} documents to IUCN collection")

            return True

        except Exception as e:
            logger.error(f"Error loading data to Weaviate: {e}")
            return False

# Global instance
data_processor = DataProcessor()
