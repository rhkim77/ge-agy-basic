#!/usr/bin/env python3
"""Task 05: End-to-End verification across 1P DataStores, GE Agents/StreamAssist, Custom IAM Role, and Antigravity Workspace."""

import subprocess
import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT_DIR, api_headers, de_base, get_access_token, load_env


def test_search(token: str, project_id: str, location: str, ds_id: str, query: str):
    url = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{ds_id}/servingConfigs/default_search:search"
    r = requests.post(url, headers=api_headers(token, project_id), json={"query": query, "pageSize": 3})
    if not r.ok:
        print(f"  [FAIL] {ds_id} ({r.status_code}): {r.text[:200]}")
        return False
    results = r.json().get("results", [])
    total = r.json().get("totalSize", len(results))
    print(f"  [OK] {ds_id} | query='{query}' -> totalSize={total}, hits={len(results)}")
    return len(results) > 0


def test_stream_assist(token: str, project_id: str, location: str, engine_id: str, query: str, ds_ids: list[str]):
    url = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/assistants/default_assistant:streamAssist"
    specs = [{"dataStore": f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{d}"} for d in ds_ids]
    r = requests.post(
        url,
        headers=api_headers(token, project_id),
        json={"query": {"text": query}, "toolsSpec": {"vertexAiSearchSpec": {"dataStoreSpecs": specs}}},
        timeout=90,
    )
    if not r.ok:
        print(f"  [FAIL] streamAssist ({r.status_code}): {r.text[:200]}")
        return False
    chunks = r.json()
    text_parts = []
    for chunk in chunks if isinstance(chunks, list) else [chunks]:
        for reply in chunk.get("answer", {}).get("replies", []):
            content = reply.get("groundedContent", {}).get("content", {})
            if content.get("text") and not content.get("thought"):
                text_parts.append(content["text"])
    answer = "".join(text_parts).strip()
    print(f"  [ASSIST OK] ({len(answer)} chars) {answer[:220].replace(chr(10), ' ')}...")
    return bool(answer)


def main():
    env = load_env()
    project_id = env["PROJECT_ID"]
    location = env["GE_LOCATION"]
    engine_id = env["GE_ENGINE_ID"]
    prefix = env["DS_PREFIX"]
    token = get_access_token()

    print("=== [1/4] 1P DataStore Search Verification ===")
    for ds_id, q in [
        (f"{prefix}-ad-compliance", "더마퓨어 아토피 치료 금지 표현 대체어"),
        (f"{prefix}-sales-policy", "루미에르 면세점 ROI 150 긴급발주 안전재고"),
        (f"{prefix}-voc-sop", "동일 Lot 10건 이상 P1 긴급 품질위원회"),
        (f"{prefix}-bq-sales-inventory", "SKU-VERD-004 H&B스토어 긴급발주필요"),
        (f"{prefix}-bq-voc-claims", "LOT-202610-D01 루트케어 용기파손"),
    ]:
        test_search(token, project_id, location, ds_id, q)

    print("\n=== [2/4] Registered GE Agents Verification ===")
    ar = requests.get(
        f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/assistants/default_assistant/agents",
        headers=api_headers(token, project_id),
    )
    if ar.ok:
        for a in ar.json().get("agents", []):
            print(f"  [AGENT] {a.get('displayName')} -> {a.get('name', '').split('/')[-1]} ({a.get('state')})")

    print("\n=== [3/4] Grounded StreamAssist 3-Scenario Verification ===")
    for q, ds_list in [
        (
            "더마퓨어 광고 문구로 '아토피를 완벽하게 치료하는 저자극 크림'을 쓰려고 하는데 사내 표시광고 가이드라인 기준 위반 여부와 대체 문구를 알려줘.",
            [f"{prefix}-ad-compliance"],
        ),
        (
            "루미에르 로얄 리페어 에센스(SKU-LUMI-001) 면세점 현황과 베르당 아쿠아 밤(SKU-VERD-004) H&B스토어 재고 리스크를 프로모션 정책 및 안전재고 매뉴얼 기준으로 요약해줘.",
            [f"{prefix}-sales-policy", f"{prefix}-bq-sales-inventory"],
        ),
        (
            "루트케어 샴푸 제조번호 LOT-202610-D01 펌프 누액 클레임이 또 접수됐어. 누적 이력과 사내 대응 SOP 기준으로 P1 격상 여부와 대응 절차를 알려줘.",
            [f"{prefix}-voc-sop", f"{prefix}-bq-voc-claims"],
        ),
    ]:
        test_stream_assist(token, project_id, location, engine_id, q, ds_list)

    print("\n=== [4/4] Antigravity Custom IAM Role & Batch Validator Verification ===")
    rr = requests.get(f"https://iam.googleapis.com/v1/projects/{project_id}/roles/geStandardChatUser", headers=api_headers(token, project_id))
    if rr.ok:
        perms = rr.json().get("includedPermissions", [])
        agy_leaks = [p for p in perms if p.startswith("businessaicode.")]
        print(f"  [IAM OK] geStandardChatUser permissions={len(perms)}, businessaicode.* leaks={len(agy_leaks)}")
    else:
        print(f"  [WARN] geStandardChatUser role check returned {rr.status_code}")

    res = subprocess.run(["python3", str(ROOT_DIR / "agy_workspace" / "samples" / "batch_copy_validator.py")], capture_output=True, text=True, check=True)
    print("  [AGY SAMPLE OK]", res.stdout.strip().replace("\n", " "))


if __name__ == "__main__":
    main()
