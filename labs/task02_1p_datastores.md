# Task 02: GCS & BigQuery 1P DataStore 구축 및 GE App 연결

`Task 01`에서 적재한 비정형 문서(`Cloud Storage`)와 정형 Table (`BigQuery`)을 Gemini Enterprise의 **1P DataStore** 5종으로 Indexing한 뒤 대상 `GE App`에 연결합니다.

### 시나리오별로 DataStore를 분리하는 이유

메인 `Default Assistant` 대화 화면에서는 `GE App`에 연결된 5개 `DataStore` 전체를 통합 검색합니다. 반면 `Task 03`의 **`Agent Designer`** 에서 업무별 전용 `Agent`나 `Workflow`를 설계할 때는 각 단계(`Node`)마다 필요한 `DataStore`만 선별 지정(`Scoping`)할 수 있습니다. 표시·광고 심의 Agent가 재고 Table까지 불필요하게 참조하지 않도록 검색 범위를 좁혀 주면 인용 정확도와 응답 일관성이 눈에 띄게 좋아집니다.

| DataStore ID | 유형 | 원본 데이터 경로 | 연결 시나리오 |
|---|---|---|---|
| `cbl-ds-ad-compliance` | `Cloud Storage` (Unstructured) | `gs://<BUCKET>/scenario1_ad_compliance/*` | Scenario 1 (표시·광고 검수) |
| `cbl-ds-sales-policy` | `Cloud Storage` (Unstructured) | `gs://<BUCKET>/scenario2_sales_promo/*` | Scenario 2 (매출·재고 브리핑) |
| `cbl-ds-voc-sop` | `Cloud Storage` (Unstructured) | `gs://<BUCKET>/scenario3_voc_qa/*` | Scenario 3 (VOC·클레임 대응) |
| `cbl-ds-bq-sales-inventory` | `BigQuery` (Structured) | `cbl_ge_demo.channel_sales_inventory` | Scenario 2 (매출·재고 브리핑) |
| `cbl-ds-bq-voc-claims` | `BigQuery` (Structured) | `cbl_ge_demo.voc_quality_claims` | Scenario 3 (VOC·클레임 대응) |

---

## 1. Track A: Google Cloud Console UI 과정

### Step 1. Cloud Storage 비정형 DataStore 3종 생성

1. `GCP Console > Gemini Enterprise > Data Stores` Menu로 이동합니다 (상단 `Region`: **`global`** 확인).
2. **`+ CREATE DATA STORE`** 를 누른 뒤 목록에서 **`Cloud Storage`** 의 **`Select`** 를 클릭합니다.
3. 첫 번째 시나리오 정보를 입력합니다.
   - Import 대상 유형: **`Folder`** 선택 후 `Browse`에서 `<BUCKET>/scenario1_ad_compliance` 지정
   - 문서 종류: **`Unstructured documents (PDF, HTML, DOCX, TXT)`**
   - Document processing / Chunking Option: **`Layout Parser` / `Enable chunking` (Chunk size `500`, `Include ancestor headings`)** 활성화
   - `Location`: **`global`**
   - `Data store name`: `CBL 표시·광고 검수 가이드 & 심의사례 (GCS)` (직접 ID 지정 시 `cbl-ds-ad-compliance`)
4. 같은 절차로 `scenario2_sales_promo` (`cbl-ds-sales-policy`)와 `scenario3_voc_qa` (`cbl-ds-voc-sop`) 두 Folder도 각각 개별 `DataStore`로 생성합니다.

### Step 2. BigQuery 정형 DataStore 2종 생성

1. 다시 **`+ CREATE DATA STORE`** 를 클릭하고 목록에서 **`BigQuery`** 의 **`Select`** 를 누릅니다.
2. `Browse`에서 `<PROJECT_ID> > cbl_ge_demo > channel_sales_inventory` `Table`을 선택합니다.
3. `Schema` Option은 기본 구조 유지 및 문서 ID 자동 생성(`Auto-generate document IDs`)을 선택한 뒤 이름을 `CBL 채널별 매출·재고 실적 (BigQuery)` (`cbl-ds-bq-sales-inventory`)로 지정해 생성합니다.
4. 동일한 방식으로 `cbl_ge_demo.voc_quality_claims` `Table`을 연결한 두 번째 정형 `DataStore` (`cbl-ds-bq-voc-claims`)를 만듭니다.

### Step 3. GE App에 5개 DataStore 연결 및 Indexing 상태 확인

1. 좌측 **`Gemini Enterprise > Apps`** 에서 `Task 00`에서 생성한 `App`을 선택합니다.
2. 하위 Menu **`Connected data stores`** 로 들어가 **`Add existing data stores`** 버튼을 클릭합니다.
3. 방금 만든 5개 `DataStore`를 모두 체크하고 **`Connect` / `Save`** 를 누릅니다.
4. 각 `DataStore` 상세 화면의 **`Activity`** Tab에서 Import 상태가 `Completed` (`failure=0`)로 전환될 때까지 확인합니다. 비정형 HTML Layout Parsing까지 약 4~8분이 걸리므로 대기 시간 동안 `Task 04` Governance 설정을 먼저 진행해도 무방합니다.

---

## 2. Track B: Script 자동화 과정

아래 Python `Script`는 `GCS` 업로드, `BigQuery` Table 적재, 5개 1P `DataStore` 생성(`Layout-based Chunking` 포함), Import 완료 대기, 그리고 `GE Engine` 연결까지 멱등성(`Idempotent`)을 보장하며 일괄 처리합니다.

```bash
python3 scripts/02_provision_1p_datastores.py
```

### 확인 포인트

- 실행 Log 마지막에 `[ATTACHED] Engine ... now has dataStoreIds: ['cbl-ds-ad-compliance', 'cbl-ds-sales-policy', 'cbl-ds-voc-sop', 'cbl-ds-bq-sales-inventory', 'cbl-ds-bq-voc-claims']` 문구가 표시되고 5개 Import 작업 모두 `failure=0`으로 집계되면 정상입니다.

다음 단계: [Task 03: GE Agent Designer 기반 Low-Code Agent & Workflow 3종 구성 및 시연](task03_ge_agents_workflows.md)
