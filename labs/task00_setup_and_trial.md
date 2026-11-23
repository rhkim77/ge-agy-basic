# Task 00 (Setup): 필수 API 활성화, 30일 체험 `License` 할당 및 `GE App` 생성

이 단계에서는 단일 Google Cloud Project에서 **Gemini Enterprise (`GE`)** 30일 무료 체험 `License`를 활성화하고, `Google Identity` 기반 첫 번째 `GE App`(`Engine`)을 준비합니다.

> [!NOTE]
> 좌석 할당 직후 `Antigravity` 백엔드 `Entitlement Cache` 동기화에 최대 5~15분이 걸릴 수 있으므로, 본 Setup 단계를 가장 먼저 완료해 두면 `Task 04 ~ 05` 진입 시 대기 없이 바로 로그인할 수 있습니다.

---

## 1. Track A: Google Cloud Console UI 과정

### Step 1. `Gemini Enterprise` 콘솔 진입 및 30일 무료 체험 시작
1. [Google Cloud Console](https://console.cloud.google.com/)에 로그인하고 상단 프로젝트 선택기에서 실습 대상 `Project`를 선택합니다.
2. 상단 검색창에 **`Gemini Enterprise`** 를 입력해 이동합니다.
3. 상단 `Region`이 **`global`** 로 선택되어 있는지 확인한 뒤 **`Create app`** 버튼을 클릭합니다.
   - **중요**: `App`의 `Location`(`global`, `us`, `eu`)은 생성 이후 변경할 수 없습니다. 최신 `Model` 및 `Agent Designer` 기능 검증에는 `global`을 권장합니다.
4. 아직 구독이 없는 `Project`라면 화면 안내에 따라 **30일 무료 체험(`Free trial`, 기본 50석)** 을 시작합니다.
5. `App` 이름(예: `cbl-enterprise-hub`)을 입력하고 생성을 완료합니다. 생성된 `App` 목록에서 **`App ID`**(예: `gemini-enterprise-XXXX_XXXX`)를 메모해 둡니다.

### Step 2. 사용자 좌석(`License`) 할당 확인
1. 좌측 메뉴에서 **`Gemini Enterprise > Licenses`** (또는 `Manage users`)로 이동합니다.
2. 상단 `Region`이 **`global`** 인지 확인한 뒤 **`Assign users`** 를 클릭합니다.
3. 실습에 사용할 본인 계정(및 추가 테스트 계정) 이메일을 입력하고 `free_trial_gemini` 구독 좌석을 할당합니다 (`Status: Assigned`).

### Step 3. 인증 공급자(`Identity Provider`) 설정 (`Non-GWS` 기준)
1. 생성한 `App` 이름을 클릭해 대시보드로 들어가면 **Set up your workforce identity** 안내 카드가 표시됩니다.
2. **`Set up identity`** (또는 좌측 `Settings > Authentication`)를 클릭합니다.
3. 유료 `Google Workspace`가 없는 환경에서도 무료 `Cloud Identity Free` 또는 Google 계정을 쓰는 경우 기본 권장 옵션인 **`Google Identity`** 를 선택하고 **`Save` / `Confirm Workforce Identity`** 를 클릭합니다.
   - *(사내 `Entra ID` · `Okta`를 `Workforce Identity Federation`으로 직접 연결하는 조직만 `3rd party identity`를 선택하며, 이 경우 `google.subject`에 반드시 소문자 이메일을 매핑합니다.)*
4. 완료 화면에 표시되는 **`Web App URL`**(`https://vertexaisearch.cloud.google.com/home/cid/...`)을 북마크해 둡니다.

---

## 2. Track B: CLI / Script 과정

터미널(또는 `Cloud Shell`)에서 Repository를 복제하고 `.env`를 설정한 뒤 `00_setup_and_check.py`를 실행해 필수 API 7종(`discoveryengine`, `businessaicode`, `bigquery`, `storage`, `iam`, `dlp`, `modelarmor`)을 일괄 활성화하고 `License` 및 `App` 상태를 점검합니다.

```bash
# 1. Google Cloud ADC 인증 (아직 인증하지 않은 경우)
gcloud auth application-default login --no-launch-browser

# 2. .env 파일 생성 및 본인 환경값 입력
cp .env.example .env
# 편집기로 .env 내 PROJECT_ID 및 GE_ENGINE_ID(위 Step 1에서 확인한 App ID) 입력

# 3. 필수 API 일괄 활성화 및 30일 체험 License / Engine 상태 확인
python3 scripts/00_setup_and_check.py
```

### 확인 포인트
- 출력 결과에서 `free_trial_gemini` (또는 보유 구독)의 `state=ACTIVE`, 본인 이메일 `ASSIGNED`, 그리고 `GE_ENGINE_ID` 옆에 `<-- TARGET (.env)` 표시가 나타나면 정상입니다.

다음 단계: [Task 01: 중규모 가상 데이터 생성 및 GCS / BigQuery 적재](task01_synthetic_data.md)
