#!/usr/bin/env python3
"""Task 03: Enable Agent Designer features and deploy 3 Cymbal Beauty & Living Low-Code / Workflow Agents."""

import json
import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import api_headers, de_base, get_access_token, load_env


def ds_resource(project_id: str, location: str, ds_id: str) -> str:
    return f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{ds_id}"


def build_agent_payloads(project_id: str, location: str, prefix: str) -> list[dict]:
    model_name = "gemini-2.5-flash"

    ds_ad = ds_resource(project_id, location, f"{prefix}-ad-compliance")
    ds_sales_pol = ds_resource(project_id, location, f"{prefix}-sales-policy")
    ds_sales_bq = ds_resource(project_id, location, f"{prefix}-bq-sales-inventory")
    ds_voc_sop = ds_resource(project_id, location, f"{prefix}-voc-sop")
    ds_voc_bq = ds_resource(project_id, location, f"{prefix}-bq-voc-claims")

    s1_nodes = [
        {
            "id": "root_seq",
            "displayName": "표시·광고 사전검토 Workflow",
            "sequentialAgentNode": {
                "description": "광고 카피 위반 진단 후 대체 카피 및 RA 심의요청서를 순차 생성합니다.",
                "subAgentIds": ["step1_audit", "step2_rewrite"],
            },
        },
        {
            "id": "step1_audit",
            "displayName": "1단계: 규정 및 반려사례 대조",
            "llmAgentNode": {
                "description": "사내 표시·광고 가이드라인과 과거 심의사례를 검색해 위반 소지를 진단합니다.",
                "model": model_name,
                "instruction": (
                    "당신은 Cymbal Beauty & Living RA팀 표시·광고 검수 전문가입니다. "
                    "사용자가 입력한 화장품 광고 카피를 반드시 연결된 DataStore(RA-AD-2026-01, MKT-COPY-2026-02, 과거 심의사례집)와 대조하여 "
                    "(1) 종합 판정(승인/조건부승인/반려), (2) 위험 표현별 위반 사유 및 화장품법 행정처분 리스크, (3) 유사 과거 반려 사례(REV-2026-XXX)를 구조화해 분석하세요."
                ),
                "dataStoreSpecs": {"specs": [{"dataStore": ds_ad}]},
                "googleSearchDisabled": True,
            },
        },
        {
            "id": "step2_rewrite",
            "displayName": "2단계: 대체 카피 및 RA 검토요청서 작성",
            "llmAgentNode": {
                "description": "1단계 진단 결과를 바탕으로 가이드라인 준수 대체 카피 2안과 RA 사전심의 요청서 초안을 작성합니다.",
                "model": model_name,
                "instruction": (
                    "1단계의 위반 진단 결과를 바탕으로 (1) 브랜드 톤앤매너를 유지하면서도 규정을 100% 준수하는 대체 카피 2안, "
                    "(2) 인체적용시험 수치 표기 시 필수 각주 4대 요건 체크리스트, (3) RA팀 제출용 사전심의 요청서 초안을 간결하게 작성하세요."
                ),
                "googleSearchDisabled": True,
            },
        },
    ]

    s2_nodes = [
        {
            "id": "root_sales",
            "displayName": "브랜드·채널 실적 및 재고 분석",
            "llmAgentNode": {
                "description": "BigQuery 채널별 매출·재고 실적과 GCS 프로모션 정책·안전재고 매뉴얼을 교차 분석합니다.",
                "model": model_name,
                "instruction": (
                    "당신은 Cymbal Beauty & Living 사업부 영업기획 및 SCM 분석 전문 Agent입니다. "
                    "반드시 BigQuery 실적 DataStore(SKU별 매출·재고·안전재고)와 GCS 정책 DataStore(채널별 할인 상한·최소 목표 ROI·안전재고 50% 미만 긴급발주 트리거)를 교차 인용해 답변하세요. "
                    "답변은 [핵심 요약] -> [정량 지표 표] -> [정책 기준 대비 판정] -> [권고 SCM/영업 액션 및 승인권자] 순서로 작성하세요."
                ),
                "dataStoreSpecs": {"specs": [{"dataStore": ds_sales_bq}, {"dataStore": ds_sales_pol}]},
                "googleSearchDisabled": True,
            },
        }
    ]

    s3_nodes = [
        {
            "id": "root_voc_seq",
            "displayName": "VOC·품질 클레임 대응 Workflow",
            "sequentialAgentNode": {
                "description": "동일 Lot 누적 이력 조회 및 SOP P1 판정 후 고객 회신 초안과 품질위원회 보고서를 순차 생성합니다.",
                "subAgentIds": ["step1_triage", "step2_draft"],
            },
        },
        {
            "id": "step1_triage",
            "displayName": "1단계: Lot 누적 이력 및 SOP 등급 판정",
            "llmAgentNode": {
                "description": "BigQuery VOC 이력과 GCS 대응 SOP를 조회해 P1/P2/P3 심각도 및 에스컬레이션 여부를 판정합니다.",
                "model": model_name,
                "instruction": (
                    "당신은 Cymbal Beauty & Living CS·품질보증(QA) 트리아지 전문가입니다. "
                    "입력된 제품/Lot 번호의 BigQuery 클레임 누적 건수와 GCS 대응 SOP(QA-SOP-2026-03: 동일 Lot 최근 30일 10건 이상 누적 시 P1-긴급 자동 격상, 출고 보류 및 품질위원회 보고) 및 보상기준표를 대조하여 "
                    "심각도 등급(P1/P2/P3), 누적 건수, 초동 SLA, 적용 보상 한도 및 필수 증빙서류를 정리하세요."
                ),
                "dataStoreSpecs": {"specs": [{"dataStore": ds_voc_bq}, {"dataStore": ds_voc_sop}]},
                "googleSearchDisabled": True,
            },
        },
        {
            "id": "step2_draft",
            "displayName": "2단계: 고객 회신 초안 및 QA 보고서 작성",
            "llmAgentNode": {
                "description": "트리아지 결과를 바탕으로 고객 발송용 회신 초안과 P1 품질위원회 긴급 보고서를 작성합니다.",
                "model": model_name,
                "instruction": (
                    "1단계 트리아지 결과를 바탕으로 (1) 정중하고 명확한 고객 발송용 회신 초안(환불/교환/진료비 지원 및 필요 서류 안내 포함), "
                    "(2) P1-긴급 해당 시 품질위원회·QA팀장 제출용 긴급 에스컬레이션 보고서(Lot 출고 보류 및 라인 점검 요청 포함)를 작성하세요."
                ),
                "googleSearchDisabled": True,
            },
        },
    ]

    return [
        {
            "displayName": "CBL 표시·광고 문구 사전검토 Workflow",
            "description": "화장품 광고 카피를 사내 표시·광고 가이드라인 및 과거 심의사례와 대조해 위반 진단·대체 카피·RA 검토요청서를 순차 생성하는 Workflow Agent",
            "lowCodeAgentDefinition": {
                "draftDisplayName": "CBL 표시·광고 문구 사전검토 Workflow",
                "draftDescription": "화장품 광고 카피 위반 진단 및 대체 카피 생성 Workflow",
                "rootAgentId": "root_seq",
                "nodes": s1_nodes,
                "deployedRootAgentId": "root_seq",
                "deployedNodes": s1_nodes,
                "draftStarterPrompts": [
                    {"text": "더마퓨어 H&B스토어 상세페이지 카피 '아토피와 피부염을 완벽하게 치료하고 부작용 제로인 저자극 크림' 검수해줘."},
                    {"text": "베르당 아쿠아 밤 '단 1회 사용으로 보습력 145% 개선' 카피에 필요한 실증 각주 4대 요건 확인해줘."},
                ],
            },
            "sharingConfig": {"scope": "ALL_USERS"},
            "observabilityConfig": {"observabilityEnabled": True},
        },
        {
            "displayName": "CBL 브랜드·채널 실적 및 재고 분석 Agent",
            "description": "BigQuery 매출·재고 실적과 GCS 프로모션 정책·안전재고 매뉴얼을 교차 분석해 이상 징후 및 SCM 긴급발주 브리프를 제공하는 Agent",
            "lowCodeAgentDefinition": {
                "draftDisplayName": "CBL 브랜드·채널 실적 및 재고 분석 Agent",
                "draftDescription": "브랜드·채널별 매출/재고 이상 탐지 및 프로모션 정책 대조 분석",
                "rootAgentId": "root_sales",
                "nodes": s2_nodes,
                "deployedRootAgentId": "root_sales",
                "deployedNodes": s2_nodes,
                "draftStarterPrompts": [
                    {"text": "루미에르 로얄 리페어 에센스(SKU-LUMI-001) 면세점 현황을 프로모션 정책과 안전재고 매뉴얼 기준으로 진단해줘."},
                    {"text": "베르당 아쿠아 밤(SKU-VERD-004) H&B스토어 재고 리스크와 긴급 SCM 액션을 요약해줘."},
                ],
            },
            "sharingConfig": {"scope": "ALL_USERS"},
            "observabilityConfig": {"observabilityEnabled": True},
        },
        {
            "displayName": "CBL VOC·품질 클레임 대응 Workflow",
            "description": "신규 클레임의 Lot 누적 이력과 대응 SOP·보상기준표를 조회해 P1 격상 판정, 고객 회신 초안, 품질위원회 보고서를 순차 생성하는 Workflow Agent",
            "lowCodeAgentDefinition": {
                "draftDisplayName": "CBL VOC·품질 클레임 대응 Workflow",
                "draftDescription": "동일 Lot 누적 VOC 트리아지 및 고객 회신·QA 보고서 생성 Workflow",
                "rootAgentId": "root_voc_seq",
                "nodes": s3_nodes,
                "deployedRootAgentId": "root_voc_seq",
                "deployedNodes": s3_nodes,
                "draftStarterPrompts": [
                    {"text": "루트케어 샴푸(SKU-ROOT-001) LOT-202610-D01 펌프 누액 클레임이 또 접수됐어. P1 격상 여부와 대응안 작성해줘."},
                    {"text": "더마퓨어 크림(LOT-202610-P02) 피부과 진료 클레임 보상 한도와 고객 회신 초안 만들어줘."},
                ],
            },
            "sharingConfig": {"scope": "ALL_USERS"},
            "observabilityConfig": {"observabilityEnabled": True},
        },
    ]


