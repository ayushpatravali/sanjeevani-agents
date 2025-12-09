import sys
import os
import unittest
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
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.super_agents import SuperAgent

class TestLangGraphLogic(unittest.TestCase):
    def setUp(self):
        self.super_agent = SuperAgent()
        self.super_agent.groq_client = MagicMock()
        self.super_agent.workers['research'] = MagicMock()
        self.super_agent.workers['gis'] = MagicMock()
        
        # Mock the app invoke
        self.super_agent.app = MagicMock()

    def test_planner_node(self):
        """Test the planner node logic directly."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '["Identify plant", "Find habitat"]'
        self.super_agent.groq_client.chat.completions.create.return_value = mock_response
        
        state = {"question": "Where does the malaria plant grow?"}
        result = self.super_agent._planner_node(state)
        
        self.assertEqual(result["plan"], ["Identify plant", "Find habitat"])
        self.assertEqual(result["current_step_index"], 0)

    def test_semantic_routing(self):
        """Test LLM-based semantic routing."""
        # Mock LLM response for routing
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "GIS"
        self.super_agent.groq_client.chat.completions.create.return_value = mock_response
        
        state = {"plan": ["Where is it found?"], "current_step_index": 0}
        decision = self.super_agent._route_decision(state)
        self.assertEqual(decision, "gis")

    def test_retry_logic(self):
        """Test that agent retries when no results found."""
        # Mock Research Agent to return empty first
        self.super_agent.workers['research'].process_query.return_value = {"results": []}
        
        state = {
            "plan": ["Find plant"], 
            "current_step_index": 0, 
            "retry_count": 0,
            "research_data": []
        }
        
        result = self.super_agent._research_node(state)
        
        # Should increment retry count and NOT advance step index
        self.assertEqual(result["retry_count"], 1)
        self.assertIn("medicinal plant", result["plan"][0]) # Check query rewrite


    def test_context_injection(self):
        """Test that context is passed to the next agent."""
        # Mock previous result
        state = {
            "plan": ["Find habitat"], 
            "current_step_index": 0,
            "research_data": [{"results": [{"botanical_name": "Artemisia"}]}]
        }
        
        self.super_agent._gis_node(state)
        
        # Verify GIS agent was called with injected context
        args, _ = self.super_agent.workers['gis'].process_query.call_args
        self.assertIn("Artemisia", args[0])

if __name__ == '__main__':
    unittest.main()
