# Task 00 (Setup): 필수 API 활성화, 30일 체험 License 할당 및 GE App 생성

단일 Google Cloud Project에서 **Gemini Enterprise**(`GE`) 30일 무료 체험 License를 활성화한 뒤 `Google Identity` 인증 기반의 첫 번째 `GE App`(`Engine`)을 생성합니다.

> [!NOTE]
> 좌석 할당 직후 `Antigravity` Backend `Entitlement Cache` 동기화에 최대 5~15분 정도 걸립니다. 이 Setup 단계를 가장 먼저 완료해 두면 `Task 04 ~ 05` 진입 시 대기 시간 없이 바로 로그인할 수 있습니다.

---

## 1. Track A: Google Cloud Console UI 과정

### Step 1. Gemini Enterprise Console 진입 및 30일 무료 체험 시작

1. [Google Cloud Console](https://console.cloud.google.com/)에 로그인한 뒤 상단 Project 선택기에서 실습 대상 `Project`를 선택합니다.
2. 상단 검색창에 `Gemini Enterprise`를 입력해 이동합니다.
3. 상단 `Region`이 `global`로 지정되어 있는지 확인하고 `Create app` 버튼을 클릭합니다.
   - **주의사항**: `App`의 `Location`(`global`, `us`, `eu`)은 생성 이후에 변경할 수 없습니다. 최신 `Model`과 `Agent Designer` 기능을 모두 사용하려면 `global`을 선택하세요.
4. 아직 활성 구독이 없는 `Project`라면 화면 안내에 따라 **30일 무료 체험**(`Free trial`, 기본 50석)을 시작합니다.
5. `App` 이름(예: `cbl-enterprise-hub`)을 입력해 생성을 마칩니다. 생성된 `App` 목록에서 **App ID**(예: `gemini-enterprise-XXXX_XXXX`)를 별도로 기록해 둡니다.

### Step 2. 사용자 좌석 (License) 할당 확인

1. 좌측 Menu에서 `Gemini Enterprise > Licenses`(또는 `Manage users`)로 이동합니다.
2. 상단 `Region`이 `global`인지 확인한 다음 `Assign users`를 클릭합니다.
3. 실습에 사용할 본인 계정과 추가 Test 계정 이메일을 입력해 `free_trial_gemini` 구독 좌석을 할당합니다 (`Status: Assigned`).

### Step 3. 인증 공급자 (Identity Provider) 설정 (Non-GWS 기준)

1. 생성한 `App` 이름을 클릭해 Dashboard로 들어가면 **Set up your workforce identity** 안내 Card가 나타납니다.
2. `Set up identity`(또는 좌측 `Settings > Authentication`)를 클릭합니다.
3. 유료 `Google Workspace`를 쓰지 않더라도 무료 `Cloud Identity Free`나 일반 Google 계정을 사용하는 환경에서는 기본 권장 Option인 `Google Identity`를 선택한 뒤 `Save` 또는 `Confirm Workforce Identity`를 누릅니다.
   - 사내 `Entra ID`나 `Okta`를 `Workforce Identity Federation`으로 직접 연동하는 조직만 `3rd party identity`를 선택합니다. 이 경우 `google.subject` 속성에 반드시 소문자 이메일을 매핑해야 좌석 인식 오류가 발생하지 않습니다.
4. 설정 완료 화면에 표시되는 **Web App URL**(`https://vertexaisearch.cloud.google.com/home/cid/...`)을 Browser에 저장해 둡니다.

---

## 2. Track B: CLI / Script 과정

Terminal 또는 `Cloud Shell`에서 Repository를 복제하고 `.env` File을 작성한 뒤 `00_setup_and_check.py`를 실행합니다. 필수 API 7종(`discoveryengine`, `businessaicode`, `bigquery`, `storage`, `iam`, `dlp`, `modelarmor`) 활성화와 `License` 및 `App` 상태 점검이 한 번에 진행됩니다.

```bash
# 1. Google Cloud ADC 인증 (아직 인증하지 않은 경우)
gcloud auth application-default login --no-launch-browser

# 2. .env File 생성 및 본인 환경값 입력
cp .env.example .env
# 편집기로 .env 내 PROJECT_ID 및 GE_ENGINE_ID(위 Step 1에서 확인한 App ID) 입력

# 3. 필수 API 일괄 활성화 및 30일 체험 License / Engine 상태 확인
python3 scripts/00_setup_and_check.py
```

### 확인 포인트

- 실행 Log에서 `free_trial_gemini`(또는 보유 구독)의 상태가 `state=ACTIVE`이고 본인 이메일이 `ASSIGNED`로 조회되며 `GE_ENGINE_ID` 우측에 `<-- TARGET (.env)` 표기가 출력되면 준비가 완료된 상태입니다.

다음 단계: [Task 01: 중규모 가상 데이터 생성 및 GCS / BigQuery 적재](task01_synthetic_data.md)
