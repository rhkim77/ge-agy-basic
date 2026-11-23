# Task 01: 중규모 가상 데이터 생성 및 GCS / BigQuery 적재

Beauty · HDB · Refreshment 소비재 기업(`Cymbal Beauty & Living`)의 3가지 현업 시나리오를 검증할 수 있도록 **중규모 정형 Dataset**(`BigQuery` 4개 Table, 총 6,460 Row)과 **비정형 규정·SOP·사례집 문서**(`Cloud Storage` 9종 Semantic HTML)를 생성해 Google Cloud에 적재합니다.

---

## 1. 로컬에서 가상 데이터 생성하기 (공통 1회 실행)

별도의 외부 `pip` Package 설치 없이 Python 표준 Library만으로 모든 CSV 및 Semantic HTML 문서 File이 `generated_data/` Directory 아래에 생성됩니다.

```bash
bash scripts/01_generate_data.sh
```

### 생성되는 데이터 자산 명세

| 구분 | File / Folder | 건수 | 핵심 시나리오 데이터 (`Hero Records`) |
|---|---|---|---|
| **BigQuery** | `products_master.csv` | 120 rows | 루미에르(`SKU-LUMI-001`), 베르당(`SKU-VERD-004`), 더마퓨어(`SKU-DERM-002`), 루트케어(`SKU-ROOT-001`) 등 10개 브랜드 마스터 |
| **BigQuery** | `channel_sales_inventory.csv` | 3,600 rows | 120일 × 30 SKU-채널 일별 실적. 루미에르 면세점 재고 `42/200`(**긴급발주필요**), 베르당 H&B스토어 정기세일 급증 및 재고 `85/300`(**긴급발주필요**) |
| **BigQuery** | `promotions_calendar.csv` | 240 rows | `PRM-2026-001`(베르당 정기세일 ROI `312.5%`), `PRM-2026-002`(루미에르 면세점 ROI `118.4%`: 최소 목표 `150%` 미달) |
| **BigQuery** | `voc_quality_claims.csv` | 2,500 rows | 루트케어 `LOT-202610-D01` 펌프 누액 **18건** 집중 발생, 더마퓨어 `LOT-202610-P02` 피부트러블 **12건** 집중 발생 |
| **GCS Docs** | `scenario1_ad_compliance/` | 3 HTML files | 화장품 표시·광고 실무 가이드라인(`RA-AD-2026-01`), 브랜드별 카피 검수기준서, 과거 심의사례 40건 이력표(`REV-2026`) |
| **GCS Docs** | `scenario2_sales_promo/` | 3 HTML files | 채널별 프로모션 운영정책서(`SLS-PRM-2026-H2`), 안전재고·긴급발주 매뉴얼(`SCM-INV-2026-04`), Q4 핵심브랜드 운영브리프 |
| **GCS Docs** | `scenario3_voc_qa/` | 3 HTML files | 품질클레임 등급별 대응 SOP(`QA-SOP-2026-03`), 보상기준표·응대안내문, 주요제품 성분·알레르기 FAQ |
| **Antigravity** | `agy_workspace/samples/campaign_copies_draft.csv` | 8 rows | `Task 05` `Antigravity` 배치 검수 실습용 신제품 마케팅 카피 시안 |

---

## 2. Cloud 적재: Track A (Console UI) vs Track B (Script)

두 경로 중 편한 방식을 골라 `Cloud Storage`와 `BigQuery`에 데이터를 올립니다. `Track B`의 `02_provision_1p_datastores.py`를 실행하면 이번 적재 단계와 `Task 02`의 `DataStore` 생성까지 한 번에 끝납니다.

### Track A: Google Cloud Console UI 과정

#### 1) Cloud Storage Bucket 생성 및 문서 업로드

1. `GCP Console > Cloud Storage > Buckets`로 이동해 `+ CREATE`를 클릭합니다.
2. `Bucket` 이름에 `<PROJECT_ID>-cbl-ge-demo`를 입력한 뒤 `Location type`에서 `Multi-region`(`us`)을 선택합니다.
3. `Access control`은 기본값(`Uniform`)으로 두고 `CREATE`를 누릅니다.
4. 생성된 `Bucket` 상세 화면에서 `UPLOAD FOLDER`를 클릭해 로컬 `generated_data/docs/` 안의 세 Folder(`scenario1_ad_compliance`, `scenario2_sales_promo`, `scenario3_voc_qa`)를 그대로 업로드합니다.

#### 2) BigQuery Dataset 및 4개 Table 생성

1. `GCP Console > BigQuery > Studio`로 이동합니다.
2. 좌측 `Explorer`에서 대상 `Project` 우측의 점 3개 Menu(`⋮`)를 눌러 `Create dataset`을 선택합니다.
3. `Dataset ID`에 `cbl_ge_demo`, `Data location`에 `US (multiple regions in United States)`를 지정하고 `CREATE DATASET`을 클릭합니다.
4. 생성된 `cbl_ge_demo` 옆 Menu(`⋮`)에서 `Create table`을 선택해 `generated_data/csv/` 안의 4개 CSV File을 순서대로 적재합니다.
   - `Create table from`: `Upload` 선택 후 CSV File 지정 (`File format`: `CSV`)
   - `Table` 이름: `products_master`, `channel_sales_inventory`, `promotions_calendar`, `voc_quality_claims`
   - `Schema`: `Auto detect` 체크, `Advanced options > Header rows to skip`: `1` 입력 후 `CREATE TABLE` 클릭
5. 적재가 끝나면 각 `Table`의 `Preview` Tab에서 전체 Row 수(`120`, `3,600`, `240`, `2,500`)가 일치하는지 확인합니다.

---

### Track B: CLI / Script 자동화 과정

`gcloud storage` CLI 명령어나 `Task 02` 통합 Python `Script`로 동일하게 적재할 수 있습니다.

```bash
source .env
BUCKET="${GCS_BUCKET:-${PROJECT_ID}-cbl-ge-demo}"

# GCS Bucket 생성 및 문서 업로드
gcloud storage buckets create "gs://${BUCKET}" --project="${PROJECT_ID}" --location="${BQ_LOCATION}" --uniform-bucket-level-access || true
gcloud storage cp -r generated_data/docs/* "gs://${BUCKET}/" --project="${PROJECT_ID}"

# (권장: 아래 통합 Script 실행 시 GCS + BigQuery 적재와 1P DataStore 5종 생성까지 일괄 수행됩니다)
python3 scripts/02_provision_1p_datastores.py
```

다음 단계: [Task 02: GCS & BigQuery 1P DataStore 구축 및 GE App 연결](task02_1p_datastores.md)
