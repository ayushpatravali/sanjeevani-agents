from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class IUCNAgent(BaseAgent):
    def __init__(self):
        super().__init__("IUCN_COLLECTION", "IUCNAgent")

    def process_query(self, query: str, limit: int = 5) -> dict:
        hits = self._search(query, limit)
        
        # Validate results against query
        validated_hits, warnings = self._validate_results(hits, query)
        
        plants = []
        for h in validated_hits:
            plant_info = {
                "botanical_name": h.get("botanical_name", "Unknown"),
                "common_names": h.get("common_names", []),
                "iucn_status": h.get("iucn_status", "Not Evaluated"),
                "threat_info": h.get("threat_info", "No specific threats identified")
            }
            plants.append(plant_info)
            
        response = {
            "agent": "IUCNAgent",
            "results": plants,
            "summary": f"{len(plants)} conservation matches",
            "confidence": min(1, len(plants) / limit),
            "warnings": warnings
        }
        
        if warnings:
            logger.warning(f"IUCNAgent warnings: {'; '.join(warnings)}")
            
        return response

    def capabilities(self) -> dict:
        return {
            "domain": "Conservation status and threats",
            "collection": "IUCNAgent",
            "specialties": [
                "IUCN conservation status",
                "Threat assessments", 
                "Endangerment levels",
                "Conservation priorities"
            ]
        }
