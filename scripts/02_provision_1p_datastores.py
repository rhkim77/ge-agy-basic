#!/usr/bin/env python3
"""Task 01 & 02: Upload synthetic data to GCS/BigQuery and provision 5 Discovery Engine 1P DataStores."""

import mimetypes
import sys
import time
import urllib.parse
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT_DIR, api_headers, de_base, get_access_token, load_env, poll_operation


def ensure_gcs_bucket(token: str, project_id: str, bucket: str, location: str = "US"):
    r = requests.get(
        f"https://storage.googleapis.com/storage/v1/b/{bucket}",
        headers=api_headers(token, project_id),
    )
    if r.status_code == 200:
        print(f"  [OK] GCS bucket exists: gs://{bucket}")
        return
    r = requests.post(
        f"https://storage.googleapis.com/storage/v1/b?project={project_id}",
        headers=api_headers(token, project_id),
        json={"name": bucket, "location": location, "iamConfiguration": {"uniformBucketLevelAccess": {"enabled": True}}},
    )
    r.raise_for_status()
    print(f"  [CREATED] GCS bucket: gs://{bucket} ({location})")


def upload_file_gcs(token: str, project_id: str, bucket: str, local_path: Path, object_name: str):
    ctype, _ = mimetypes.guess_type(str(local_path))
    if local_path.suffix == ".xlsx":
        ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif local_path.suffix == ".html":
        ctype = "text/html; charset=utf-8"
    elif local_path.suffix == ".csv":
        ctype = "text/csv; charset=utf-8"
    else:
        ctype = ctype or "application/octet-stream"

    encoded = urllib.parse.quote(object_name, safe="")
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o?uploadType=media&name={encoded}"
    r = requests.post(url, headers=api_headers(token, project_id, content_type=ctype), data=local_path.read_bytes())
    r.raise_for_status()


def ensure_bq_dataset(token: str, project_id: str, dataset_id: str, location: str = "US"):
    r = requests.get(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}",
        headers=api_headers(token, project_id),
    )
    if r.status_code == 200:
        print(f"  [OK] BigQuery dataset exists: {project_id}.{dataset_id}")
        return
    r = requests.post(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets",
        headers=api_headers(token, project_id),
        json={
            "datasetReference": {"projectId": project_id, "datasetId": dataset_id},
            "location": location,
            "description": "Cymbal Beauty & Living — Gemini Enterprise & Antigravity Demo Lab Dataset",
        },
    )
    r.raise_for_status()
    print(f"  [CREATED] BigQuery dataset: {project_id}.{dataset_id} ({location})")


def load_bq_table(token: str, project_id: str, dataset_id: str, table_id: str, gcs_uri: str, location: str = "US"):
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/jobs"
    body = {
        "configuration": {
            "load": {
                "sourceUris": [gcs_uri],
                "destinationTable": {"projectId": project_id, "datasetId": dataset_id, "tableId": table_id},
                "sourceFormat": "CSV",
                "skipLeadingRows": 1,
                "autodetect": True,
                "writeDisposition": "WRITE_TRUNCATE",
                "encoding": "UTF-8",
            }
        },
        "jobReference": {"location": location},
    }
    r = requests.post(url, headers=api_headers(token, project_id), json=body)
    r.raise_for_status()
    job_id = r.json()["jobReference"]["jobId"]

    for _ in range(60):
        jr = requests.get(
            f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/jobs/{job_id}?location={location}",
            headers=api_headers(token, project_id),
        )
        jr.raise_for_status()
        jdata = jr.json()
        if jdata.get("status", {}).get("state") == "DONE":
            err = jdata.get("status", {}).get("errorResult")
            if err:
                raise RuntimeError(f"BQ load failed for {table_id}: {err}")
            rows = jdata.get("statistics", {}).get("load", {}).get("outputRows", "?")
            print(f"  [LOADED] {dataset_id}.{table_id}: {rows} rows")
            return
        time.sleep(2)
    raise TimeoutError(f"BQ load job timed out: {table_id}")


