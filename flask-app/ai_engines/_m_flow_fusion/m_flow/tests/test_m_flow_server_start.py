"""Smoke-test suite for the M-Flow HTTP server.

Validates startup, health/root endpoints, authentication, data ingestion,
memorization pipeline, graph retrieval, and search functionality.
"""

import os
import signal
import subprocess
import sys
import time
import unittest
import uuid

import requests
from pathlib import Path

SERVER_HOST = "0.0.0.0"
SERVER_PORT = "8000"
BASE_URL = f"http://127.0.0.1:{SERVER_PORT}"
STARTUP_WAIT_SECS = 35
REQUEST_TIMEOUT_STD = 15
REQUEST_TIMEOUT_LONG = 50
REQUEST_TIMEOUT_PIPELINE = 150


class TestMflowServerStart(unittest.TestCase):
    """Verify the M-Flow uvicorn server starts correctly and handles a full request cycle."""

    @classmethod
    def setUpClass(cls):
        cls.server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "m_flow.api.client:app",
                "--host",
                SERVER_HOST,
                "--port",
                SERVER_PORT,
            ],
            preexec_fn=os.setsid,
        )
        time.sleep(STARTUP_WAIT_SECS)

        if cls.server_process.poll() is not None:
            err_output = cls.server_process.stderr.read().decode("utf-8")
            print(f"Server bootstrap failed: {err_output}", file=sys.stderr)
            raise RuntimeError(f"Server bootstrap failed: {err_output}")

    @classmethod
    def tearDownClass(cls):
        proc = getattr(cls, "server_process", None)
        if proc is None:
            return
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
        proc.wait()

    def _authenticate(self) -> str:
        """Log in with default credentials and return the Bearer header value."""
        creds = {"username": "default_user@example.com", "password": "default_password"}
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=creds, timeout=REQUEST_TIMEOUT_STD)
        resp.raise_for_status()
        return f"Bearer {resp.json()['access_token']}"

    def test_server_is_running(self):
        """Full request cycle: health -> root -> login -> add -> memorize -> graph -> search."""
        health_resp = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT_STD)
        self.assertIn(health_resp.status_code, [200])

        root_resp = requests.get(f"{BASE_URL}/", timeout=REQUEST_TIMEOUT_STD)
        self.assertEqual(root_resp.status_code, 200)
        self.assertIn("status", root_resp.json())
        self.assertEqual(root_resp.json()["status"], "ok")
        self.assertIn("service", root_resp.json())

        bearer_token = self._authenticate()
        auth_hdr = {"Authorization": bearer_token}

        ds_name = f"test_{uuid.uuid4().hex[:8]}"
        sample_file = Path(os.path.join(Path(__file__).parent, "test_data/example.png"))
        upload_payload = {"datasetName": ds_name}
        file_part = {"data": (sample_file.name, open(sample_file, "rb"))}

        add_resp = requests.post(
            f"{BASE_URL}/api/v1/add",
            headers=auth_hdr,
            data=upload_payload,
            files=file_part,
            timeout=REQUEST_TIMEOUT_LONG,
        )
        if add_resp.status_code not in (200, 201):
            add_resp.raise_for_status()

        pipeline_body = {"datasets": [ds_name]}
        pipeline_hdrs = {**auth_hdr, "Content-Type": "application/json"}

        mem_resp = requests.post(
            f"{BASE_URL}/api/v1/memorize",
            headers=pipeline_hdrs,
            json=pipeline_body,
            timeout=REQUEST_TIMEOUT_PIPELINE,
        )
        if mem_resp.status_code not in (200, 201):
            mem_resp.raise_for_status()

        all_datasets = requests.get(f"{BASE_URL}/api/v1/datasets", headers=auth_hdr).json()

        target_ds_id = None
        for ds in all_datasets:
            if ds["name"] == ds_name:
                target_ds_id = ds["id"]
                break

        graph_resp = requests.get(f"{BASE_URL}/api/v1/datasets/{target_ds_id}/graph", headers=auth_hdr)
        self.assertEqual(graph_resp.status_code, 200)

        graph_payload = graph_resp.json()
        self.assertGreater(len(graph_payload.get("nodes", [])), 0, "No nodes found in knowledge graph")

        search_body = {"searchType": "TRIPLET_COMPLETION", "query": "What's in the document?"}
        search_resp = requests.post(
            f"{BASE_URL}/api/v1/search",
            headers=pipeline_hdrs,
            json=search_body,
            timeout=REQUEST_TIMEOUT_LONG,
        )
        if search_resp.status_code not in (200, 201):
            search_resp.raise_for_status()


if __name__ == "__main__":
    unittest.main()
