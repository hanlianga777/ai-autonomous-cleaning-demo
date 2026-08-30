import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from database import connection as db
from analytics.history_seed import seed_history

from analytics.service import analytics_overview, heatmap, kpis, robot_utilization, task_history
from optimization.agent import generate_recommendations


class AnalyticsOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original = db.DATABASE_PATH
        db.DATABASE_PATH = Path(self.temp.name) / "analytics.sqlite"
        db.initialize_database()
        seed_history()

    def tearDown(self):
        db.DATABASE_PATH = self.original
        self.temp.cleanup()

    def test_thirty_day_history_and_kpis_are_reproducible(self):
        history = task_history()
        metrics = kpis()
        self.assertGreaterEqual(len(history), 280)
        self.assertEqual(metrics["period_days"], 30)
        self.assertGreater(metrics["autonomous_closure_rate"], 80)
        # Synthetic history contains no fake model tool calls.
        self.assertIsNone(metrics["multi_view_recovery_rate"])
        self.assertGreater(metrics["average_closure_time_minutes"], metrics["average_response_time_minutes"])

    def test_heatmap_time_distribution_and_utilization_have_expected_operational_signal(self):
        self.assertEqual(heatmap()[0]["zone_id"], "a1-east-entrance")
        self.assertEqual(sum(point["count"] for point in heatmap()), len(task_history()))
        overview = analytics_overview()
        self.assertEqual(sum(bucket["count"] for bucket in overview["time_distribution"]), len(task_history()))
        for row in robot_utilization():
            self.assertAlmostEqual(row["utilization"], row["active_minutes"] / row["available_minutes"] * 100, delta=0.1)

    def test_optimization_is_bounded_to_analytics_inputs_and_recommendations(self):
        with self.assertRaisesRegex(ValueError, "retired"):
            generate_recommendations()


if __name__ == "__main__":
    unittest.main()
