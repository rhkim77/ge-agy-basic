#!/usr/bin/env python3
"""Shared configuration, ADC/gcloud auth, and REST API helpers for the GE + Antigravity Demo Lab."""

import os
import shutil
import subprocess
import time
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_env() -> dict[str, str]:
    env = {}
    for candidate in (ROOT_DIR / ".env.example", ROOT_DIR / ".env"):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(env.keys()):
        if k in os.environ:
            env[k] = os.environ[k]
    if not env.get("PROJECT_ID") or env["PROJECT_ID"] == "YOUR_PROJECT_ID":
        raise RuntimeError("Set PROJECT_ID in .env (copy .env.example to .env first).")
    if not env.get("GCS_BUCKET"):
        env["GCS_BUCKET"] = f"{env['PROJECT_ID']}-cbl-ge-demo"
    return env


def find_gcloud() -> str:
    for path in (
        shutil.which("gcloud"),
        str(Path.home() / "google-cloud-sdk" / "bin" / "gcloud"),
        "/usr/bin/gcloud",
    ):
        if path and Path(path).exists():
            return path
    raise RuntimeError("gcloud binary not found. Install Google Cloud SDK or add it to PATH.")


def get_access_token() -> str:
    gcloud = find_gcloud()
    for cmd in (
        [gcloud, "auth", "application-default", "print-access-token"],
        [gcloud, "auth", "print-access-token"],
    ):
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    raise RuntimeError(
        "No valid Google Cloud access token found. Run:\n"
        "  gcloud auth application-default login --no-launch-browser"
    )


def api_headers(token: str, project_id: str, content_type: str = "application/json") -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": project_id,
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def de_base(location: str) -> str:
    return "https://discoveryengine.googleapis.com" if location == "global" else f"https://{location}-discoveryengine.googleapis.com"


def poll_operation(token: str, project_id: str, location: str, op_name: str, timeout_sec: int = 300) -> dict:
    url = f"{de_base(location)}/v1alpha/{op_name}"
    start = time.time()
    while time.time() - start < timeout_sec:
        r = requests.get(url, headers=api_headers(token, project_id))
        r.raise_for_status()
        data = r.json()
        if data.get("done"):
            return data
        time.sleep(5)
    raise TimeoutError(f"Operation timed out after {timeout_sec}s: {op_name}")
