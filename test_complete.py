"""
Comprehensive Test Suite for Deadline Guardian Agent
Tests all functionality including API endpoints, risk calculation, dependency analysis, and AI integration.
"""
import unittest
from unittest.mock import MagicMock, patch, Mock
import json
from datetime import datetime, timedelta
import app


class TestRiskCalculation(unittest.TestCase):
    """Test risk level calculation logic."""
    
    def test_completed_task(self):
        """Completed tasks should have COMPLETED risk."""
        risk, days = app.calculate_risk_level("2025-12-31", "done")
        self.assertEqual(risk, "COMPLETED")
        self.assertEqual(days, 0)
    
    def test_overdue_task(self):
        """Overdue tasks should have CRITICAL risk."""
        past_date = "2020-01-01"
        risk, days = app.calculate_risk_level(past_date, "todo")
        self.assertEqual(risk, "CRITICAL")
        self.assertLess(days, 0)
    
    def test_due_today(self):
        """Tasks due within 24 hours should have HIGH or CRITICAL risk (depends on time)."""
        today = datetime.now().strftime("%Y-%m-%d")
        risk, days = app.calculate_risk_level(today, "in_progress")
        # Can be HIGH (< 1 day) or CRITICAL (< 0 if past midnight)
        self.assertIn(risk, ["HIGH", "CRITICAL"])
    
    def test_due_in_2_days(self):
        """Tasks due in 2 days should have MEDIUM risk."""
        future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        risk, days = app.calculate_risk_level(future_date, "todo")
        self.assertEqual(risk, "MEDIUM")
        # Days can be 1 or 2 depending on time of day
        self.assertIn(days, [1, 2])
    
    def test_due_in_5_days(self):
        """Tasks due in 5+ days should have LOW risk."""
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        risk, days = app.calculate_risk_level(future_date, "todo")
        self.assertEqual(risk, "LOW")
        self.assertGreaterEqual(days, 3)
    
    def test_invalid_date(self):
        """Invalid dates should return UNKNOWN risk."""
        risk, days = app.calculate_risk_level("invalid-date", "todo")
        self.assertEqual(risk, "UNKNOWN")
        self.assertEqual(days, 0)


class TestTimeFormatting(unittest.TestCase):
    """Test time remaining formatting."""
    
    def test_overdue_formatting(self):
        """Overdue tasks should show OVERDUE message."""
        result = app.format_time_remaining(-3)
        self.assertEqual(result, "OVERDUE by 3 day(s)")
    
    def test_due_today_formatting(self):
        """Tasks due today should show Due TODAY."""
        result = app.format_time_remaining(0)
        self.assertEqual(result, "Due TODAY")
    
    def test_future_formatting(self):
        """Future tasks should show days remaining."""
        result = app.format_time_remaining(5)
        self.assertEqual(result, "5 day(s)")


