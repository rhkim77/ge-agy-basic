---
name: ad-compliance-auditor
description: Audits cosmetic and HDB marketing campaign copies in batch against Cymbal Beauty & Living RA-AD-2026-01 compliance rules and generates an HTML audit report. Use when asked to validate, audit, or rewrite marketing copy CSV files in Antigravity.
---

# Cosmetic Ad-Copy Batch Compliance Auditor Skill

## Workflow
1. 입력 CSV(`samples/campaign_copies_draft.csv`)의 각 행(`copy_id`, `brand`, `channel`, `draft_copy`, `has_clinical_footnote`)을 읽습니다.
2. `.agent/rules/cymbal-domain-governance.md`의 금지어 사전 및 실증자료 각주 요건을 적용해 `REJECT`, `CONDITIONAL`, `PASS` 등급을 판정합니다.
3. `python3 samples/batch_copy_validator.py`를 실행하거나 확장하여 `samples/output_ad_audit_report.html` 시각 리포트를 생성하고 위반 건수 요약을 보고합니다.
