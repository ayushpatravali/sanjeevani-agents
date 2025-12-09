from typing import Dict, Any
from .base_agent import BaseAgent
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class GISAgent(BaseAgent):
    def __init__(self):
        super().__init__("GIS_COLLECTION", "GISAgent")

    def process_query(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Process query using Weaviate GISLocation collection.
        Returns list of districts where plant is found.
        """
        try:
            plant_names = self._extract_plant_names(query)
            
            # If BaseAgent failed, try local regex for botanical names
            if not plant_names:
                import re
                # Look for Capitalized word followed by lowercase word (e.g. Amaranthus viridis)
                # Also support hyphenated species names like "Hibiscus rosa-sinensis"
                matches = re.findall(r'\b([A-Z][a-z]+ [a-z]+(?:-[a-z]+)?)\b', query)
                filtered = []
                stopwords = {"Where", "What", "When", "How", "Why", "Does", "Is", "Are", "Can", "Find", "Show", "Give", "Tell", "Location", "Map", "District"}
                for m in matches:
                    first_word = m.split()[0]
                    if first_word not in stopwords:
                        filtered.append(m)
                if filtered:
                    plant_names = filtered
            
            print(f"GISAgent Extracted Plants: {plant_names}", flush=True)
            
            target_plant = plant_names[0] if plant_names else query
            logger.info(f"GISAgent Target Plant: {target_plant}")
            
            # Query the unified GISLocation collection
            # Use weaviate_manager directly as BaseAgent doesn't expose self.client
            from src.database.weaviate_client import weaviate_manager
            import json
            
            if not weaviate_manager.client:
                weaviate_manager.connect()
                
            collection = weaviate_manager.client.collections.get(settings.GIS_LOCATION_COLLECTION)
            
            # Cascading Search Strategy
            search_candidates = []
            if plant_names:
                search_candidates.extend(plant_names)
            
            # Add regex matches as fallback candidates
            import re
            matches = re.findall(r'\b([A-Z][a-z]+ [a-z]+(?:-[a-z]+)?)\b', query)
            stopwords = {"Where", "What", "When", "How", "Why", "Does", "Is", "Are", "Can", "Find", "Show", "Give", "Tell", "Location", "Map", "District"}
            for m in matches:
                if m.split()[0] not in stopwords and m not in search_candidates:
                    search_candidates.append(m)
            
            # Add raw query words (excluding stopwords) if nothing else
            if not search_candidates:
                words = [w for w in query.split() if w not in stopwords]
                search_candidates.append(" ".join(words))

            logger.info(f"GISAgent Search Candidates: {search_candidates}")
            
            response = None
            for candidate in search_candidates:
                logger.info(f"GISAgent querying BM25 for: {candidate}")
                try:
                    resp = collection.query.bm25(
                        query=candidate,
                        query_properties=["plant_name", "common_names"],
                        limit=5
                    )
                    if resp and resp.objects:
                        response = resp
                        logger.info(f"Found {len(resp.objects)} results for {candidate}")
                        break # Stop if found
                except Exception as e:
                    logger.error(f"GIS BM25 search failed for {candidate}: {e}")
            
            results = []
            habitat_info = ""
            
            if response and response.objects:
                # Take the best match
                obj = response.objects[0]
                props = obj.properties
                
                # Get habitat info
                habitat_info = props.get("habitat", "")
                
                # Parse locations
                loc_json = props.get("locations_json", "[]")
                try:
                    locations = json.loads(loc_json)
                    for loc in locations:
                        results.append({
                            "district": loc.get("district"),
                            "latitude": loc.get("latitude"),
                            "longitude": loc.get("longitude"),
                            "soils": loc.get("soils")
                        })
                except:
                    logger.warning("Failed to parse locations_json")
            
            if not results:
                summary = f"No specific district location data found for {target_plant} in the Karnataka GIS database. Habitat: {habitat_info}"
            else:
                district_names = [r['district'] for r in results if r.get('district')]
                unique_districts = sorted(list(set(district_names)))
                districts_str = ", ".join(unique_districts)
                summary = f"Found in {len(unique_districts)} districts in Karnataka: {districts_str}. Habitat: {habitat_info}"

            return {
                "agent": "GISAgent",
                "results": results,
                "habitat": habitat_info,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"GIS query failed CRITICALLY: {e}")
            return {"error": str(e), "results": [], "summary": "GIS Search failed due to internal error."}

    def _standard_search(self, query: str, limit: int) -> Dict[str, Any]:
        """Fallback to original text-based search"""
        hits = self._search(query, limit)
        validated_hits, warnings = self._validate_results(hits, query)
        return {
            "agent": "GISAgent",
            "results": validated_hits,
            "summary": f"{len(validated_hits)} geographical matches",
            "warnings": warnings
        }

    def capabilities(self) -> dict:
        return {
            "domain": "Geographical distribution and habitat",
            "collection": "GISAgent", 
            "specialties": [
                "Natural habitat information",
                "Geographic distribution",
                "Growing conditions",
                "Regional availability"
            ]
        }
