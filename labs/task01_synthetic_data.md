# Task 01: 중규모 가상 데이터 생성 및 `GCS` / `BigQuery` 적재

이 단계에서는 Beauty · HDB · Refreshment 소비재 기업(`Cymbal Beauty & Living`)의 3가지 현업 시나리오를 뒷받침하는 **중규모 정형 데이터(`BigQuery` 4개 `Table`, 총 6,460 `Row`)**와 **비정형 규정·SOP 문서(`Cloud Storage` 9종: `HTML` 7종 + `XLSX` 2종)**를 생성하고 클라우드에 적재합니다.

---

## 1. 로컬에서 가상 데이터 생성하기 (공통 1회 실행)

외부 `pip` 패키지 설치 없이 Python 표준 라이브러리만으로 모든 CSV, HTML, Excel(`.xlsx`) 파일이 `generated_data/` 하위에 생성됩니다.

```bash
bash scripts/01_generate_data.sh
```

### 생성되는 데이터 자산 명세

| 구분 | 파일명 / 폴더 | 건수 | 핵심 시나리오 데이터 (`Hero Records`) |
|---|---|---|---|
| **BigQuery** | `products_master.csv` | 120 rows | 루미에르(`SKU-LUMI-001`), 베르당(`SKU-VERD-004`), 더마퓨어(`SKU-DERM-002`), 루트케어(`SKU-ROOT-001`) 등 10개 브랜드 마스터 |
| **BigQuery** | `channel_sales_inventory.csv` | 3,600 rows | 120일 × 30 SKU-채널 실적. 루미에르 면세점 재고 `42/200`(**긴급발주필요**), 베르당 H&B스토어 정기세일 급증 및 재고 `85/300`(**긴급발주필요**) |
| **BigQuery** | `promotions_calendar.csv` | 240 rows | `PRM-2026-001`(베르당 정기세일 ROI `312.5%`), `PRM-2026-002`(루미에르 면세점 ROI `118.4%` — 목표 `150%` 미달) |
| **BigQuery** | `voc_quality_claims.csv` | 2,500 rows | 루트케어 `LOT-202610-D01` 펌프 누액 **18건** 집중 발생, 더마퓨어 `LOT-202610-P02` 피부트러블 **12건** 집중 발생 |
| **GCS Docs** | `scenario1_ad_compliance/` | 3 files | 화장품 표시·광고 실무 가이드라인(`RA-AD-2026-01`), 브랜드별 카피 검수기준서, 과거 심의사례 40건(`.xlsx`) |
| **GCS Docs** | `scenario2_sales_promo/` | 3 files | 채널별 프로모션 운영정책서(`SLS-PRM-2026-H2`), 안전재고·긴급발주 매뉴얼(`SCM-INV-2026-04`), Q4 핵심브랜드 운영브리프 |
| **GCS Docs** | `scenario3_voc_qa/` | 3 files | 품질클레임 등급별 대응 SOP(`QA-SOP-2026-03`), 보상기준표·응대스크립트(`.xlsx`), 주요제품 성분·알레르기 FAQ |
| **Antigravity** | `agy_workspace/samples/campaign_copies_draft.csv` | 8 rows | `Task 05` `Antigravity` 배치 검수 실습용 신제품 마케팅 카피 시안 |

---

## 2. 클라우드 적재 — Track A (`Console UI`) vs Track B (`Script`)

아래 두 가지 방법 중 하나를 선택해 `Cloud Storage`와 `BigQuery`에 데이터를 적재합니다. *(참고: `Track B`의 `02_provision_1p_datastores.py`는 본 적재 과정과 `Task 02`의 `DataStore` 생성을 한 번에 수행합니다.)*

### Track A: Google Cloud Console UI 과정

#### 1) `Cloud Storage` Bucket 생성 및 문서 업로드
1. `GCP Console > Cloud Storage > Buckets`로 이동하여 **`+ CREATE`** 를 클릭합니다.
2. Bucket 이름에 `<PROJECT_ID>-cbl-ge-demo`를 입력하고, `Location type`은 **`Multi-region` (`us`)** 를 선택합니다.
3. `Access control`은 기본값(`Uniform`)을 유지하고 **`CREATE`** 를 클릭합니다.
4. 생성된 Bucket 안에서 **`UPLOAD FOLDER`** 버튼을 눌러 로컬 `generated_data/docs/` 안의 세 폴더(`scenario1_ad_compliance`, `scenario2_sales_promo`, `scenario3_voc_qa`)를 그대로 업로드합니다.

#### 2) `BigQuery` Dataset 및 4개 Table 생성
1. `GCP Console > BigQuery > Studio`로 이동합니다.
2. 좌측 `Explorer`에서 프로젝트 옆 점 3개 메뉴(`⋮`) → **`Create dataset`** 을 클릭합니다.
3. `Dataset ID`에 **`cbl_ge_demo`**, `Data location`에 **`US (multiple regions in United States)`** 를 선택하고 **`CREATE DATASET`** 을 클릭합니다.
4. 생성된 `cbl_ge_demo` 옆 메뉴(`⋮`) → **`Create table`** 을 클릭하여 `generated_data/csv/` 내 4개 CSV 파일을 각각 적재합니다:
   - `Create table from`: **`Upload`** → 파일 선택 (`.csv`), `File format`: `CSV`
   - `Table` 이름: 각각 `products_master`, `channel_sales_inventory`, `promotions_calendar`, `voc_quality_claims`
   - `Schema`: **`Auto detect`** 체크, `Advanced options > Header rows to skip`: **`1`** 입력 후 **`CREATE TABLE`** 클릭
5. 적재 후 각 `Table`의 **`Preview`** 탭에서 총 행 수(`120`, `3,600`, `240`, `2,500`)를 확인합니다.

---

### Track B: CLI / Script 자동화 과정

`gcloud storage`와 `bq` 명령어(또는 `Task 02` 통합 Python `Script`)로 동일하게 적재할 수 있습니다.

```bash
source .env
BUCKET="${GCS_BUCKET:-${PROJECT_ID}-cbl-ge-demo}"

# GCS Bucket 생성 및 문서 업로드
gcloud storage buckets create "gs://${BUCKET}" --project="${PROJECT_ID}" --location="${BQ_LOCATION}" --uniform-bucket-level-access || true
gcloud storage cp -r generated_data/docs/* "gs://${BUCKET}/" --project="${PROJECT_ID}"

# (또는 Task 02 통합 Script 실행 시 GCS + BigQuery + 1P DataStore까지 한 번에 처리됩니다)
python3 scripts/02_provision_1p_datastores.py
```

다음 단계: [Task 02: GCS & BigQuery 1P DataStore 구축 및 GE App 연결](task02_1p_datastores.md)
