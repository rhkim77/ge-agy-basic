# Task 02: `GCS` & `BigQuery` 1P `DataStore` 구축 및 `GE App` 연결

이 단계에서는 `Task 01`에서 적재한 비정형 문서(`GCS`)와 정형 테이블(`BigQuery`)을 Gemini Enterprise의 **1P `DataStore`** 5종으로 인덱싱하고 대상 `GE App`에 연결합니다.

### 왜 시나리오별로 `DataStore`를 분리하나요?
- **메인 `Default Assistant` 채팅창**에서는 연결된 5개 `DataStore` 전체를 통합 검색합니다.
- 반면 `Task 03`의 **`Agent Designer`** 에서 업무별 전용 `Agent` / `Workflow`를 만들 때는 해당 업무에 필요한 `DataStore`만 선택적으로 지정(`Scoping`)할 수 있어 검색 정확도와 응답 품질이 크게 높아집니다.

| DataStore ID | 유형 | 소스 대상 | 연결될 시나리오 |
|---|---|---|---|
| `cbl-ds-ad-compliance` | `Cloud Storage` (Unstructured) | `gs://<BUCKET>/scenario1_ad_compliance/*` | Scenario 1 (표시·광고 검수) |
| `cbl-ds-sales-policy` | `Cloud Storage` (Unstructured) | `gs://<BUCKET>/scenario2_sales_promo/*` | Scenario 2 (매출·재고 브리핑) |
| `cbl-ds-voc-sop` | `Cloud Storage` (Unstructured) | `gs://<BUCKET>/scenario3_voc_qa/*` | Scenario 3 (VOC·클레임 대응) |
| `cbl-ds-bq-sales-inventory` | `BigQuery` (Structured) | `cbl_ge_demo.channel_sales_inventory` | Scenario 2 (매출·재고 브리핑) |
| `cbl-ds-bq-voc-claims` | `BigQuery` (Structured) | `cbl_ge_demo.voc_quality_claims` | Scenario 3 (VOC·클레임 대응) |

---

## 1. Track A: Google Cloud Console UI 과정

### Step 1. `Cloud Storage` 비정형 `DataStore` 3종 생성
1. `GCP Console > Gemini Enterprise > Data Stores` 메뉴로 이동합니다 (상단 `Region`: **`global`** 확인).
2. **`+ CREATE DATA STORE`** 클릭 → 소스 목록에서 **`Cloud Storage`** 의 **`Select`** 를 클릭합니다.
3. 첫 번째 시나리오 구성을 입력합니다:
   - Import 대상 유형: **`Folder`** 선택 → `Browse`에서 `<BUCKET>/scenario1_ad_compliance` 선택
   - 데이터 형식: **`Unstructured documents (PDF, HTML, DOCX, TXT, XLSX)`**
   - Document processing / Chunking 옵션(선택 가능 시): **`Layout Parser` / `Enable chunking` (Chunk size `500`, `Include ancestor headings`)** 체크
   - `Location`: **`global`**
   - `Data store name`: `CBL 표시·광고 검수 가이드 & 심의사례 (GCS)` (ID를 직접 지정할 수 있으면 `cbl-ds-ad-compliance`)
4. 동일한 방식으로 `scenario2_sales_promo` (`cbl-ds-sales-policy`), `scenario3_voc_qa` (`cbl-ds-voc-sop`) 두 폴더에 대해서도 각각 `DataStore`를 생성합니다.

### Step 2. `BigQuery` 정형 `DataStore` 2종 생성
1. 다시 **`+ CREATE DATA STORE`** 클릭 → 소스 목록에서 **`BigQuery`** 의 **`Select`** 를 클릭합니다.
2. `Browse`를 눌러 `<PROJECT_ID> > cbl_ge_demo > channel_sales_inventory` `Table`을 선택합니다.
3. Schema 옵션은 **`Custom` (기본 구조 유지)** 및 ID 자동 생성(`Auto-generate document IDs`)을 선택하고 이름을 `CBL 채널별 매출·재고 실적 (BigQuery)` (`cbl-ds-bq-sales-inventory`)로 지정해 생성합니다.
4. 동일한 절차로 `cbl_ge_demo.voc_quality_claims` `Table`을 연결한 `DataStore` (`cbl-ds-bq-voc-claims`)를 생성합니다.

### Step 3. `GE App`에 5개 `DataStore` 연결 및 인덱싱 상태 확인
1. 좌측 **`Gemini Enterprise > Apps`** 에서 `Task 00`에서 만든 `App`을 클릭합니다.
2. 좌측 하위 메뉴 **`Connected data stores`** 로 이동한 뒤 **`Add existing data stores`** 버튼을 클릭합니다.
3. 방금 생성한 5개 `DataStore`를 모두 체크하고 **`Connect` / `Save`** 를 클릭합니다.
4. 각 `DataStore`를 클릭해 **`Activity`** 탭에서 Import 상태가 `Completed`로 바뀔 때까지 확인합니다 (비정형 문서 파싱 포함 약 4~8분 소요; 기다리는 동안 `Task 04` 거버넌스 설정을 먼저 진행해도 좋습니다).

---

## 2. Track B: Script 자동화 과정

아래 Python `Script`는 `GCS` 업로드, `BigQuery` 적재, 5개 1P `DataStore` 생성(Layout-based Chunking 포함), 비동기 Import 요청, 그리고 `GE Engine` 연결까지 멱등성(`Idempotent`) 있게 일괄 처리합니다.

```bash
python3 scripts/02_provision_1p_datastores.py
```

### 확인 포인트
- 출력 로그에 `[ATTACHED] Engine ... now has dataStoreIds: ['cbl-ds-ad-compliance', 'cbl-ds-sales-policy', 'cbl-ds-voc-sop', 'cbl-ds-bq-sales-inventory', 'cbl-ds-bq-voc-claims']` 메시지가 출력되면 연결이 완료된 것입니다.

다음 단계: [Task 03: GE Agent Designer 기반 No-Code Agent & Workflow 3종 구성 및 시연](task03_ge_agents_workflows.md)
