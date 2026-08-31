"""Interview runtime fingerprint and safe Advanced projection contracts."""
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

from api.routes import (
    get_event_detail, get_events, get_operations_snapshot, get_operations_work_orders,
    get_workbench_scenario_02_assets, get_workbench_scenarios, health_check,
    post_ai_lab_mock_case, post_multiview_scenario_02,
)
from api.runtime_contract import RELEASE_CONTRACT, REQUIRED_CAPABILITIES, runtime_info


class RuntimeContractTests(TestCase):

    def test_legacy_customer_runtime_reads_are_retired(self):
        for endpoint in (
            get_workbench_scenario_02_assets, get_workbench_scenarios,
            get_operations_snapshot, get_operations_work_orders, get_events,
            lambda: get_event_detail("legacy-event"), post_multiview_scenario_02,
            lambda: post_ai_lab_mock_case("heavy_milk_tea_spill"),
        ):
            with self.subTest(endpoint=endpoint.__name__), self.assertRaises(HTTPException) as error:
                endpoint()
            self.assertEqual(error.exception.status_code, 410)

    def test_health_has_precise_release_contract_and_required_capabilities(self):
        health = health_check()
        self.assertEqual(health["release_contract"], RELEASE_CONTRACT)
        self.assertTrue(set(REQUIRED_CAPABILITIES).issubset(set(health["capabilities"])))
        # Kept for existing callers, but no longer sufficient for launcher reuse.
        self.assertEqual(health["api_contract"], "operations.v1")

    @patch("api.runtime_contract.get_agent_model", return_value="Bearer secret-agent-model")
    @patch("api.runtime_contract.system_ai_status")
    def test_advanced_runtime_info_is_allowlisted_and_secret_free(self, status, _agent):
        status.return_value = {
            "qwen_vl": {"mode": "REAL_READY", "model": "/Users/private/qwen-vl-max", "api_key_configured": True},
            "yolo": {"loaded": False, "weights_path": "/Users/private/model.pt"},
            "reason": "Bearer secret-token",
        }
        info = runtime_info()
        self.assertEqual(info["release_contract"], RELEASE_CONTRACT)
        self.assertEqual(info["cloud_status"], "REAL_READY")
        self.assertEqual(info["vlm_model"], "[REDACTED]")
        self.assertEqual(info["agent_model"], "[REDACTED]")
        self.assertEqual(info["evidence_mode"], "CONTROLLED_EVIDENCE")
        rendered = str(info)
        self.assertNotIn("secret-token", rendered)
        self.assertNotIn("/Users/private", rendered)
        self.assertNotIn("api_key", rendered)
