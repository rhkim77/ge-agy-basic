# Cymbal Beauty & Living: Enterprise AI Development & Data Governance Rules

이 Workspace에서 Google Antigravity (`agy`) Agent가 Code를 작성하거나 데이터를 조회할 때는 아래 3가지 거버넌스 Rule을 항상 준수해야 합니다.

## 1. 화장품 표시·광고 법규 준수 (RA-AD-2026-01)
- 화장품법 제13조 기준 질병 치료·예방 오인 Keyword(`아토피`, `피부염`, `여드름 완치`, `세포 재생`, `탈모 치료`, `발모`, `스테로이드 대체`, `피부과 전문의 지정`, `부작용 제로`, `100%`, `기적`)는 반드시 **고위험**(`REJECT`)으로 분류합니다.
- 개선율·지속시간 등 정량 수치(`145% 개선`, `48시간 지속` 등)가 포함된 문구는 인체적용시험 4대 필수 요건(시험기관명, 시험기간, 대상 인원, 개인차 있음) 각주 유무를 검증해 누락 시 **조건부승인**(`CONDITIONAL`)으로 판정합니다.

## 2. BigQuery 조회 안전 수칙 (cbl_ge_demo)
- 운영 BigQuery Dataset(`cbl_ge_demo`)에 `DROP`, `TRUNCATE`, `DELETE` Query를 절대 실행하지 않습니다. 분석 Report 작성 시에는 항상 `SELECT` 읽기 전용 Query만 수행합니다.
- 안전재고 판정 기준(`SCM-INV-2026-04`): `ending_stock_qty < safety_stock_qty * 0.5`인 품목은 **긴급발주필요**로 분류하고 48시간 이내 출고 또는 타 채널 여유 재고 전환 권고를 함께 제시합니다.

## 3. VOC 동일 Lot 자동 격상 수칙 (QA-SOP-2026-03)
- `voc_quality_claims` Table 분석 시 동일 `sku_id` 및 `lot_number`에서 최근 30일 이내 10건 이상의 클레임이 누적된 경우에는 개별 심각도와 무관하게 **P1-긴급**(품질위원회 에스컬레이션 및 물류 출고 보류) 등급으로 분류합니다.
