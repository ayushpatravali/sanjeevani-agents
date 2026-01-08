
import sys
import os
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.database.weaviate_client import weaviate_manager
from src.agents.research_agent import ResearchAgent

def test_research_crash():
    print("--- 1. Initial Connect ---")
    if not weaviate_manager.connect():
        print("Initial connect failed!")
        return
    
    agent = ResearchAgent()
    print("Agent initialized.")
    
    # Simulate closing the connection "behind the agent's back"
    print("--- 2. Simulating DISCONNECT ---")
    weaviate_manager.close() 
    print("Client manually closed.")
    
    # Try Query Q1: "uses of Hygrophila auriculata"
    query = "uses of Hygrophila auriculata"
    print(f"--- 3. Querying: '{query}' ---")
    try:
        # This triggers _extract_plant_names -> _search -> _search_with_plant_filter
        # _search_with_plant_filter calls _connect(), which checks is_ready().
        # Since client IS NOT None (the object exists, just closed), is_ready() call might crash.
        # My try-except fix SHOULD handle this.
        result = agent.process_query(query)
        print(f"Result: {result.get('summary')}")
    except Exception as e:
        print(f"CRASHED CAUGHT IN MAIN: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_research_crash()
