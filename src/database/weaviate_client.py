"""Weaviate client connection and setup"""
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from typing import Optional, Dict, Any
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)

class WeaviateManager:
    """Manages Weaviate database connections and operations"""
    def __init__(self):
        self.client: Optional[weaviate.WeaviateClient] = None
        self.collections: Dict[str, Any] = {}

    def connect(self) -> bool:
        try:
            # Check if already connected
            if self.client and self.client.is_ready():
                return True
                
            # Close existing if any (just in case)
            self.close()

            if settings.WEAVIATE_API_KEY:
                self.client = weaviate.connect_to_local(
                    host=settings.WEAVIATE_URL.replace("http://", "").replace("https://", ""),
                    auth_credentials=weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY)
                )
            else:
                self.client = weaviate.connect_to_local()
                
            if self.client.is_ready():
                logger.info("Successfully connected to Weaviate")
                return True
            logger.error("Failed to connect to Weaviate")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            return False

    def close(self):
        """Close the Weaviate connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate connection closed")
            except Exception as e:
                logger.error(f"Error closing Weaviate connection: {e}")
            finally:
                self.client = None

    def create_collections(self) -> bool:
        if not self.client:
            logger.error("No Weaviate connection available")
            return False
        try:
            # Research Agent Collection
            if not self.client.collections.exists(settings.RESEARCH_COLLECTION):
                self.client.collections.create(
                    name=settings.RESEARCH_COLLECTION,
                    properties=[
                        Property(name="plant_id", data_type=DataType.TEXT),
                        Property(name="botanical_name", data_type=DataType.TEXT),
                        Property(name="common_names", data_type=DataType.TEXT_ARRAY),
                        Property(name="family", data_type=DataType.TEXT),
                        Property(name="traditional_uses", data_type=DataType.TEXT_ARRAY),
                        Property(name="major_constituents", data_type=DataType.TEXT_ARRAY),
                        Property(name="pharmacological_activities", data_type=DataType.TEXT),
                        Property(name="modern_applications", data_type=DataType.TEXT_ARRAY),
                        Property(name="safety_info", data_type=DataType.TEXT),
                        Property(name="text_content", data_type=DataType.TEXT),
                    ],
                    vector_config=Configure.Vectorizer.text2vec_transformers()
                )
                logger.info(f"Created {settings.RESEARCH_COLLECTION} collection")
            # GIS Agent Collection
            if not self.client.collections.exists(settings.GIS_COLLECTION):
                self.client.collections.create(
                    name=settings.GIS_COLLECTION,
                    properties=[
                        Property(name="plant_id", data_type=DataType.TEXT),
                        Property(name="botanical_name", data_type=DataType.TEXT),
                        Property(name="common_names", data_type=DataType.TEXT_ARRAY),
                        Property(name="habitat", data_type=DataType.TEXT),
                        Property(name="distribution", data_type=DataType.TEXT),
                        Property(name="text_content", data_type=DataType.TEXT),
                    ],
                    vector_config=Configure.Vectorizer.text2vec_transformers()
                )
                logger.info(f"Created {settings.GIS_COLLECTION} collection")
            # IUCN Agent Collection
            if not self.client.collections.exists(settings.IUCN_COLLECTION):
                self.client.collections.create(
                    name=settings.IUCN_COLLECTION,
                    properties=[
                        Property(name="plant_id", data_type=DataType.TEXT),
                        Property(name="botanical_name", data_type=DataType.TEXT),
                        Property(name="common_names", data_type=DataType.TEXT_ARRAY),
                        Property(name="iucn_status", data_type=DataType.TEXT),
                        Property(name="threat_info", data_type=DataType.TEXT),
                        Property(name="text_content", data_type=DataType.TEXT),
                    ],
                    vector_config=Configure.Vectorizer.text2vec_transformers()
                )
                logger.info(f"Created {settings.IUCN_COLLECTION} collection")
            # GIS Location Collection (New)
            logger.info(f"Checking existence of {settings.GIS_LOCATION_COLLECTION}...")
            if not self.client.collections.exists(settings.GIS_LOCATION_COLLECTION):
                logger.info(f"Creating {settings.GIS_LOCATION_COLLECTION}...")
                self.client.collections.create(
                    name=settings.GIS_LOCATION_COLLECTION,
                    properties=[
                        Property(name="district", data_type=DataType.TEXT),
                        Property(name="location", data_type=DataType.GEO_COORDINATES),
                        Property(name="plants", data_type=DataType.TEXT_ARRAY),
                        Property(name="soils", data_type=DataType.TEXT),
                    ],
                    # No vectorizer needed for pure filter search
                    # vector_config=Configure.Vectorizer.text2vec_transformers() 
                )
                logger.info(f"Created {settings.GIS_LOCATION_COLLECTION} collection")
            else:
                logger.info(f"{settings.GIS_LOCATION_COLLECTION} already exists.")

            # Store collection references using ACTUAL schema names
            self.collections = {
                settings.RESEARCH_COLLECTION: self.client.collections.get(settings.RESEARCH_COLLECTION),
                settings.GIS_COLLECTION: self.client.collections.get(settings.GIS_COLLECTION),
                settings.IUCN_COLLECTION: self.client.collections.get(settings.IUCN_COLLECTION),
                settings.GIS_LOCATION_COLLECTION: self.client.collections.get(settings.GIS_LOCATION_COLLECTION)
            }
            logger.info(f"Collection references stored with keys: {list(self.collections.keys())}")
            return True
        except Exception as e:
            logger.error(f"Error creating collections: {e}")
            return False

    def get_collection(self, collection_name: str):
        return self.collections.get(collection_name)

    def close(self):
        if self.client:
            self.client.close()
            logger.info("Weaviate connection closed")

# Global instance
weaviate_manager = WeaviateManager()
