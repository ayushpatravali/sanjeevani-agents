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
                # Look for Capitalized words (Common names) or Binomials (Scientific)
                # Matches: "Neem", "Tulsi", "Azadirachta indica", "Hibiscus rosa-sinensis"
                import re
                matches = re.findall(r'\b([A-Z][a-z]+(?: [a-z]+(?:-[a-z]+)?)?)\b', query)
                
                filtered = []
                # Expanded stopwords list to avoid false positives on common sentence starters
                stopwords = {
                    "Where", "What", "When", "How", "Why", "Does", "Is", "Are", "Can", 
                    "Find", "Show", "Give", "Tell", "Location", "Map", "District",
                    "Which", "The", "A", "An", "In", "On", "At", "From", "To", "And", "Or", "But",
                    "Plant", "Tree", "Flower", "Herb", "Shrub", "Weed", "Seed", "Fruit", "Leaf", "Root",
                    "Grown", "Found", "Grow", "Exist", "Live", "Specification", "Specify", "About", "Me"
                }
                for m in matches:
                    # check first word
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
            from weaviate.classes.query import Filter
            
            if not weaviate_manager.client:
                weaviate_manager.connect()
                
            collection = weaviate_manager.client.collections.get(settings.GIS_LOCATION_COLLECTION)
            
            candidates = []
            if plant_names:
                candidates.extend(plant_names)
            else:
                candidates.append(query)
                
            # Clean candidates (Title case usually matches better for plants)
            search_terms = []
            for c in candidates:
                search_terms.append(c.lower())
                search_terms.append(c.title())
            
            search_terms = list(set(search_terms))
            logger.info(f"GISAgent Searching Districts for: {search_terms}")
            
            # The Schema is: District Object -> has 'plants' array
            # We want to find all districts where 'plants' contains our target
            
            results = []
            try:
                # 1. Try Exact Filter (Best for specific plants)
                response = collection.query.fetch_objects(
                    filters=Filter.by_property("plants").contains_any(search_terms),
                    limit=100
                )
                
                if not response.objects:
                    # 2. Fallback to BM25 if filter finds nothing (maybe partial match?)
                    # Searching the 'plants' array for the query string
                    logger.info("Filter found nothing, trying BM25 fallback...")
                    response = collection.query.bm25(
                        query=query,
                        query_properties=["plants"],
                        limit=20
                    )

                for obj in response.objects:
                    props = obj.properties
                    d_name = props.get("district")
                    if d_name:
                        results.append({
                            "district": d_name,
                            "soils": props.get("soils", "Unknown")
                        })
                        
            except Exception as e:
                 logger.error(f"GIS Search Error: {e}")

            if not results:
                summary = f"No specific district data found for '{target_plant}' in the database."
            else:
                district_names = [r['district'] for r in results]
                unique_districts = sorted(list(set(district_names)))
                districts_str = ", ".join(unique_districts)
                if len(unique_districts) > 10:
                    districts_str = ", ".join(unique_districts[:10]) + f" and {len(unique_districts)-10} others"
                    
                summary = f"Found '{target_plant}' in {len(unique_districts)} districts: {districts_str}."

            return {
                "agent": "GISAgent",
                "results": results, # List of {district, soils}
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
