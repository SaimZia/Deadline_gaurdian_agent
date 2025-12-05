"""
Test script for Advanced Dependency Logic in Deadline Guardian Agent
Verifies dependency graph construction and cascading risk analysis.
"""
import unittest
from unittest.mock import MagicMock, patch
import app

class TestDependencyLogic(unittest.TestCase):

    def setUp(self):
        # Sample tasks with dependencies
        # Task 1 (Overdue) -> Blocks Task 2 -> Blocks Task 3
        # Task 4 (Safe) -> Blocks Task 5
        self.tasks = [
            {
                "task_id": "1",
                "task_name": "Core API",
                "task_status": "todo",
                "task_deadline": "2020-01-01", # Overdue (CRITICAL)
                "depends_on": None
            },
            {
                "task_id": "2",
                "task_name": "Frontend Integration",
                "task_status": "todo",
                "task_deadline": "2030-01-01", # Safe date
                "depends_on": "1" # Depends on Overdue Task
            },
            {
                "task_id": "3",
                "task_name": "E2E Tests",
                "task_status": "todo",
                "task_deadline": "2030-01-01", # Safe date
                "depends_on": "2" # Indirectly blocked by Task 1
            },
            {
                "task_id": "4",
                "task_name": "Documentation",
                "task_status": "todo",
                "task_deadline": "2030-01-01", # Safe
                "depends_on": None
            },
            {
                "task_id": "5",
                "task_name": "Publish Docs",
                "task_status": "todo",
                "task_deadline": "2030-01-01", # Safe
                "depends_on": "4" # Depends on Safe Task
            }
        ]

    def test_build_dependency_graph(self):
        """Test graph construction."""
        graph, _, _ = app.build_dependency_graph(self.tasks)
        
        # Check reverse dependencies (who depends on me?)
        self.assertIn("2", graph["1"]) # Task 1 blocks Task 2
        self.assertIn("3", graph["2"]) # Task 2 blocks Task 3
        self.assertIn("5", graph["4"]) # Task 4 blocks Task 5
        self.assertEqual(len(graph["3"]), 0) # Task 3 blocks no one

    def test_cascading_risk_analysis(self):
        """Test that tasks blocked by CRITICAL/HIGH risks are flagged."""
        blocked_tasks, bottlenecks = app.analyze_cascading_risks(self.tasks)
        
        print(f"\nBlocked Tasks: {blocked_tasks}")
        print(f"Bottlenecks: {bottlenecks}")

        # Task 2 should be blocked because Task 1 is CRITICAL (Overdue)
        self.assertIn("2", blocked_tasks)
        
        # Task 5 should NOT be blocked because Task 4 is LOW risk
        self.assertNotIn("5", blocked_tasks)
        
        # Task 1 is a bottleneck (blocks Task 2) - logic defines bottleneck as blocking > 1 task?
        # Let's check logic: "if len(dependents) > 1"
        # In this simple chain 1->2->3, no single task blocks > 1 task directly.
        # Let's add a task to make Task 1 a bottleneck
        
        tasks_with_bottleneck = self.tasks + [{
            "task_id": "6",
            "task_name": "Mobile App",
            "task_status": "todo",
            "task_deadline": "2030-01-01",
            "depends_on": "1" # Now Task 1 blocks Task 2 AND Task 6
        }]
        
        _, bottlenecks_new = app.analyze_cascading_risks(tasks_with_bottleneck)
        self.assertIn("1", bottlenecks_new)
        print(f"New Bottlenecks: {bottlenecks_new}")

if __name__ == '__main__':
    unittest.main()
