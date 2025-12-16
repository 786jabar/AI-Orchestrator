import unittest
from core.llm_mock import MockLLM, LLMInterface, LLMResponse


class TestMockLLM(unittest.TestCase):
    
    def setUp(self):
        self.llm = MockLLM()
    
    def test_generate_plan(self):
        response = self.llm.generate("Create a plan for web application")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, LLMResponse)
        self.assertIn("Plan", response.content)
    
    def test_generate_code(self):
        response = self.llm.generate("Implement a function")
        self.assertIsNotNone(response)
        self.assertIn("def", response.content)
    
    def test_call_count(self):
        initial_count = self.llm.call_count
        self.llm.generate("test prompt")
        self.assertEqual(self.llm.call_count, initial_count + 1)


class TestLLMInterface(unittest.TestCase):
    
    def setUp(self):
        self.interface = LLMInterface(use_mock=True)
    
    def test_generate_text(self):
        result = self.interface.generate_text("Create a plan")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_get_call_count(self):
        self.interface.generate_text("test")
        count = self.interface.get_call_count()
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()


