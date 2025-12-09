from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("RESEARCH_COLLECTION", "ResearchAgent")

    def process_query(self, query: str, limit: int = 5) -> dict:
        hits = self._search(query, limit)
        
        # Validate results against query
        validated_hits, warnings = self._validate_results(hits, query)
        
        plants = []
        for h in validated_hits:
            # Truncate long fields
            pharm = h.get("pharmacological_activities", "")
            if len(pharm) > 500: pharm = pharm[:500] + "..."
            
            uses = h.get("traditional_uses", [])
            if isinstance(uses, list):
                uses = [u[:100] + "..." if len(u) > 100 else u for u in uses]
            
            plant_info = {
                "botanical_name": h.get("botanical_name", "Unknown"),
                "common_names": h.get("common_names", []),
                "traditional_uses": uses,
                "pharmacology": pharm,
                "major_constituents": h.get("major_constituents", []),
                "safety_info": h.get("safety_info", "Not specified")
            }
            plants.append(plant_info)
        
        response = {
            "agent": "ResearchAgent",
            "results": plants,
            "summary": f"{len(plants)} medicinal matches",
            "confidence": min(1, len(plants) / limit),
            "warnings": warnings
        }
        
        if warnings:
            logger.warning(f"ResearchAgent warnings: {'; '.join(warnings)}")
            
        return response

    def capabilities(self) -> dict:
        return {
            "domain": "Medicinal / traditional uses",
            "collection": "ResearchAgent",
            "specialties": [
                "Traditional medicinal uses",
                "Pharmacological activities", 
                "Chemical constituents",
                "Modern applications",
                "Safety information"
            ]
        }
