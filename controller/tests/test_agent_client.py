import unittest
from unittest.mock import Mock

import requests

from check_ui.agent_client import AgentClient


class TestAgentClientLogging(unittest.TestCase):

    def test_preview_compacts_whitespace_and_truncates(self):
        preview = AgentClient._preview("line one\nline two\tline three", limit=18)

        self.assertEqual(preview, "line one line two...")

    def test_log_job_status_uses_single_line_truncated_output(self):
        logger = Mock()
        client = AgentClient(logger=logger)
        output = "[TASK DONE]\n" + ("Communication relay mission completed successfully. " * 10)

        client._log_job_status(
            "7a237dda-b808-4e8a-8dbd-e3acc3179bd8",
            {
                "status": "completed",
                "result": {
                    "success": True,
                    "output": output,
                },
            },
            55.1,
        )

        message = logger.info.call_args.args[0]
        self.assertNotIn("\n", message)
        self.assertIn("result_success=True", message)
        self.assertIn("output=[TASK DONE] Communication relay mission", message)
        self.assertLessEqual(len(message), 620)

    def test_cancel_job_posts_cancel_endpoint(self):
        client = AgentClient(base_url="http://agent.test")
        response = Mock(status_code=200)
        client.session.post = Mock(return_value=response)

        self.assertTrue(client.cancel_job("job-1"))
        client.session.post.assert_called_once_with(
            "http://agent.test/agent/jobs/job-1/cancel",
            timeout=10,
        )

    def test_wait_timeout_cancels_job(self):
        client = AgentClient()
        client.cancel_job = Mock(return_value=True)

        success, result = client.wait_for_completion("job-1", timeout=-1)

        self.assertFalse(success)
        self.assertIsNone(result)
        client.cancel_job.assert_called_once_with("job-1")

    def test_cancel_transport_failure_does_not_mask_timeout(self):
        client = AgentClient()
        client.session.post = Mock(
            side_effect=requests.exceptions.ConnectionError("cancel transport failed")
        )

        success, result = client.wait_for_completion("job-1", timeout=-1)

        self.assertFalse(success)
        self.assertIsNone(result)
        client.session.post.assert_called_once_with(
            "http://localhost:18000/agent/jobs/job-1/cancel",
            timeout=10,
        )

    def test_callback_stop_cancels_job(self):
        client = AgentClient()
        client.get_job_status = Mock(return_value={"status": "running"})
        client.cancel_job = Mock(return_value=True)

        success, result = client.wait_for_completion(
            "job-1",
            poll_interval=0,
            status_callback=lambda _status, _elapsed: False,
        )

        self.assertFalse(success)
        self.assertIsNone(result)
        client.cancel_job.assert_called_once_with("job-1")

    def test_status_poll_failures_cancel_job(self):
        client = AgentClient()
        client.get_job_status = Mock(return_value=None)
        client.cancel_job = Mock(return_value=True)

        success, result = client.wait_for_completion(
            "job-1",
            poll_interval=0,
            max_status_failures=1,
        )

        self.assertFalse(success)
        self.assertIsNone(result)
        client.cancel_job.assert_called_once_with("job-1")

    def test_terminal_job_statuses_do_not_cancel(self):
        cases = [
            ({"status": "completed", "result": {"success": True}}, True),
            ({"status": "failed", "error": "boom"}, False),
            ({"status": "cancelled"}, False),
        ]

        for job_info, expected_success in cases:
            with self.subTest(status=job_info["status"]):
                client = AgentClient()
                client.get_job_status = Mock(return_value=job_info)
                client.cancel_job = Mock(return_value=True)

                success, result = client.wait_for_completion("job-1", poll_interval=0)

                self.assertEqual(success, expected_success)
                self.assertEqual(result, job_info)
                client.cancel_job.assert_not_called()


if __name__ == "__main__":
    unittest.main()
