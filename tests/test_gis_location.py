import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules["weaviate"] = MagicMock()
sys.modules["weaviate.classes"] = MagicMock()
sys.modules["weaviate.classes.config"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["groq"] = MagicMock()
sys.modules["langgraph"] = MagicMock()
sys.modules["langgraph.graph"] = MagicMock()
sys.modules["langgraph.prebuilt"] = MagicMock()
sys.modules["langgraph.checkpoint"] = MagicMock()
sys.modules["langgraph.checkpoint.memory"] = MagicMock()
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.gis_agent import GISAgent

class TestGISLocation(unittest.TestCase):
    def test_gis_query(self):
        """Test that GISAgent queries GISLocation collection."""
        agent = GISAgent()
        agent.client = MagicMock()
        
        # Mock collection query response
        mock_obj1 = MagicMock()
        mock_obj1.properties = {"district": "Bangalore", "location": {"latitude": 12.9, "longitude": 77.5}, "soils": "Red"}
        
        mock_obj2 = MagicMock()
        mock_obj2.properties = {"district": "Belgaum", "location": {"latitude": 15.8, "longitude": 74.5}, "soils": "Black"}
        
        mock_response = MagicMock()
        mock_response.objects = [mock_obj1, mock_obj2]
        
        agent.client.collections.get.return_value.query.bm25.return_value = mock_response
        
        # Run query
        result = agent.process_query("Where does Tulsi grow?")
        
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["district"], "Bangalore")
        self.assertEqual(result["results"][0]["latitude"], 12.9)
        self.assertEqual(result["results"][1]["district"], "Belgaum")

if __name__ == '__main__':
    unittest.main()