class TestDependencyGraph(unittest.TestCase):
    """Test dependency graph construction."""
    
    def setUp(self):
        """Set up test tasks with dependencies."""
        self.tasks = [
            {
                "task_id": "T1",
                "task_name": "Task 1",
                "task_status": "todo",
                "task_deadline": "2020-01-01",  # Overdue
                "depends_on": None
            },
            {
                "task_id": "T2",
                "task_name": "Task 2",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "T1"
            },
            {
                "task_id": "T3",
                "task_name": "Task 3",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "T1"  # T1 blocks both T2 and T3 (bottleneck)
            },
            {
                "task_id": "T4",
                "task_name": "Task 4",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "T2"
            }
        ]
    
    def test_graph_construction(self):
        """Test that dependency graph is built correctly."""
        graph, status_map, risk_map = app.build_dependency_graph(self.tasks)
        
        # T1 should block T2 and T3
        self.assertIn("T2", graph["T1"])
        self.assertIn("T3", graph["T1"])
        
        # T2 should block T4
        self.assertIn("T4", graph["T2"])
        
        # T4 blocks nothing
        self.assertEqual(len(graph["T4"]), 0)
    
    def test_status_map(self):
        """Test that status map is populated correctly."""
        _, status_map, _ = app.build_dependency_graph(self.tasks)
        
        self.assertEqual(status_map["T1"], "todo")
        self.assertEqual(status_map["T2"], "todo")
    
    def test_risk_map(self):
        """Test that initial risk map is calculated correctly."""
        _, _, risk_map = app.build_dependency_graph(self.tasks)
        
        # T1 is overdue, should be CRITICAL
        self.assertEqual(risk_map["T1"], "CRITICAL")
        
        # T2, T3, T4 have future deadlines, should be LOW
        self.assertEqual(risk_map["T2"], "LOW")
        self.assertEqual(risk_map["T3"], "LOW")
    
    def test_comma_separated_dependencies(self):
        """Test handling of comma-separated dependency strings."""
        tasks_with_multiple_deps = [
            {
                "task_id": "A",
                "task_name": "Task A",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": None
            },
            {
                "task_id": "B",
                "task_name": "Task B",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": None
            },
            {
                "task_id": "C",
                "task_name": "Task C",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "A, B"  # Comma-separated
            }
        ]
        
        graph, _, _ = app.build_dependency_graph(tasks_with_multiple_deps)
        
        # Both A and B should block C
        self.assertIn("C", graph["A"])
        self.assertIn("C", graph["B"])


class TestCascadingRisks(unittest.TestCase):
    """Test cascading risk analysis and bottleneck detection."""
    
    def setUp(self):
        """Set up test tasks."""
        self.tasks = [
            {
                "task_id": "CRITICAL_TASK",
                "task_name": "Critical Blocker",
                "task_status": "todo",
                "task_deadline": "2020-01-01",  # Overdue = CRITICAL
                "depends_on": None
            },
            {
                "task_id": "BLOCKED_1",
                "task_name": "Blocked Task 1",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "CRITICAL_TASK"
            },
            {
                "task_id": "BLOCKED_2",
                "task_name": "Blocked Task 2",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "CRITICAL_TASK"
            },
            {
                "task_id": "SAFE_TASK",
                "task_name": "Safe Task",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": None
            }
        ]
    
    def test_blocked_tasks_detection(self):
        """Test that tasks blocked by critical dependencies are identified."""
        blocked_tasks, _ = app.analyze_cascading_risks(self.tasks)
        
        # BLOCKED_1 and BLOCKED_2 should be blocked by CRITICAL_TASK
        self.assertIn("BLOCKED_1", blocked_tasks)
        self.assertIn("BLOCKED_2", blocked_tasks)
        
        # SAFE_TASK should not be blocked
        self.assertNotIn("SAFE_TASK", blocked_tasks)
    
    def test_bottleneck_detection(self):
        """Test that bottlenecks (tasks blocking >1 task) are identified."""
        _, bottlenecks = app.analyze_cascading_risks(self.tasks)
        
        # CRITICAL_TASK blocks 2 tasks, so it's a bottleneck
        self.assertIn("CRITICAL_TASK", bottlenecks)
        
        # Other tasks don't block multiple tasks
        self.assertNotIn("SAFE_TASK", bottlenecks)


