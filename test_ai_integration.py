"""
Test script for AI Integration in Deadline Guardian Agent
Mocks the OpenAI client to verify logic flow without an actual API key.
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import app

class TestAIIntegration(unittest.TestCase):

    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True
        
        # Sample tasks for testing
        self.sample_tasks = [
            {
                "task_id": "1",
                "task_name": "Critical Bug Fix",
                "task_status": "todo",
                "task_deadline": "2025-12-01",
                "task_description": "Fix critical production issue affecting payments."
            },
            {
                "task_id": "2",
                "task_name": "Update Docs",
                "task_status": "todo",
                "task_deadline": "2025-12-15",
                "task_description": "Update API documentation."
            }
        ]

    def test_analyze_risks_with_llm_structure(self):
        """Test that the LLM analysis function returns expected structure."""
        
        # Mock the OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        # Mock JSON response from LLM
        expected_ai_output = {
            "risk_analysis": "The critical bug fix is high risk due to its nature.",
            "strategic_recommendations": [
                "Prioritize the payment bug fix immediately.",
                "Schedule documentation update for next week."
            ]
        }
        
        mock_response.choices[0].message.content = json.dumps(expected_ai_output)
        mock_client.chat.completions.create.return_value = mock_response
        
        # Patch the client in the app module
        with patch('app.client', mock_client):
            result = app.analyze_risks_with_llm(self.sample_tasks)
            
            self.assertIsNotNone(result)
            self.assertIn("risk_analysis", result)
            self.assertIn("strategic_recommendations", result)
            self.assertEqual(result["risk_analysis"], expected_ai_output["risk_analysis"])

    @patch('app.collection') # Mock MongoDB collection
    def test_handle_request_with_ai(self, mock_collection):
        """Test the full handler with mocked AI and Database."""
        
        # Setup Mock DB
        mock_collection.find.return_value = self.sample_tasks
        
        # Setup Mock AI
        mock_client = MagicMock()
        mock_response = MagicMock()
        expected_ai_output = {
            "risk_analysis": "AI Analysis: Critical bug needs attention.",
            "strategic_recommendations": ["Fix bug now"]
        }
        mock_response.choices[0].message.content = json.dumps(expected_ai_output)
        mock_client.chat.completions.create.return_value = mock_response
        
        # Patch both client and DB
        with patch('app.client', mock_client):
            payload = {
                "request_id": "test-ai-1",
                "agent_name": "deadline_guardian_agent",
                "intent": "deadline.monitor",
                "input": {"text": "check deadlines"},
                "context": {"user_id": "test", "timestamp": "2025-11-29T12:00:00"}
            }
            
            response = self.app.post('/handle', json=payload)
            data = response.get_json()
            
            # Verify Response Structure
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["status"], "success")
            
            # Verify AI content is in the result
            result_text = data["output"]["result"]
            self.assertIn("🤖 **AI Analysis**", result_text)
            self.assertIn("AI Analysis: Critical bug needs attention.", result_text)
            self.assertIn("💡 **Strategic Recommendations**", result_text)
            self.assertIn("Fix bug now", result_text)
            
            print("\n✅ AI Integration Test Passed!")
            print("Response Preview:")
            print("-" * 40)
            print(result_text)
            print("-" * 40)

if __name__ == '__main__':
    unittest.main()
