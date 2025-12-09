import unittest
import sys
import os
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["weaviate"] = MagicMock()
sys.modules["weaviate.classes"] = MagicMock()
sys.modules["weaviate.classes.config"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["groq"] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.base_agent import BaseAgent

class ConcreteAgent(BaseAgent):
    def process_query(self, query):
        pass
    def capabilities(self):
        pass


class TestFuzzyLogic(unittest.TestCase):
    def setUp(self):
        self.agent = ConcreteAgent("DUMMY_KEY", "DummyAgent")



    def test_exact_match(self):
        """Test that exact names are still found."""
        names = self.agent._extract_plant_names("Tell me about Tulsi")
        self.assertIn("tulsi", names)
        self.assertIn("ocimum sanctum", names)

    def test_fuzzy_match_minor_typo(self):
        """Test that minor typos are corrected."""
        # "Tusli" -> "Tulsi"
        names = self.agent._extract_plant_names("Tell me about Tusli")
        self.assertIn("tulsi", names)

    def test_fuzzy_match_another_typo(self):
        """Test another typo."""
        # "Ashwaganda" -> "Ashwagandha"
        names = self.agent._extract_plant_names("Benefits of Ashwaganda")
        self.assertIn("ashwagandha", names)

    def test_no_false_positives(self):
        """Test that random words don't trigger matches."""
        # "weather" is distinct enough. "Tell me" might be matching "neem" or similar if threshold is too low.
        names = self.agent._extract_plant_names("Is it raining today?")
        self.assertEqual(len(names), 0)


if __name__ == '__main__':
    unittest.main()
