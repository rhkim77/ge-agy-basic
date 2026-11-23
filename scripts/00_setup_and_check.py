#!/usr/bin/env python3
"""Task 00: Enable required GCP APIs and verify Gemini Enterprise 30-day Free-Trial / Subscription status."""

import json
import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import api_headers, de_base, get_access_token, load_env

REQUIRED_APIS = [
    "discoveryengine.googleapis.com",
    "businessaicode.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "dlp.googleapis.com",
    "modelarmor.googleapis.com",
]


def main():
    env = load_env()
    project_id = env["PROJECT_ID"]
    location = env["GE_LOCATION"]
    engine_id = env.get("GE_ENGINE_ID", "")
    token = get_access_token()

    tinfo = requests.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={token}").json()
    caller = tinfo.get("email", "unknown")
    print(f"Active Principal : {caller}")
    print(f"Target Project   : {project_id} (GE Location: {location})")

    print("\n[Step 1/3] Enabling required Google Cloud APIs...")
    for svc in REQUIRED_APIS:
        r = requests.post(
            f"https://serviceusage.googleapis.com/v1/projects/{project_id}/services/{svc}:enable",
            headers=api_headers(token, project_id),
            json={},
        )
        status = "OK" if r.ok else f"WARN ({r.status_code})"
        print(f"  - {svc}: {status}")

    print("\n[Step 2/3] Checking Gemini Enterprise LicenseConfigs (30-day Free-Trial / Active Subscriptions)...")
    lr = requests.get(
        f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/licenseConfigs",
        headers=api_headers(token, project_id),
    )
    if lr.ok:
        configs = lr.json().get("licenseConfigs", [])
        if not configs:
            print("  [ACTION NEEDED] No LicenseConfig found in this location.")
            print("  -> Open GCP Console > Gemini Enterprise > Create app to start the 30-day Free Trial.")
        for c in configs:
            cid = c.get("name", "").split("/")[-1]
            print(
                f"  - {cid}: state={c.get('state')}, seats={c.get('licenseCount')}, "
                f"freeTrial={c.get('freeTrial', False)}, term={c.get('subscriptionTerm')}"
            )
    else:
        print(f"  [WARN] Could not query licenseConfigs ({lr.status_code}): {lr.text[:200]}")

    ulr = requests.get(
        f"{de_base(location)}/v1/projects/{project_id}/locations/{location}/userStores/default_user_store/userLicenses?pageSize=20",
        headers=api_headers(token, project_id),
    )
    if ulr.ok:
        ulics = ulr.json().get("userLicenses", [])
        print(f"  Assigned User Seats in {location}: {len(ulics)}")
        for u in ulics[:5]:
            print(f"    * {u.get('userPrincipal')} -> {u.get('licenseAssignmentState')}")

    print("\n[Step 3/3] Checking Gemini Enterprise Apps (Engines)...")
    er = requests.get(
        f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/engines",
        headers=api_headers(token, project_id),
    )
    if er.ok:
        engines = er.json().get("engines", [])
        for e in engines:
            eid = e.get("name", "").split("/")[-1]
            marker = " <-- TARGET (.env)" if eid == engine_id else ""
            print(f"  - {eid} ({e.get('displayName')}){marker}")
        if not engines:
            print("  [ACTION NEEDED] No GE App found. Create an App in Console (Task 00) and set GE_ENGINE_ID in .env.")


if __name__ == "__main__":
    main()