def ensure_datastore(token: str, project_id: str, location: str, ds_id: str, display_name: str, content_config: str):
    base = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection"
    r = requests.get(f"{base}/dataStores/{ds_id}", headers=api_headers(token, project_id))
    if r.status_code == 200:
        print(f"  [OK] DataStore exists: {ds_id}")
        return

    payload = {
        "displayName": display_name,
        "industryVertical": "GENERIC",
        "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
        "contentConfig": content_config,
    }
    if content_config == "CONTENT_REQUIRED":
        payload["documentProcessingConfig"] = {
            "defaultParsingConfig": {"digitalParsingConfig": {}},
            "chunkingConfig": {"layoutBasedChunkingConfig": {"chunkSize": 500, "includeAncestorHeadings": True}},
        }

    r = requests.post(f"{base}/dataStores?dataStoreId={ds_id}", headers=api_headers(token, project_id), json=payload)
    if r.status_code == 409:
        print(f"  [OK] DataStore already exists: {ds_id}")
        return
    if not r.ok:
        raise RuntimeError(f"Create DataStore {ds_id} failed ({r.status_code}): {r.text}")
    op = r.json()
    if "/operations/" in op.get("name", "") and not op.get("done"):
        poll_operation(token, project_id, location, op["name"], timeout_sec=180)
    print(f"  [CREATED] DataStore: {ds_id} ({content_config})")


def import_to_datastore(token: str, project_id: str, location: str, ds_id: str, body: dict) -> str:
    base = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection"
    url = f"{base}/dataStores/{ds_id}/branches/0/documents:import"
    r = requests.post(url, headers=api_headers(token, project_id), json=body)
    if not r.ok:
        raise RuntimeError(f"Import to {ds_id} failed ({r.status_code}): {r.text}")
    op_name = r.json().get("name", "")
    print(f"  [IMPORT STARTED] {ds_id} -> {op_name}")
    return op_name


def attach_datastores_to_engine(token: str, project_id: str, location: str, engine_id: str, ds_ids: list[str]):
    base = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection"
    r = requests.get(f"{base}/engines/{engine_id}", headers=api_headers(token, project_id))
    r.raise_for_status()
    existing = r.json().get("dataStoreIds", [])
    merged = list(dict.fromkeys(existing + ds_ids))

    pr = requests.patch(
        f"{base}/engines/{engine_id}?updateMask=dataStoreIds",
        headers=api_headers(token, project_id),
        json={"dataStoreIds": merged},
    )
    if pr.ok:
        op = pr.json()
        if "/operations/" in op.get("name", "") and not op.get("done"):
            poll_operation(token, project_id, location, op["name"], timeout_sec=180)
        print(f"  [ATTACHED] Engine {engine_id} now has dataStoreIds: {merged}")
        return
    raise RuntimeError(f"Failed attaching DataStores to Engine ({pr.status_code}): {pr.text[:300]}")


