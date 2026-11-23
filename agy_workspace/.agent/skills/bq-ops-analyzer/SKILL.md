---
name: bq-ops-analyzer
description: Queries the Cymbal Beauty & Living BigQuery dataset (cbl_ge_demo) to detect channel inventory stock-out risks, low-ROI promotions, and P1 same-Lot VOC clusters. Use when analyzing sales, inventory, promotions, or VOC claims in Antigravity.
---

# BigQuery Sales, Inventory & VOC Operations Analyzer Skill

## Standard Read-Only Diagnostic Queries
1. **긴급발주필요 SKU 탐지 (`SCM-INV-2026-04`)**
   - `channel_sales_inventory` Table에서 최신 일자(`MAX(sales_date)`) 기준 `ending_stock_qty < safety_stock_qty * 0.5`인 SKU·채널 목록을 조회한 뒤 `promotions_calendar`의 `actual_roi_pct`와 `JOIN`합니다.
2. **동일 Lot 집중 클레임 탐지 (`QA-SOP-2026-03`)**
   - `voc_quality_claims` Table에서 `GROUP BY sku_id, brand, lot_number, claim_type HAVING COUNT(*) >= 10` 조건으로 P1 자동 격상 대상 Lot를 추출합니다.
