import unittest

from analytics.service import analytics_overview, heatmap, kpis, robot_utilization, task_history
from optimization.agent import generate_recommendations


class AnalyticsOptimizationTests(unittest.TestCase):
    def test_thirty_day_history_and_kpis_are_reproducible(self):
        history = task_history()
        metrics = kpis()
        self.assertGreaterEqual(len(history), 300)
        self.assertEqual(metrics["period_days"], 30)
        self.assertGreater(metrics["autonomous_closure_rate"], 80)
        self.assertGreaterEqual(metrics["multi_view_recovery_rate"], 0)
        self.assertLessEqual(metrics["multi_view_recovery_rate"], 100)
        self.assertGreater(metrics["average_closure_time_minutes"], metrics["average_response_time_minutes"])

    def test_heatmap_time_distribution_and_utilization_have_expected_operational_signal(self):
        self.assertEqual(heatmap()[0]["zone_id"], "a1-east-entrance")
        self.assertEqual(sum(point["count"] for point in heatmap()), len(task_history()))
        overview = analytics_overview()
        self.assertEqual(sum(bucket["count"] for bucket in overview["time_distribution"]), len(task_history()))
        lowest = min(robot_utilization(), key=lambda row: row["utilization"])
        self.assertEqual(lowest["robot_id"], "robot-c")

    def test_optimization_is_bounded_to_analytics_inputs_and_recommendations(self):
        result = generate_recommendations()
        self.assertEqual({call["tool"] for call in result["tool_calls"]}, {"Heatmap Tool", "Robot Utilization Tool", "Task History Tool"})
        self.assertEqual({recommendation["type"] for recommendation in result["recommendations"]}, {"STANDBY_POINT", "PROACTIVE_PATROL", "RESOURCE_CONFIGURATION"})
        self.assertNotIn("chain_of_thought", str(result).lower())
        self.assertTrue(any("Scheduler" in guardrail for guardrail in result["guardrails"]))


if __name__ == "__main__":
    unittest.main()
