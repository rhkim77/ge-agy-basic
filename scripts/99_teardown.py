#!/usr/bin/env python3
"""Ordered teardown: Delete custom GE Agents -> Detach 1P DataStores -> Delete DataStores -> Delete BigQuery Dataset -> Delete GCS Bucket."""

import sys
import urllib.parse
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import api_headers, de_base, get_access_token, load_env, poll_operation


def main():
    env = load_env()
    project_id = env["PROJECT_ID"]
    location = env["GE_LOCATION"]
    engine_id = env["GE_ENGINE_ID"]
    bucket = env["GCS_BUCKET"]
    bq_dataset = env["BQ_DATASET"]
    prefix = env["DS_PREFIX"]
    token = get_access_token()

    ds_ids = [
        f"{prefix}-ad-compliance",
        f"{prefix}-sales-policy",
        f"{prefix}-voc-sop",
        f"{prefix}-bq-sales-inventory",
        f"{prefix}-bq-voc-claims",
    ]
    base = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection"

    print("[1/5] Deleting Lab Agents on default_assistant...")
    ar = requests.get(f"{base}/engines/{engine_id}/assistants/default_assistant/agents", headers=api_headers(token, project_id))
    if ar.ok:
        for a in ar.json().get("agents", []):
            if a.get("displayName", "").startswith("CBL "):
                dr = requests.delete(f"{de_base(location)}/v1alpha/{a['name']}", headers=api_headers(token, project_id))
                print(f"  [DELETED AGENT] {a.get('displayName')}: {dr.status_code}")

    print("[2/5] Detaching Lab DataStores from GE Engine...")
    r = requests.get(f"{base}/engines/{engine_id}", headers=api_headers(token, project_id))
    if r.ok:
        remaining = [d for d in r.json().get("dataStoreIds", []) if d not in ds_ids]
        pr = requests.patch(
            f"{base}/engines/{engine_id}?updateMask=dataStoreIds",
            headers=api_headers(token, project_id),
            json={"dataStoreIds": remaining},
        )
        if pr.ok and "/operations/" in pr.json().get("name", "") and not pr.json().get("done"):
            poll_operation(token, project_id, location, pr.json()["name"], timeout_sec=120)
        print(f"  [OK] Remaining dataStoreIds: {remaining}")

    print("[3/5] Deleting Lab DataStores...")
    for ds_id in ds_ids:
        dr = requests.delete(f"{base}/dataStores/{ds_id}", headers=api_headers(token, project_id))
        print(f"  [DELETE {ds_id}] status={dr.status_code}")

    print("[4/5] Deleting BigQuery Dataset...")
    br = requests.delete(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{bq_dataset}?deleteContents=true",
        headers=api_headers(token, project_id),
    )
    print(f"  [DELETE BQ {bq_dataset}] status={br.status_code}")

    print("[5/5] Deleting GCS Bucket...")
    lr = requests.get(f"https://storage.googleapis.com/storage/v1/b/{bucket}/o", headers=api_headers(token, project_id))
    if lr.ok:
        for item in lr.json().get("items", []):
            name = urllib.parse.quote(item["name"], safe="")
            requests.delete(f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{name}", headers=api_headers(token, project_id))
        requests.delete(f"https://storage.googleapis.com/storage/v1/b/{bucket}", headers=api_headers(token, project_id))
        print(f"  [DELETED] gs://{bucket}")


if __name__ == "__main__":
    main()