def main():
    env = load_env()
    project_id = env["PROJECT_ID"]
    ge_location = env["GE_LOCATION"]
    engine_id = env["GE_ENGINE_ID"]
    bucket = env["GCS_BUCKET"]
    bq_dataset = env["BQ_DATASET"]
    bq_location = env["BQ_LOCATION"]
    prefix = env["DS_PREFIX"]

    token = get_access_token()
    print(f"Target Project: {project_id} | Engine: {engine_id} ({ge_location})")

    print("\n[Step 1/5] Provisioning GCS bucket and uploading scenario docs & CSVs...")
    ensure_gcs_bucket(token, project_id, bucket, location=bq_location)
    docs_root = ROOT_DIR / "generated_data" / "docs"
    csv_root = ROOT_DIR / "generated_data" / "csv"
    if not docs_root.exists() or not csv_root.exists():
        raise RuntimeError("Generated data missing. Run scripts/01_generate_data.sh first.")

    for doc_file in sorted(docs_root.rglob("*")):
        if doc_file.is_file():
            rel = doc_file.relative_to(docs_root).as_posix()
            upload_file_gcs(token, project_id, bucket, doc_file, rel)
            print(f"  [UPLOADED] gs://{bucket}/{rel}")

    csv_files = sorted(csv_root.glob("*.csv"))
    for csv_file in csv_files:
        upload_file_gcs(token, project_id, bucket, csv_file, f"bq_staging/{csv_file.name}")

    print("\n[Step 2/5] Provisioning BigQuery dataset and loading 4 tables...")
    ensure_bq_dataset(token, project_id, bq_dataset, location=bq_location)
    for csv_file in csv_files:
        load_bq_table(token, project_id, bq_dataset, csv_file.stem, f"gs://{bucket}/bq_staging/{csv_file.name}", location=bq_location)

    print("\n[Step 3/5] Creating 5 Discovery Engine 1P DataStores...")
    datastores = [
        (f"{prefix}-ad-compliance", "CBL 표시·광고 검수 가이드 & 심의사례 (GCS)", "CONTENT_REQUIRED", {
            "gcsSource": {"inputUris": [f"gs://{bucket}/scenario1_ad_compliance/*"], "dataSchema": "content"},
            "reconciliationMode": "FULL",
        }),
        (f"{prefix}-sales-policy", "CBL 채널 프로모션 정책 & 안전재고 매뉴얼 (GCS)", "CONTENT_REQUIRED", {
            "gcsSource": {"inputUris": [f"gs://{bucket}/scenario2_sales_promo/*"], "dataSchema": "content"},
            "reconciliationMode": "FULL",
        }),
        (f"{prefix}-voc-sop", "CBL VOC·품질클레임 대응 SOP & 보상기준 (GCS)", "CONTENT_REQUIRED", {
            "gcsSource": {"inputUris": [f"gs://{bucket}/scenario3_voc_qa/*"], "dataSchema": "content"},
            "reconciliationMode": "FULL",
        }),
        (f"{prefix}-bq-sales-inventory", "CBL 채널별 매출·재고 실적 (BigQuery)", "NO_CONTENT", {
            "bigquerySource": {
                "projectId": project_id,
                "datasetId": bq_dataset,
                "tableId": "channel_sales_inventory",
                "dataSchema": "custom",
            },
            "autoGenerateIds": True,
            "reconciliationMode": "FULL",
        }),
        (f"{prefix}-bq-voc-claims", "CBL 고객 VOC·품질 클레임 이력 (BigQuery)", "NO_CONTENT", {
            "bigquerySource": {
                "projectId": project_id,
                "datasetId": bq_dataset,
                "tableId": "voc_quality_claims",
                "dataSchema": "custom",
            },
            "autoGenerateIds": True,
            "reconciliationMode": "FULL",
        }),
    ]

    for ds_id, display_name, content_config, _ in datastores:
        ensure_datastore(token, project_id, ge_location, ds_id, display_name, content_config)

    print("\n[Step 4/5] Importing documents & BigQuery tables into 1P DataStores...")
    ops = []
    for ds_id, _, _, import_body in datastores:
        op_name = import_to_datastore(token, project_id, ge_location, ds_id, import_body)
        if op_name:
            ops.append((ds_id, op_name))

    print("\n[Step 5/5] Attaching all 5 DataStores to GE Engine...")
    attach_datastores_to_engine(token, project_id, ge_location, engine_id, [d[0] for d in datastores])

    print("\nWaiting for DataStore import operations to finish (up to 5 min)...")
    for ds_id, op_name in ops:
        try:
            res = poll_operation(token, project_id, ge_location, op_name, timeout_sec=300)
            meta = res.get("metadata", {})
            print(f"  [IMPORT DONE] {ds_id}: success={meta.get('successCount', '?')}, failure={meta.get('failureCount', 0)}")
        except Exception as e:
            print(f"  [IMPORT IN BACKGROUND] {ds_id}: {e}")

    print("\n1P DataStore provisioning complete!")


if __name__ == "__main__":
    main()
