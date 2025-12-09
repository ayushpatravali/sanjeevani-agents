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

from src.tools.image_fetcher import fetch_wikipedia_image
from src.agents.super_agents import SuperAgent

class TestStructuredOutput(unittest.TestCase):
    def test_image_fetcher(self):
        """Test that image fetcher returns a URL."""
        # Mock requests.get
        with patch('requests.get') as mock_get:
            # Mock search response
            mock_get.return_value.json.side_effect = [
                {"query": {"search": [{"title": "Ocimum tenuiflorum"}]}}, # Search result
                {"query": {"pages": {"123": {"thumbnail": {"source": "http://example.com/tulsi.jpg"}}}}} # Image result
            ]
            
            url = fetch_wikipedia_image("Tulsi")
            self.assertEqual(url, "http://example.com/tulsi.jpg")

    def test_super_agent_structured_output(self):
        """Test that SuperAgent returns structured data."""
        agent = SuperAgent()
        agent.app = MagicMock()
        
        # Mock graph output
        mock_output = {
            "final_answer": '{"answer": "Tulsi is great.", "image_query": "Tulsi", "locations": ["India"]}',
            "research_data": [],
            "gis_data": [],
            "plan": []
        }
        agent.app.invoke.return_value = mock_output
        
        # Mock image fetcher inside query
        with patch('src.tools.image_fetcher.fetch_wikipedia_image') as mock_fetch:
            mock_fetch.return_value = "http://real-wiki-image.jpg"
            
            result = agent.query("Tell me about Tulsi")
            
            self.assertEqual(result["answer"], "Tulsi is great.")
            self.assertEqual(result["locations"], ["India"])
            self.assertEqual(result["image_url"], "http://real-wiki-image.jpg")

if __name__ == '__main__':
    unittest.main()
