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

            url = settings.WEAVIATE_URL
            api_key = settings.WEAVIATE_API_KEY

            # Cloud Connection (WCS)
            if "weaviate.cloud" in url or "weaviate.network" in url:
                # Ensure HTTPS
                if not url.startswith("https://"):
                    url = "https://" + url
                
                logger.info(f"Connecting to Weaviate Cloud: {url}")
                # Fix deprecation: connect_to_wcs -> connect_to_weaviate_cloud
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=url,
                    auth_credentials=weaviate.auth.AuthApiKey(api_key),
                    skip_init_checks=True  # Bypass gRPC health check for restrictive networks
                )
            
            # Local Custom Connection (with Auth)
            elif api_key:
                logger.info(f"Connecting to Local Weaviate (Auth): {url}")
                # Clean URL for connect_to_local
                host = url.replace("http://", "").replace("https://", "")
                self.client = weaviate.connect_to_local(
                    host=host,
                    auth_credentials=weaviate.auth.AuthApiKey(api_key)
                )
            
            # Local Anonymous Connection
            else:
                logger.info(f"Connecting to Local Weaviate (Anonymous): {url}")
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
        
        # Determine Vectorizer based on environment
        config_url = settings.WEAVIATE_URL.lower()
        is_cloud = "weaviate.cloud" in config_url or "weaviate.network" in config_url
        
        if is_cloud:
            logger.info("Detected Cloud Environment: Disabling default 'text2vec-transformers'")
            vectorizer_config = Configure.Vectorizer.none()
        else:
            logger.info("Detected Local Environment: Using 'text2vec-transformers'")
            vectorizer_config = Configure.Vectorizer.text2vec_transformers()

        try:
            # Helper for properties to ensure BM25 indexing
            # In v4, index_searchable defaults to True for text, but let's be explicit if getting errors
            from weaviate.classes.config import Property, DataType, Tokenization

            def text_prop(name, is_array=False):
                return Property(
                    name=name, 
                    data_type=DataType.TEXT_ARRAY if is_array else DataType.TEXT,
                    tokenization=Tokenization.WORD,  # Required for efficient BM25
                    index_searchable=True
                )

            # Research Agent Collection
            if not self.client.collections.exists(settings.RESEARCH_COLLECTION):
                self.client.collections.create(
                    name=settings.RESEARCH_COLLECTION,
                    properties=[
                        text_prop("plant_id"),
                        text_prop("botanical_name"),
                        text_prop("common_names", True),
                        text_prop("family"),
                        text_prop("traditional_uses", True),
                        text_prop("major_constituents", True),
                        text_prop("pharmacological_activities"),
                        text_prop("modern_applications", True),
                        text_prop("safety_info"),
                        text_prop("text_content"),
                    ],
                    vectorizer_config=vectorizer_config
                )
                logger.info(f"Created {settings.RESEARCH_COLLECTION} collection")
            # GIS Agent Collection
            if not self.client.collections.exists(settings.GIS_COLLECTION):
                self.client.collections.create(
                    name=settings.GIS_COLLECTION,
                    properties=[
                        text_prop("plant_id"),
                        text_prop("botanical_name"),
                        text_prop("common_names", True),
                        text_prop("habitat"),
                        text_prop("distribution"),
                        text_prop("text_content"),
                    ],
                    vectorizer_config=vectorizer_config
                )
                logger.info(f"Created {settings.GIS_COLLECTION} collection")
            # IUCN Agent Collection
            if not self.client.collections.exists(settings.IUCN_COLLECTION):
                self.client.collections.create(
                    name=settings.IUCN_COLLECTION,
                    properties=[
                        text_prop("plant_id"),
                        text_prop("botanical_name"),
                        text_prop("common_names", True),
                        text_prop("iucn_status"),
                        text_prop("threat_info"),
                        text_prop("text_content"),
                    ],
                    vectorizer_config=vectorizer_config
                )
                logger.info(f"Created {settings.IUCN_COLLECTION} collection")
            # GIS Location Collection (New)
            logger.info(f"Checking existence of {settings.GIS_LOCATION_COLLECTION}...")
            if not self.client.collections.exists(settings.GIS_LOCATION_COLLECTION):
                logger.info(f"Creating {settings.GIS_LOCATION_COLLECTION}...")
                self.client.collections.create(
                    name=settings.GIS_LOCATION_COLLECTION,
                    properties=[
                        text_prop("district"),
                        Property(name="location", data_type=DataType.GEO_COORDINATES),
                        text_prop("plants", True), # Crucial for finding plants!
                        text_prop("soils"),
                    ],
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
