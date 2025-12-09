"""Configuration settings for Sanjeevani Agents"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # Weaviate Configuration
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Collection Names
    RESEARCH_COLLECTION = "ResearchAgent"
    GIS_COLLECTION = "GISAgent" 
    GIS_LOCATION_COLLECTION = "GISLocation"
    IUCN_COLLECTION = "IUCNAgent"
    
    # Data Processing
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Agent Configuration
    AGENT_CONFIG: Dict[str, Any] = {
        "research": {
            "collection": RESEARCH_COLLECTION,
            "description": "Handles medicinal properties, traditional uses, and pharmacological activities"
        },
        "gis": {
            "collection": GIS_COLLECTION,
            "description": "Handles geographical distribution, habitat, and location data"
        },
        "iucn": {
            "collection": IUCN_COLLECTION,
            "description": "Handles conservation status, threats, and IUCN classifications"
        }
    }

settings = Settings()
