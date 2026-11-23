# Task 04: `Google Antigravity` (`agy`) 거버넌스, `Custom IAM Role` 분리 및 `MCP Allowlist` 설정

기업에서 `Gemini Enterprise` 좌석을 도입하면 기본적으로 `Google Antigravity` (`AI developer tools`) 권한이 함께 포함됩니다. 실무 운영에서는 **일반 현업 임직원에게는 `GE Web App` · `Canvas`만 허용(`Antigravity` 차단)**하고, **승인된 개발자·AX 담당자 그룹에게만 `Antigravity`를 허용**하는 직무별 권한 분리와 로컬 실행 보안 통제가 필요합니다.

---

## 1. 직무별 `IAM` 분리 구조

| 대상 그룹 | 부여할 `IAM Role` | `GE Web App` / `Canvas` | `Google Antigravity` (`agy`) |
|---|---|---|---|
| **일반 현업 임직원** | `projects/<PROJECT_ID>/roles/geStandardChatUser` (`Custom Role`) | **허용** (`immersiveArtifacts.*` 포함) | **차단** (`businessaicode.*` 권한 제외) |
| **승인 개발자 / AX 담당자** | `roles/discoveryengine.agentspaceUser` (표준 `Gemini Enterprise User`) | **허용** | **허용** |
| **플랫폼 관리자 (`Admin`)** | `roles/discoveryengine.agentspaceAdmin` **+** `roles/discoveryengine.agentspaceUser` | **허용** | **허용** *(주의: `Admin` 단독 역할만으로는 `Antigravity` 실행 불가 — 반드시 `User` 역할 병행 부여)* |

---

## 2. Track A: Google Cloud Console UI 과정

### Step 1. 일반 임직원용 `Antigravity` 차단 `Custom IAM Role` 확인 및 부여
> [!IMPORTANT]
> `Canvas` 기능에 필요한 `discoveryengine.immersiveArtifacts.*` 권한은 Preview 권한이 포함되어 있어 `Console UI`의 역할 복제 화면만으로는 누락될 수 있습니다. 역할 자체 생성은 아래 `Track B`의 `04_setup_antigravity.py`(또는 `gcloud iam roles create`)로 생성한 뒤, `GCP Console > IAM & Admin > IAM`에서 그룹별 바인딩을 수행하는 것이 안전합니다.

1. `GCP Console > IAM & Admin > Roles`에서 `GE Standard Chat User (No Antigravity)` (`geStandardChatUser`) 역할을 클릭해 `businessaicode.locations.*` 권한이 제외되어 있는지 확인합니다.
2. `IAM & Admin > IAM`에서 **`+ GRANT ACCESS`** 를 클릭하여:
   - 일반 현업 사용자/그룹 → `Custom > GE Standard Chat User (No Antigravity)` 부여
   - 승인 개발자 사용자/그룹(및 실습 본인 계정) → `Gemini Enterprise User` (`roles/discoveryengine.agentspaceUser`) 부여

### Step 2. `Settings > AI developer tools` 보안 및 `MCP Allowlist` 구성
1. `GCP Console > Gemini Enterprise > Settings`로 이동한 뒤 상단 탭에서 **`AI developer tools`** 를 선택합니다 (상단 `Region`: **`global`** 확인).
2. **`AI developer tools`** 마스터 토글을 **`On`** 으로 켭니다 (꺼져 있던 경우 자동으로 `businessaicode.googleapis.com` API를 점검·활성화합니다).
3. 아래 권장 엔터프라이즈 보안 정책을 설정합니다:
   - **Security > Outside workspace file access**: **`Deny`** (열어 둔 프로젝트 폴더 바깥의 로컬 파일 접근 차단)
   - **Security > Terminal execution policy**: **`Require review`** (에이전트가 셸 명령을 실행하기 전 개발자 승인 요구)
   - **Security > Terminal sandbox**: **`Enabled`**
   - **Compliance > Metadata logging**: **`Enabled`** (`Cloud Logging`의 `businessaicode.googleapis.com/inference_response` 스트림으로 사용자별 Token 사용량 및 활성 여부 추적)
4. **MCP Server 통제 (`Allowed server configuration`)** 입력란에 [agy_workspace/configs/mcp_allowlist.json](../agy_workspace/configs/mcp_allowlist.json) 내용을 복사해 붙여넣고 **`Save`** 를 클릭합니다:
   ```json
   {
     "mcpServers": {
       "local_servers": [
         {
           "id": "local-copy-auditor",
           "command": "python3",
           "args": [
             "samples/batch_copy_validator.py",
             "--stdio-check"
           ]
         }
       ],
       "remote_servers": [
         {
           "id": "bigquery"
         }
       ]
     }
   }
   ```

### Step 3. 주간 공유 `Credit` 독점 방지 (`Usage & spend`)
1. 좌측 메뉴 **`Gemini Enterprise > Usage & spend`** 로 이동합니다.
2. `Pay-as-you-go usage above quota`가 **`Disabled`** 인지 확인합니다 (30일 체험 `License`에서는 기본 비활성).
3. 특정 개발자 1인이 주간 공유 `Antigravity Credit Pool`을 과도하게 소진하지 못하도록 **`Limit any single-user's quota (Multiplier)`** 값을 **`10`** 으로 설정하고 저장합니다.

---

## 3. Track B: Script 자동화 과정

아래 `Script`는 `businessaicode.googleapis.com` 활성화, `gcp-sa-businessaicode` `Service Identity` 생성, 최신 `roles/discoveryengine.agentspaceUser` 권한 목록 조회 후 `businessaicode.*`만 제거한 `geStandardChatUser` `Custom Role` 생성/업데이트, 그리고 `mcp_allowlist.json` 문법 검증을 자동으로 수행합니다.

```bash
python3 scripts/04_setup_antigravity.py
```

다음 단계: [Task 05: Google Antigravity 접속 및 도메인 Rule · Skill · BigQuery 연계 개발 실습](task05_agy_hands_on_demo.md)
