# Task 05: Google Antigravity 접속 및 Domain Rule · Skill · BigQuery 연계 실습

마지막 단계에서는 현업 임직원이 `GE Web App`(`Task 03`)에서 건별로 질의하던 동일한 `Cymbal Beauty & Living` 데이터와 사내 규정을 개발자·AX 담당자가 **Google Antigravity**(`Desktop IDE` 또는 `agy CLI`)에서 이어받아 **다건 배치 검수기와 임원용 운영 분석 Dashboard**로 확장하는 협업 시나리오를 실습합니다.

---

## 1. agy_workspace 구성 살펴보기

Repository 안의 [agy_workspace/](../agy_workspace/) Folder에는 조직 개발 표준을 강제하는 Domain `Rule`과 재사용 가능한 `Skill` 2종이 사전 구성되어 있습니다.

| File 경로 | 역할 |
|---|---|
| [.agent/rules/cymbal-domain-governance.md](../agy_workspace/.agent/rules/cymbal-domain-governance.md) | 화장품법 제13조 금지 표현 기준(`RA-AD-2026-01`), `BigQuery` 읽기 전용 안전 수칙, 동일 Lot 10건 이상 `P1-긴급` 격상 원칙을 모든 `Antigravity` Session에 자동 주입 |
| [.agent/skills/ad-compliance-auditor/SKILL.md](../agy_workspace/.agent/skills/ad-compliance-auditor/SKILL.md) | 다건 마케팅 카피 CSV를 일괄 검수해 시각적 HTML Audit Report를 생성하는 `Skill` |
| [.agent/skills/bq-ops-analyzer/SKILL.md](../agy_workspace/.agent/skills/bq-ops-analyzer/SKILL.md) | `cbl_ge_demo` `BigQuery` Dataset에서 안전재고 미달 SKU와 동일 Lot 집중 VOC를 추출하는 `Skill` |
| [samples/campaign_copies_draft.csv](../agy_workspace/samples/campaign_copies_draft.csv) | 신제품 캠페인 카피 시안 8건 (반려·조건부승인·승인 Case 혼합) |
| [samples/batch_copy_validator.py](../agy_workspace/samples/batch_copy_validator.py) | 배치 검수 기준 Reference `Script` |

---

## 2. Track A: Google Antigravity Desktop IDE / CLI 실습 과정

### Step 1. Antigravity 로그인 및 agy_workspace 열기

1. **Desktop IDE 사용 시**
   - `Google Antigravity`를 실행한 뒤 초기 로그인 화면에서 `Use Business Account`와 `Continue with Google Cloud`를 차례대로 선택합니다 (`WIF` 연동 조직은 하단 `Use Advanced SSO Config` 선택).
   - Browser에서 `Task 00` `Seat`를 할당받은 계정으로 로그인하고 대상 `Project ID`와 `Location`(`global`)을 지정합니다.
   - `Seat` 할당 후 5~15분 이내라 `Entitlement Cache` 동기화 전이거나 `Self-serve` 온라인 결제 계정을 쓰는 경우에는 로그인 화면에서 `Use Google Cloud project instead`를 선택해 동일 `Project`로 진입할 수 있습니다.
   - 좌측 `Open Folder` 또는 `Projects`에서 이 Repository 안의 `agy_workspace` Folder를 엽니다 (`Yes, I trust this folder` 선택).

2. **agy CLI 사용 시**
   ```bash
   cd agy_workspace
   agy
   # 로그인 Prompt에서 Use Business Account (또는 Use a Google Cloud project) -> Project ID -> global 선택
   # Skill 로드 확인: /skills 입력 시 ad-compliance-auditor, bq-ops-analyzer 표시 확인
   ```

### Step 2. 실습 시나리오 4-A: 신제품 카피 다건 배치 검수기 고도화

`Antigravity` 대화창에 아래 `Prompt`를 입력해 Domain `Rule`과 `ad-compliance-auditor` `Skill`이 자동 반영되는지 확인합니다.

```text
samples/campaign_copies_draft.csv File의 8개 마케팅 카피를 우리 회사 표시·광고 거버넌스 Rule에 따라 일괄 검수해줘.
기존 samples/batch_copy_validator.py를 실행해서 samples/output_ad_audit_report.html을 생성하고
REJECT(반려) 또는 CONDITIONAL(조건부승인) 판정을 받은 항목마다 규정을 준수하는 수정 카피 추천 Column까지 추가한 요약 표를 보여줘.
```

- `Task 04`에서 `Terminal execution policy = Require review`로 설정했기 때문에 `Agent`가 `python3 samples/batch_copy_validator.py` 실행 승인을 요청합니다. 내용을 확인한 뒤 `Allow`를 클릭합니다.
- 생성된 `agy_workspace/samples/output_ad_audit_report.html` File을 Browser에서 열어 색상별 판정 Badge(`REJECT` 5건, `CONDITIONAL` 1건, `PASS` 2건)와 추천 대체 문구를 확인합니다.

### Step 3. 실습 시나리오 4-B: BigQuery 재고 리스크 & P1 집중 Lot 임원 브리핑 생성

`Antigravity` 대화창에 아래 `Prompt`를 입력합니다 (`bigquery` 원격 MCP Server 또는 읽기 전용 `SELECT` Query를 활용합니다).

```text
bq-ops-analyzer Skill과 거버넌스 Rule을 참고해서 현재 Project의 cbl_ge_demo Dataset을 조회해줘.
1) 안전재고 50% 미만인 긴급발주필요 SKU·채널 현황과 연결된 프로모션 ROI
2) 동일 Lot에서 10건 이상 집중 발생한 P1-긴급 품질 클레임 현황을 조회해서
주간 임원회의용 단일 HTML Dashboard(samples/output_exec_ops_brief.html)로 만들어줘.
```

---

## 3. Track B: 전 구간 자동 검증 및 실습 Resource 정리 (Script)

### 1) 전 구간 통합 자동 검증 (05_verify_all.py)

5개 1P `DataStore` 검색 응답, 3개 등록 `Agent` 상태, 3대 시나리오 `StreamAssist` 답변 품질, `geStandardChatUser` `IAM Role`의 `businessaicode.*` 차단 여부, 그리고 `Antigravity` 배치 검수기 실행까지 한 번에 검증합니다.

```bash
python3 scripts/05_verify_all.py
```

### 2) 실습 Resource 정리 (99_teardown.py)

실습을 모두 마친 뒤 등록 `Agent` 삭제, `Engine DataStore` 연결 해제, 5개 `DataStore` 삭제, `BigQuery Dataset` 삭제, `GCS Bucket` 삭제를 의존성 순서에 맞춰 안전하게 정리하려면 아래 명령을 실행합니다.

```bash
python3 scripts/99_teardown.py
```

> [!WARNING]
> 시연 환경을 계속 유지해야 하는 경우에는 `99_teardown.py`를 실행하지 마세요.
