"""
Parent class: handles Weaviate connection & semantic search with plant name awareness.
"""
from abc import ABC, abstractmethod
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from src.database.weaviate_client import weaviate_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, collection_env_key: str, name: str):
        self.collection_env_key = collection_env_key
        self.name = name
        self.collection = None
        
        # Common plant name patterns for extraction
        self.plant_name_patterns = [
            r'\b([A-Z][a-z]+ [a-z]+)\b',  # Botanical names like "Ocimum sanctum"
            r'\btulsi\b', r'\bneem\b', r'\bturmeric\b', r'\bashwagandha\b',
            r'\bmoringa\b', r'\bgalangal\b', r'\bkaronda\b', r'\bjasmine\b',
            r'\bashoka\b', r'\bkalmegh\b', r'\bchiretta\b'
        ]

    # ---------- private helpers ----------
    def _connect(self) -> bool:
        """Ensure connection to Weaviate and set the collection handle."""
        # Robust connection check
        try:
            if not weaviate_manager.client or not weaviate_manager.client.is_ready():
                 if not weaviate_manager.connect():
                     return False
        except Exception as e:
            logger.warning(f"Health check failed ({e}), forcing reconnection...")
            if not weaviate_manager.connect():
                return False
        
        self.collection = weaviate_manager.client.collections.get(
            getattr(settings, self.collection_env_key)
        )
        return bool(self.collection)
    
    def close(self):
        """Close Weaviate connection."""
        if weaviate_manager.client:
            weaviate_manager.client.close()

    def _extract_plant_names(self, query: str) -> List[str]:
        """Extract potential plant names from the query with fuzzy matching."""
        from rapidfuzz import process, fuzz
        
        query_lower = query.lower()
        found_names = []
        
        # Check for common names
        common_name_map = {
            'tulsi': ['tulsi', 'holy basil', 'ocimum sanctum'],
            'neem': ['neem', 'azadirachta indica'],
            'turmeric': ['turmeric', 'curcuma longa'],
            'ashwagandha': ['ashwagandha', 'withania somnifera'],
            'moringa': ['moringa', 'drumstick tree', 'moringa oleifera'],
            'galangal': ['galangal', 'greater galangal', 'alpinia galanga'],
            'karonda': ['karonda', 'christ\'s thorn', 'carissa carandas'],
            'jasmine': ['jasmine', 'jasminum'],
            'ashoka': ['ashoka', 'saraca asoca'],
            'kalmegh': ['kalmegh', 'green chiretta', 'andrographis paniculata']
        }
        
        # 1. Exact checks
        for key, variants in common_name_map.items():
            if any(variant in query_lower for variant in variants):
                found_names.extend(variants)
        
        # 2. Fuzzy checks (if no exact matches found or to augment)
        # Split query into words to check against keys
        words = query_lower.split()
        stopwords = {'tell', 'about', 'what', 'where', 'when', 'which', 'this', 'that', 'plant', 'herb', 'tree', 'grow', 'find', 'benefits', 'uses', 'today', 'raining'}
        
        for word in words:
            # Skip very short words and stopwords
            if len(word) < 4 or word in stopwords: continue
            
            # Check against keys
            match = process.extractOne(word, common_name_map.keys(), scorer=fuzz.ratio)
            if match and match[1] > 79: # Lowered threshold to 79% to catch 'tusli' (80%)
                matched_key = match[0]



                # Only add if not already found
                if matched_key not in [n for n in found_names]:
                    found_names.extend(common_name_map[matched_key])




        # Extract potential botanical names (Genus species pattern)
        # Removed broad regex to prevent false positives like "Is it"
        # botanical_matches = re.findall(r'\b([A-Z][a-z]+ [a-z]+)\b', query)
        # found_names.extend([match.lower() for match in botanical_matches])
        
        return list(set(found_names))  # Remove duplicates


    def _search_with_plant_filter(self, query: str, plant_names: List[str], limit: int = 5) -> List[Dict]:
        """Search with plant name filtering when specific plants are mentioned."""
        if not self.collection and not self._connect():
            logger.error(f"{self.name}: No Weaviate collection available for search.")
            return []

        try:
            # First, try exact botanical name matches
            exact_matches = []
            for plant_name in plant_names:
                try:
                    botanical_results = self.collection.query.near_text(
                        query=query,
                        where={
                            "path": ["botanical_name"],
                            "operator": "Like",
                            "valueText": f"*{plant_name}*"
                        },
                        limit=limit
                    )
                    exact_matches.extend([hit.properties for hit in botanical_results.objects])
                except Exception as e:
                    # Retry once on connection error
                    logger.warning(f"Botanical filter failed ({e}). Retrying after reconnect...")
                    if self._connect():
                         try:
                             botanical_results = self.collection.query.near_text(
                                query=query,
                                where={
                                    "path": ["botanical_name"],
                                    "operator": "Like",
                                    "valueText": f"*{plant_name}*"
                                },
                                limit=limit
                            )
                             exact_matches.extend([hit.properties for hit in botanical_results.objects])
                         except: pass

            # If we have exact matches, return those
            if exact_matches:
                return exact_matches[:limit]

            # Try common names filter
            common_matches = []
            for plant_name in plant_names:
                try:
                    common_results = self.collection.query.near_text(
                        query=query,
                        where={
                            "path": ["common_names"],
                            "operator": "ContainsAny",
                            "valueTextArray": [plant_name.title(), plant_name.lower(), plant_name.upper()]
                        },
                        limit=limit
                    )
                    common_matches.extend([hit.properties for hit in common_results.objects])
                except Exception as e:
                    logger.debug(f"Common name filter failed for {plant_name}: {e}")

            if common_matches:
                return common_matches[:limit]

            # Fallback: semantic search but validate results contain the plant names
            semantic_results = self.collection.query.near_text(query=query, limit=limit * 2)
            validated_results = []
            
            for hit in semantic_results.objects:
                props = hit.properties
                botanical_name = props.get('botanical_name', '').lower()
                common_names = [name.lower() for name in props.get('common_names', [])]
                text_content = props.get('text_content', '').lower()
                
                # Check if any of the extracted plant names appear in this result
                for plant_name in plant_names:
                    if (plant_name in botanical_name or 
                        any(plant_name in common for common in common_names) or
                        plant_name in text_content):
                        validated_results.append(props)
                        break
                
                if len(validated_results) >= limit:
                    break
                    
            return validated_results

        except Exception as e:
            logger.error(f"{self.name} filtered search failed: {e}")
            return []

    def _search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Enhanced search that combines plant name detection with semantic search.
        """
        if not self.collection and not self._connect():
            logger.error(f"{self.name}: No Weaviate collection available for search.")
            return []

        # Extract potential plant names from query
        plant_names = self._extract_plant_names(query)
        
        if plant_names:
            logger.info(f"{self.name}: Detected plant names in query: {plant_names}")
            # Use filtered search when plant names are detected
            results = self._search_with_plant_filter(query, plant_names, limit)
            if results:
                return results
            else:
                logger.warning(f"{self.name}: No results found for specified plants, falling back to semantic search")

        # Fallback to pure semantic search
        try:
            results = self.collection.query.near_text(query=query, limit=limit)
            return [hit.properties for hit in results.objects]
        except Exception as e:
            logger.warning(f"{self.name} semantic search failed: {e}. Attempting Reconnect...")
            if self._connect():
                try:
                    results = self.collection.query.near_text(query=query, limit=limit)
                    return [hit.properties for hit in results.objects]
                except: pass
            
            logger.warning("Retrying with BM25...")
            try:
                # BM25 Fallback for environments without vectorizer
                results = self.collection.query.bm25(query=query, limit=limit)
                return [hit.properties for hit in results.objects]
            except Exception as e2:
                logger.error(f"{self.name} BM25 fallback also failed: {e2}")
                return []

    def _validate_results(self, results: List[Dict], query: str) -> Tuple[List[Dict], List[str]]:
        """Validate if results match the queried plant names and provide warnings."""
        plant_names = self._extract_plant_names(query)
        if not plant_names:
            return results, []  # No validation needed if no specific plant mentioned
        
        validated_results = []
        warnings = []
        
        for result in results:
            botanical_name = result.get('botanical_name', '').lower()
            common_names = [name.lower() for name in result.get('common_names', [])]
            
            # Check if result matches any of the queried plant names
            matches_query = False
            for plant_name in plant_names:
                if (plant_name in botanical_name or 
                    any(plant_name in common for common in common_names)):
                    matches_query = True
                    break
            
            if matches_query:
                validated_results.append(result)
            else:
                warnings.append(f"Found information about {result.get('botanical_name', 'Unknown')} instead of requested plant")
        
        if not validated_results and results:
            warnings.append(f"No direct matches found for '{', '.join(plant_names)}'. Showing semantically similar plants.")
            return results, warnings
            
        return validated_results if validated_results else results, warnings

    # ---------- public API ----------
    @abstractmethod
    def process_query(self, query: str, limit: int = 5) -> dict:
        """Execute a search and return a structured response."""
        ...

    @abstractmethod
    def capabilities(self) -> dict:
        """Return a description of what this agent can do."""
        ...
