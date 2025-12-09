import requests
import logging

logger = logging.getLogger(__name__)

def fetch_wikipedia_image(query: str) -> str:
    """
    Fetches the main image URL for a given query from Wikipedia.
    Returns None if no image found.
    """
    try:
        # 1. Search for the page
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 1
        }
        headers = {
            "User-Agent": "SanjeevaniAgent/1.0 (contact@example.com)"
        }
        response = requests.get(search_url, params=search_params, headers=headers, timeout=5)
        if not response.ok:
            logger.warning(f"Wikipedia search failed: {response.status_code}")
            return None
            
        try:
            data = response.json()
        except ValueError:
            logger.warning("Wikipedia response was not valid JSON")
            return None
        
        if not data.get("query", {}).get("search"):
            return None
            
        page_title = data["query"]["search"][0]["title"]
        
        # 2. Get page image
        img_params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "pageimages",
            "pithumbsize": 500  # Request a thumbnail of 500px width
        }
        img_response = requests.get(search_url, params=img_params, headers=headers, timeout=5)
        img_data = img_response.json()
        
        pages = img_data.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if "thumbnail" in page_info:
                return page_info["thumbnail"]["source"]
                
        return None
        
    except Exception as e:
        logger.error(f"Failed to fetch Wikipedia image for '{query}': {e}")
        return None