def main():
    env = load_env()
    project_id = env["PROJECT_ID"]
    location = env["GE_LOCATION"]
    engine_id = env["GE_ENGINE_ID"]
    prefix = env["DS_PREFIX"]
    token = get_access_token()

    base = f"{de_base(location)}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection"

    print(f"[Step 1/3] Enabling Agent Designer & Canvas features on Engine {engine_id}...")
    er = requests.get(f"{base}/engines/{engine_id}", headers=api_headers(token, project_id))
    er.raise_for_status()
    features = dict(er.json().get("features", {}))
    features["workflow-agents"] = "FEATURE_STATE_ON"
    features["no-code-agent-builder"] = "FEATURE_STATE_ON"
    features["disable-canvas"] = "FEATURE_STATE_OFF"
    pr = requests.patch(
        f"{base}/engines/{engine_id}?updateMask=features",
        headers=api_headers(token, project_id),
        json={"features": features},
    )
    if pr.ok:
        print("  [OK] Enabled workflow-agents, no-code-agent-builder, and Canvas (disable-canvas=OFF).")
    else:
        print(f"  [WARN] Feature update returned {pr.status_code}: {pr.text[:200]}")

    agents_url = f"{base}/engines/{engine_id}/assistants/default_assistant/agents"
    print("\n[Step 2/3] Checking existing Agents on default_assistant...")
    r = requests.get(agents_url, headers=api_headers(token, project_id))
    r.raise_for_status()
    existing_by_name = {a.get("displayName"): a.get("name") for a in r.json().get("agents", [])}
    print("  Existing:", list(existing_by_name.keys()))

    print("\n[Step 3/3] Creating 3 Cymbal Beauty & Living Low-Code / Workflow Agents...")
    for payload in build_agent_payloads(project_id, location, prefix):
        name = payload["displayName"]
        if name in existing_by_name:
            print(f"  [OK] Already exists: {name} -> {existing_by_name[name]}")
            continue
        cr = requests.post(agents_url, headers=api_headers(token, project_id), json=payload)
        if cr.ok:
            created = cr.json()
            print(f"  [CREATED] {name} -> {created.get('name')} (state={created.get('state')})")
        else:
            raise RuntimeError(f"Create Agent '{name}' failed ({cr.status_code}): {cr.text[:400]}")


if __name__ == "__main__":
    main()
