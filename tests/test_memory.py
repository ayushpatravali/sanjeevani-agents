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

from src.agents.super_agents import SuperAgent, AgentState
# Define dummy classes since we mocked the module
class HumanMessage:
    def __init__(self, content): self.content = content; self.type = "human"
class SystemMessage:
    def __init__(self, content): self.content = content; self.type = "system"


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.super_agent = SuperAgent()
        self.super_agent.groq_client = MagicMock()
        self.super_agent.workers['research'] = MagicMock()
        self.super_agent.workers['gis'] = MagicMock()
        self.super_agent.app = MagicMock() # Mock the compiled graph

    def test_planner_uses_history(self):
        """Test that planner receives chat history."""
        # Mock state with history
        state = {
            "question": "Where does it grow?",
            "chat_history": [
                HumanMessage(content="What is Tulsi?"),
                SystemMessage(content="Tulsi is a medicinal plant.")
            ]
        }
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '["Find habitat of Tulsi"]'
        self.super_agent.groq_client.chat.completions.create.return_value = mock_response
        
        result = self.super_agent._planner_node(state)
        
        # Verify prompt contained history
        call_args = self.super_agent.groq_client.chat.completions.create.call_args
        prompt_sent = call_args[1]['messages'][0]['content']
        
        self.assertIn("What is Tulsi?", prompt_sent)
        self.assertIn("Tulsi is a medicinal plant", prompt_sent)
        self.assertEqual(result["plan"], ["Find habitat of Tulsi"])

if __name__ == '__main__':
    unittest.main()