class TestAPIEndpoints(unittest.TestCase):
    """Test Flask API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app.app.test_client()
        self.app.testing = True
    
    def test_health_endpoint(self):
        """Test /health endpoint."""
        response = self.app.get('/health')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["agent"], "deadline_guardian_agent")
        self.assertIn("timestamp", data)
        self.assertIn("mongodb", data)
        self.assertIn("ai_enabled", data)
    
    def test_root_endpoint(self):
        """Test / root endpoint."""
        response = self.app.get('/')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Deadline Guardian Agent is running", data["message"])
        self.assertEqual(data["status"], "online")
        self.assertIn("endpoints", data)
    
    def test_handle_missing_body(self):
        """Test /handle with missing/empty request body."""
        # Test with empty JSON object
        response = self.app.post('/handle', json={})
        data = response.get_json()
        
        # Should return error for missing required fields
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["status"], "error")

    
    def test_handle_invalid_intent(self):
        """Test /handle with invalid intent."""
        payload = {
            "request_id": "test-123",
            "intent": "invalid.intent",
            "input": {"text": "test"}
        }
        
        response = self.app.post('/handle', json=payload)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error"]["type"], "invalid_intent")
    
    @patch('app.collection')
    def test_handle_success_with_tasks(self, mock_collection):
        """Test /handle with valid request and mocked tasks."""
        # Mock MongoDB response
        mock_tasks = [
            {
                "task_id": "T1",
                "task_name": "Test Task",
                "task_status": "todo",
                "task_deadline": "2020-01-01",  # Overdue
                "task_description": "Test description",
                "depends_on": None
            }
        ]
        mock_collection.find.return_value = mock_tasks
        
        payload = {
            "request_id": "test-456",
            "intent": "deadline.monitor",
            "input": {"text": "check deadlines"}
        }
        
        response = self.app.post('/handle', json=payload)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["agent_name"], "deadline_guardian_agent")
        self.assertIn("output", data)
        self.assertIn("result", data["output"])
        self.assertIn("confidence", data["output"])
        self.assertIn("details", data["output"])
        
        # Check that result contains expected sections
        result_text = data["output"]["result"]
        self.assertIn("Advanced Deadline Report", result_text)
        self.assertIn("Total Tasks:", result_text)
    
    @patch('app.collection')
    def test_handle_empty_tasks(self, mock_collection):
        """Test /handle with no tasks in database."""
        mock_collection.find.return_value = []
        
        payload = {
            "request_id": "test-789",
            "intent": "deadline.monitor",
            "input": {"text": "check deadlines"}
        }
        
        response = self.app.post('/handle', json=payload)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertIn("Total Tasks: 0", data["output"]["result"])


class TestAIIntegration(unittest.TestCase):
    """Test AI analysis integration."""
    
    def setUp(self):
        """Set up test tasks."""
        self.tasks = [
            {
                "task_id": "AI_TEST_1",
                "task_name": "Critical Bug",
                "task_status": "todo",
                "task_deadline": "2020-01-01",
                "task_description": "Fix critical production bug",
                "depends_on": None
            }
        ]
    
    def test_ai_analysis_with_mock_client(self):
        """Test AI analysis with mocked OpenAI client."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        expected_output = {
            "risk_analysis": "Critical task requires immediate attention.",
            "strategic_recommendations": [
                "Allocate senior developer to critical bug",
                "Set up daily standup for this issue"
            ]
        }
        
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(expected_output)
        mock_client.chat.completions.create.return_value = mock_response
        
        # Patch the client
        with patch('app.client', mock_client):
            result = app.analyze_risks_with_llm(self.tasks, [], [])
            
            self.assertIsNotNone(result)
            self.assertEqual(result["risk_analysis"], expected_output["risk_analysis"])
            self.assertEqual(len(result["strategic_recommendations"]), 2)
    
    def test_ai_analysis_without_client(self):
        """Test AI analysis when client is not available."""
        with patch('app.client', None):
            result = app.analyze_risks_with_llm(self.tasks, [], [])
            self.assertIsNone(result)
    
    def test_ai_analysis_with_exception(self):
        """Test AI analysis handles exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch('app.client', mock_client):
            result = app.analyze_risks_with_llm(self.tasks, [], [])
            self.assertIsNone(result)


class TestFullIntegration(unittest.TestCase):
    """Integration tests for complete workflow."""
    
    def setUp(self):
        """Set up test client and mock data."""
        self.app = app.app.test_client()
        self.app.testing = True
        
        self.complex_tasks = [
            {
                "task_id": "BACKEND",
                "task_name": "Backend API",
                "task_status": "todo",
                "task_deadline": "2020-01-01",  # Overdue
                "task_description": "Build REST API",
                "depends_on": None
            },
            {
                "task_id": "FRONTEND",
                "task_name": "Frontend UI",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "task_description": "Build React UI",
                "depends_on": "BACKEND"
            },
            {
                "task_id": "MOBILE",
                "task_name": "Mobile App",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "task_description": "Build mobile app",
                "depends_on": "BACKEND"
            },
            {
                "task_id": "TESTING",
                "task_name": "E2E Testing",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "task_description": "End-to-end tests",
                "depends_on": "FRONTEND"
            }
        ]
    
    @patch('app.collection')
    @patch('app.client')
    def test_full_workflow_with_ai(self, mock_ai_client, mock_collection):
        """Test complete workflow with AI analysis."""
        # Setup mocks
        mock_collection.find.return_value = self.complex_tasks
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "risk_analysis": "Backend API is a critical bottleneck blocking Frontend and Mobile.",
            "strategic_recommendations": [
                "Prioritize Backend API completion immediately",
                "Consider parallel work on documentation while waiting"
            ]
        })
        mock_ai_client.chat.completions.create.return_value = mock_response
        
        # Make request
        payload = {
            "request_id": "integration-test",
            "intent": "deadline.monitor",
            "input": {"text": "analyze project deadlines"}
        }
        
        response = self.app.post('/handle', json=payload)
        data = response.get_json()
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        
        result = data["output"]["result"]
        
        # Should show 4 total tasks
        self.assertIn("Total Tasks: 4", result)
        
        # Should identify BACKEND as bottleneck
        self.assertIn("Bottlenecks: 1", result)
        
        # Should show CRITICAL section for overdue BACKEND
        self.assertIn("CRITICAL", result)
        self.assertIn("BACKEND", result)
        
        # Should show BLOCKED section for FRONTEND and MOBILE
        self.assertIn("BLOCKED", result)
        
        # Should include AI analysis
        self.assertIn("AI Analysis", result)
        self.assertIn("bottleneck", result.lower())
        
        # Should include recommendations
        self.assertIn("Strategic Recommendations", result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_task_with_missing_fields(self):
        """Test handling of tasks with missing fields."""
        incomplete_task = {
            "task_id": "INCOMPLETE",
            "task_name": "Incomplete Task"
            # Missing deadline, status, etc.
        }
        
        # Should not crash
        risk, days = app.calculate_risk_level(
            incomplete_task.get("task_deadline", ""),
            incomplete_task.get("task_status", "")
        )
        
        self.assertEqual(risk, "UNKNOWN")
    
    def test_circular_dependencies(self):
        """Test handling of circular dependencies."""
        circular_tasks = [
            {
                "task_id": "A",
                "task_name": "Task A",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "B"
            },
            {
                "task_id": "B",
                "task_name": "Task B",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": "A"  # Circular!
            }
        ]
        
        # Should not crash
        graph, _, _ = app.build_dependency_graph(circular_tasks)
        
        # Both should reference each other
        self.assertIn("A", graph["B"])
        self.assertIn("B", graph["A"])
    
    def test_list_dependencies(self):
        """Test handling of list-type dependencies."""
        task_with_list_deps = [
            {
                "task_id": "X",
                "task_name": "Task X",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": None
            },
            {
                "task_id": "Y",
                "task_name": "Task Y",
                "task_status": "todo",
                "task_deadline": "2030-01-01",
                "depends_on": ["X"]  # List format
            }
        ]
        
        graph, _, _ = app.build_dependency_graph(task_with_list_deps)
        self.assertIn("Y", graph["X"])


def run_all_tests():
    """Run all test suites and print summary."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRiskCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestCascadingRisks))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestAIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestFullIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
