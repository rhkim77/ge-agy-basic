#!/usr/bin/env python3
"""Reference batch cosmetic ad-copy validator for Task 5 (Google Antigravity hands-on lab).

Reads `samples/campaign_copies_draft.csv`, evaluates RA-AD-2026-01 rules, and writes
`samples/output_ad_audit_report.html` + JSON summary.
"""

import csv
import html
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "campaign_copies_draft.csv"
OUTPUT_HTML = BASE_DIR / "output_ad_audit_report.html"

PROHIBITED_RULES = [
    (r"아토피|피부염|여드름|지루성", "질병명 직접 언급 및 의약품 오인 (화장품법 제13조)"),
    (r"치료|완치|세포\s*재생|모근\s*재생|발모|새로\s*자라는|스테로이드\s*대체", "의약품 치료·발모·재생 효능 표방 금지"),
    (r"100%|부작용\s*제로|기적의|완벽\s*예방|영구적", "배타적·절대적 과장 표현 금지"),
    (r"전문의\s*지정|전문의\s*추천|의사\s*추천", "의료인 지정·추천 표현 금지"),
]

NUMERIC_CLAIM_RE = re.compile(r"(\d+%\s*개선|\d+시간)")


def evaluate_copy(row: dict) -> dict:
    text = row["draft_copy"]
    has_fn = row.get("has_clinical_footnote", "N").upper() == "Y"
    reasons = [desc for pat, desc in PROHIBITED_RULES if re.search(pat, text)]

    if reasons:
        verdict = "REJECT (반려)"
    elif NUMERIC_CLAIM_RE.search(text) and not has_fn:
        verdict = "CONDITIONAL (조건부승인)"
        reasons.append("정량 효능 수치 포함 — 인체적용시험 4대 각주(기관·기간·인원·개인차) 보완 필수")
    else:
        verdict = "PASS (승인)"
        reasons.append("화장품 표시·광고 가이드라인 적합")

    return {
        **row,
        "verdict": verdict,
        "reasons": "; ".join(reasons),
    }


def main():
    if "--stdio-check" in sys.argv:
        print(json.dumps({"status": "ok", "tool": "local-copy-auditor"}))
        return

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing {INPUT_CSV}. Run scripts/01_generate_data.sh first.")

    with INPUT_CSV.open(encoding="utf-8") as f:
        results = [evaluate_copy(r) for r in csv.DictReader(f)]

    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    rows_html = []
    for r in results:
        badge_color = "#fce8e6" if "REJECT" in r["verdict"] else ("#fef7e0" if "CONDITIONAL" in r["verdict"] else "#e6f4ea")
        rows_html.append(
            f"<tr><td>{html.escape(r['copy_id'])}</td>"
            f"<td>{html.escape(r['brand'])}</td>"
            f"<td>{html.escape(r['channel'])}</td>"
            f"<td>{html.escape(r['draft_copy'])}</td>"
            f"<td style='background:{badge_color};font-weight:bold'>{html.escape(r['verdict'])}</td>"
            f"<td>{html.escape(r['reasons'])}</td></tr>"
        )

    doc = (
        "<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'>"
        "<title>Cymbal Beauty & Living — Batch Ad-Copy Audit Report</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:1040px;margin:24px auto;color:#202124}"
        "table{border-collapse:collapse;width:100%;font-size:13px}"
        "th,td{border:1px solid #dadce0;padding:8px;text-align:left}"
        "th{background:#f1f3f4}</style></head><body>"
        "<h1>Cymbal Beauty & Living — 표시·광고 배치 검수 리포트</h1>"
        f"<p>총 검수 건수: {len(results)}건 | 요약: {html.escape(json.dumps(counts, ensure_ascii=False))}</p>"
        "<table><thead><tr><th>ID</th><th>브랜드</th><th>채널</th><th>카피 시안</th><th>판정</th><th>검수 사유</th></tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table></body></html>"
    )
    OUTPUT_HTML.write_text(doc, encoding="utf-8")
    print(json.dumps({"total": len(results), "summary": counts, "report": str(OUTPUT_HTML)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
