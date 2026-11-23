#!/usr/bin/env python3
"""Zero-dependency synthetic enterprise document generator for Cymbal Beauty & Living (CBL) 1P GCS DataStores.

Generates 9 domain documents (7 semantic UTF-8 HTML docs + 2 standards-compliant OOXML XLSX workbooks) across 3 scenarios:
  - scenario1_ad_compliance/ (3 docs: 2 HTML guidelines + 1 XLSX historical review ledger)
  - scenario2_sales_promo/   (3 docs: 3 HTML policy/manual/brief docs)
  - scenario3_voc_qa/        (3 docs: 2 HTML SOP/FAQ docs + 1 XLSX compensation & script table)
"""

import html
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

OUT_DIR = Path(__file__).resolve().parent.parent / "generated_data" / "docs"
for sub in ("scenario1_ad_compliance", "scenario2_sales_promo", "scenario3_voc_qa"):
    (OUT_DIR / sub).mkdir(parents=True, exist_ok=True)


def make_html_doc(path: Path, title: str, subtitle: str, sections: list[tuple[str, list[str], list[list[str]] | None]]):
    parts = [
        "<!DOCTYPE html>",
        '<html lang="ko">',
        f'<head><meta charset="UTF-8"><title>{html.escape(title)}</title>',
        "<style>body{font-family:Arial,sans-serif;line-height:1.6;max-width:900px;margin:24px auto;color:#202124}"
        "h1{font-size:22px;border-bottom:2px solid #1a73e8;padding-bottom:8px}"
        "h2{font-size:16px;color:#1a73e8;margin-top:24px}"
        ".meta{color:#5f6368;font-size:13px;margin-bottom:16px}"
        "table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}"
        "th,td{border:1px solid #dadce0;padding:8px;text-align:left;vertical-align:top}"
        "th{background:#f1f3f4;font-weight:bold}</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        f'<p class="meta">{html.escape(subtitle)}</p>',
    ]
    for heading, paragraphs, table_data in sections:
        parts.append(f"<h2>{html.escape(heading)}</h2>")
        for p in paragraphs:
            parts.append(f"<p>{html.escape(p)}</p>")
        if table_data:
            parts.append("<table><thead><tr>")
            for h in table_data[0]:
                parts.append(f"<th>{html.escape(str(h))}</th>")
            parts.append("</tr></thead><tbody>")
            for row in table_data[1:]:
                parts.append("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>")
            parts.append("</tbody></table>")
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _col_letter(idx: int) -> str:
    res = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        res = chr(65 + rem) + res
    return res


def make_xlsx(path: Path, sheet_name: str, headers: list[str], rows: list[list]):
    all_rows = [headers] + rows
    sheet_rows_xml = []
    for r_idx, row in enumerate(all_rows, start=1):
        cells_xml = []
        for c_idx, val in enumerate(row, start=1):
            ref = f"{_col_letter(c_idx)}{r_idx}"
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                cells_xml.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                text = escape(str(val))
                cells_xml.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        sheet_rows_xml.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows_xml)}</sheetData>'
        "</worksheet>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    wb_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{escape(sheet_name[:31])}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", wb_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def generate_scenario1():
    d = OUT_DIR / "scenario1_ad_compliance"

    make_html_doc(
        d / "01_화장품_표시광고_실무_가이드라인_2026.html",
        "Cymbal Beauty & Living 화장품 표시·광고 실무 가이드라인 (2026 개정판)",
        "문서번호: RA-AD-2026-01 | 주관부서: RA팀 · 법무팀 | 적용대상: Beauty · HDB 전 브랜드 마케팅",
        [
            ("1. 의약품 오인 우려 금지 표현 (화장품법 제13조 기준)", [
                "화장품은 인체의 청결·미화·피부 및 모발 건강 유지·증진을 목적으로 하며, 질병의 예방·치료 효능을 암시하는 모든 표현은 엄격히 금지됩니다.",
                "금지 키워드 예시: 피부 재생, 세포 재생, 아토피 치료, 피부염 완치, 여드름 완치, 탈모 치료/발모, 상처 치유, 스테로이드 대체, 보톡스/필러 효과.",
                "위반 시 행정처분 기준: 1차 위반 시 해당 품목 광고업무정지 3개월(의약품 오인) 또는 2개월(소비자 오인), 반복 위반 시 판매업무정지 가중 처분 대상입니다.",
            ], [
                ["구분", "절대 금지 표현 (반려)", "허용 가능 대체 표현 (실증/기준 충족 시)"],
                ["피부 장벽/진정", "손상된 피부 재생, 아토피 치료, 피부염 완벽 제거", "건조함으로 거칠어진 피부 장벽 강화에 도움, 외부 자극으로부터 피부 진정"],
                ["주름/탄력", "주름 완벽 제거, 보톡스 효과, 세포 노화 역전", "피부 주름 개선에 도움을 주는 기능성 화장품, 탄력 있는 피부결 케어"],
                ["탈모 기능성", "탈모 치료, 머리카락 새로 남(발모), 모근 재생", "탈모 증상 완화에 도움을 주는 기능성 샴푸 (식약처 보고 완료 품목 한정)"],
                ["최상급/배타적", "국내 최초 100% 효과, 부작용 제로, 기적의 크림, 의사 지정", "자사 기존 제품 대비 보습력 개선 (인체적용시험 조건 명시 필수)"],
            ]),
            ("2. 인체적용시험(실증자료) 표기 필수 4대 요건", [
                "수치(예: 보습력 145% 개선, 48시간 보습 지속)를 광고 카피에 기재할 경우 반드시 하단 각주 또는 본문에 (1) 시험기관명, (2) 시험기간, (3) 대상 인원 및 연령대, (4) 개인차 있음 문구를 명시해야 합니다.",
                "실증 보고서가 없는 상태에서 '임상 완료', '피부과 테스트 완료' 문구를 임의로 사용할 수 없으며, RA팀 심의번호(RA-2026-XXXX)를 사전 발급받아야 합니다.",
            ], None),
            ("3. 사전 심의 및 에스컬레이션 절차", [
                "신제품 런칭 카피, H&B스토어/로켓커머스 상세페이지, 인플루언서 협찬 가이드(PPL)는 배포 최소 영업일 5일 전 RA팀에 사전 검토를 요청해야 합니다.",
                "고위험 표현(의약품 오인, 미검증 수치, 의사 추천/지정)이 1건 이상 감지될 경우, 마케팅 담당자는 수정 후 RA팀 최종 승인(Approval)을 획득해야 집행 가능합니다.",
            ], None),
        ],
    )

    make_html_doc(
        d / "02_CBL_브랜드별_마케팅카피_검수기준서.html",
        "Cymbal Beauty & Living 핵심 브랜드별 마케팅 카피 검수 기준서",
        "문서번호: MKT-COPY-2026-02 | 대상 브랜드: 루미에르, 베르당, 더마퓨어, 루트케어, 퓨어민트",
        [
            ("1. 루미에르 (LUMIERE) — 프레스티지 안티에이징", [
                "허용 소구점: 골든실크 헤리티지 스토리텔링, 기능성 화장품(주름개선·미백) 보고 범위 내 효능, 인체적용시험 완료 수치(시험 조건 병기 시).",
                "주의 금지어: '피부 세포 재생', '노화 완벽 차단', '약효'. 대체어: '피부 본연의 컨디션 케어', '탄력 있는 피부결 유지'.",
            ], None),
            ("2. 베르당 (VERDANT) — 허브 수분 코스메틱", [
                "허용 소구점: 48시간 수분 지속력(실증자료 기반), 산뜻한 수분 젤 제형감, 허브 추출물 블렌딩 스토리.",
                "주의 금지어: '트러블 즉각 치료', '모공 영구 축소'. 대체어: '일시적 모공 수렴 효과', '촉촉하고 맑은 피부결 정돈'.",
            ], None),
            ("3. 더마퓨어 (DERMAPURE) — 민감성 더마 코스메틱", [
                "허용 소구점: 바이오세라마이드 기반 피부 유사 지질 보습, 민감성 피부 대상 저자극 테스트 완료(시험기관·인원 명기).",
                "주의 금지어: '아토피 전용 크림', '스테로이드 대체 치료제', '피부염 완치', '피부과 전문의 지정'. 대체어: '건조함으로 민감해진 피부를 위한 데일리 보습 장벽 케어'.",
            ], None),
            ("4. 루트케어 (ROOTCARE) — 탈모증상완화 기능성", [
                "허용 소구점: 식약처 보고 완료 품목에 한해 '탈모 증상 완화에 도움을 줌' 표기 가능, 두피 각질/유분 세정력 실증 수치.",
                "주의 금지어: '탈모 치료 샴푸', '발모 촉진', '지루성 두피염 완치'. 대체어: '탈모 증상 완화 기능성', '건강한 두피 환경 케어'.",
            ], None),
        ],
    )

    headers = ["심의ID", "브랜드", "채널", "제출 원문 카피", "심의결과", "반려/수정 사유", "승인된 수정 카피"]
    cases = [
        ["REV-2026-001", "루미에르", "자사몰", "바르는 순간 손상된 피부 세포를 100% 재생시키는 기적의 에센스", "반려", "의약품 오인(세포 재생) + 절대적/과장 표현(100%, 기적)", "풍부한 영양감으로 탄력 있는 피부 컨디션을 가꾸어 주는 리페어 에센스"],
        ["REV-2026-002", "더마퓨어", "H&B스토어", "아토피와 피부염을 완벽하게 치료하는 저자극 더마 크림", "반려", "질병명(아토피, 피부염) 직접 언급 및 치료 효능 표방", "건조함으로 민감해진 피부의 보습 장벽 강화에 도움을 주는 저자극 크림"],
        ["REV-2026-003", "루트케어", "로켓커머스", "2주 만에 머리카락이 새로 나는 탈모 치료 샴푸", "반려", "발모/탈모 치료 표현 금지 (화장품법 제13조 위반)", "두피 영양 공급으로 탈모 증상 완화에 도움을 주는 기능성 샴푸"],
        ["REV-2026-004", "베르당", "H&B스토어", "단 1회 사용으로 보습력 145% 개선! 48시간 수분 폭발", "조건부승인", "수치 표기 시 인체적용시험 기관·기간·대상 인원 각주 누락", "단 1회 사용으로 피부 보습량 145% 개선 (한국피부임상센터, 2026.08, 성인여성 32명, 개인차 있음)"],
        ["REV-2026-005", "퓨어민트", "오픈마켓스토어", "단 3일 양치로 치아 미백 완성 및 충치 100% 예방", "반려", "의약외품 허가 효능 범위 초과(100% 예방 단정)", "꾸준한 양치로 치아 미백 및 충치 예방에 도움을 주는 프리미엄 치약"],
        ["REV-2026-006", "셀라쥬", "백화점", "보톡스 맞은 듯 이마 주름을 영구적으로 지워주는 크림", "반려", "의료시술(보톡스) 비유 및 영구적 제거 과장 표현", "주름 개선 기능성 성분이 탄탄하고 매끄러운 피부결 케어에 도움"],
        ["REV-2026-007", "페르망", "면세점", "발효 성분이 외부 자극으로 지친 피부를 편안하게 진정", "승인", "적합 (화장품 효능 범위 내 일반 표현)", "발효 성분이 외부 자극으로 지친 피부를 편안하게 진정"],
        ["REV-2026-008", "더마퓨어", "로켓커머스", "피부과 전문의 추천 부작용 제로 민감성 크림", "반려", "의사 추천/지정 표현 금지 및 부작용 제로 단정 불가", "민감성 피부 대상 피부자극 테스트 완료 데일리 보습 크림 (시험조건 명기)"],
        ["REV-2026-009", "베르당", "자사몰", "모공을 영구적으로 축소하고 여드름을 완치하는 수분 토너", "반려", "질병(여드름) 완치 및 영구 축소 허위과장", "피지 정돈과 일시적 모공 수렴 케어에 도움을 주는 산뜻한 허브 토너"],
        ["REV-2026-010", "루트케어", "오픈마켓스토어", "지루성 두피염 가려움 완벽 치료 및 모근 재생 앰플", "반려", "질병명(지루성 두피염) 치료 및 모근 재생 의약품 오인", "건조함으로 인한 두피 가려움 완화 및 건강한 두피 장벽 케어 앰플"],
    ]
    brands_extra = ["루미에르", "베르당", "더마퓨어", "루트케어", "페르망", "셀라쥬"]
    for i in range(11, 41):
        b = brands_extra[i % len(brands_extra)]
        res = "승인" if i % 3 == 0 else ("조건부승인" if i % 3 == 1 else "반려")
        reason = "적합" if res == "승인" else ("시험조건 각주 보완 필요" if res == "조건부승인" else "과장 표현 또는 기능성 범위 초과")
        cases.append([
            f"REV-2026-{i:03d}",
            b,
            ["H&B스토어", "로켓커머스", "자사몰", "백화점"][i % 4],
            f"{b} 2026 시즌 캠페인 상세페이지 카피 시안 #{i}",
            res,
            reason,
            f"{b} 가이드라인 준수 수정 카피 #{i} (실증 조건 병기)",
        ])
    make_xlsx(d / "03_과거_광고심의_반려승인_사례집_2026.xlsx", "심의사례_2026", headers, cases)


def generate_scenario2():
    d = OUT_DIR / "scenario2_sales_promo"

    make_html_doc(
        d / "01_2026_하반기_채널별_프로모션_운영정책서.html",
        "Cymbal Beauty & Living 2026 하반기 채널별 프로모션 운영 정책서",
        "문서번호: SLS-PRM-2026-H2 | 주관부서: 영업기획팀 · 채널전략팀",
        [
            ("1. 채널별 최대 할인율 및 승인 권한 기준", [
                "브랜드 가치 보호와 수익성 유지를 위해 모든 유통 채널 프로모션은 아래 할인율 상한과 최소 목표 ROI(투자대비수익률)를 준수해야 합니다.",
                "실제 ROI가 채널별 하한선 미만으로 2주 이상 지속되는 프로모션은 '저조(점검필요)'로 분류되며, 영업기획팀과 브랜드 매니저가 즉시 프로모션 구조(증정품 전환, 할인율 조정)를 재검토해야 합니다.",
            ], [
                ["유통 채널", "기본 할인 상한", "특별행사 상한", "최소 목표 ROI", "승인권자 (상한 초과 시)"],
                ["H&B스토어", "20%", "30% (정기세일)", "200%", "20% 이하 팀장 / 초과 사업부장"],
                ["면세점", "10%", "15% (VIP/시즌)", "150%", "10% 초과 시 부문장 사전 승인 필수"],
                ["백화점", "0% (정가/증정)", "10% (VIP 초대)", "180%", "할인 적용 시 사업부장 승인"],
                ["로켓커머스", "15%", "25% (시즌대전)", "220%", "20% 초과 시 사업부장 승인"],
                ["자사몰/오픈마켓", "15%", "25% (브랜드위크)", "230%", "20% 초과 시 사업부장 승인"],
            ]),
            ("2. 면세점 프레스티지 브랜드(루미에르·페르망) 운영 특별 지침", [
                "면세점 채널은 대량 할인 대신 VIP 기프트 증정 및 전용 에디션 구성을 원칙으로 합니다.",
                "전월 대비 면세점 매출이 20% 이상 하락하고 프로모션 ROI가 150% 미만인 경우, 즉시 원인 분석(단체 관광객 수요 변화, 재고 부족 여부, 환율 영향) 브리프를 작성해 주간 경영회의에 보고해야 합니다.",
            ], None),
        ],
    )

    make_html_doc(
        d / "02_안전재고_및_긴급발주_운영매뉴얼.html",
        "Cymbal Beauty & Living 채널별 안전재고 및 긴급발주 운영 매뉴얼",
        "문서번호: SCM-INV-2026-04 | 주관부서: SCM운영팀 · 물류기획팀",
        [
            ("1. 재고 상태 판정 및 긴급발주 트리거 기준", [
                "모든 핵심 SKU는 채널별 일평균 판매량과 생산 리드타임을 반영한 안전재고(safety_stock_qty)를 보유합니다.",
                "정상: 현재고 >= 안전재고 100% | 주의: 안전재고 50% 이상 ~ 100% 미만 | 긴급발주필요: 현재고 < 안전재고 50%.",
                "긴급발주필요 상태가 감지된 SKU는 영업담당자(MD)가 당일 15:00까지 SCM운영팀에 긴급 물량 배정 또는 타 채널 재고 전환(Transfer)을 요청해야 합니다.",
            ], [
                ["재고 등급", "판정 기준", "필수 대응 액션", "리드타임 목표"],
                ["긴급발주필요", "현재고 < 안전재고의 50%", "긴급 생산/물류 배정 요청 및 타 채널 재고 전환 검토", "48시간 이내 출고"],
                ["주의", "안전재고 50% ~ 99%", "프로모션 잔여 기간 소진 속도 점검 및 선제 발주", "5영업일 이내 입고"],
                ["정상", "현재고 >= 안전재고 100%", "정기 주간 발주 사이클 유지", "표준 리드타임"],
            ]),
            ("2. 대형 행사(H&B 정기세일·로켓커머스 대전) 품절 방지 프로토콜", [
                "정기세일 등 대형 프로모션 기간 중 일 판매량이 평시 대비 50% 이상 급증할 경우, 현재고가 안전재고의 50% 아래로 떨어지기 전이라도 사전 물량 확보(Buffer Allocation)를 발동할 수 있습니다.",
            ], None),
        ],
    )

    make_html_doc(
        d / "03_2026_Q4_핵심브랜드_운영브리프.html",
        "Cymbal Beauty & Living 2026 Q4 핵심 브랜드 채널 운영 브리프",
        "작성일: 2026년 11월 20일 | 작성부서: 사업부 영업기획팀",
        [
            ("1. 루미에르 (LUMIERE) 면세점 동향 및 리스크", [
                "대표 품목인 루미에르 로얄 리페어 에센스 90ml (SKU-LUMI-001)의 11월 면세점 매출이 전월 대비 약 28% 수준으로 둔화되었으며, VIP 기프트 증정 프로모션(PRM-2026-002)의 현재 ROI는 118.4%로 면세점 최소 목표 ROI(150%)를 하회하고 있습니다.",
                "또한 면세점 현재고가 42개로 안전재고(200개)의 21% 수준까지 하락해 긴급발주필요 상태입니다. 원인은 10월 말 해외 물류 선적 지연과 면세 전용 세트 포장재 수급 차질로 파악되며, 백화점 여유 재고 중 100개 긴급 전환을 검토 중입니다.",
            ], None),
            ("2. 베르당 (VERDANT) H&B스토어 정기세일 급증 대응", [
                "베르당 허브 아쿠아 밤 50ml (SKU-VERD-004)는 11월 15일 시작된 H&B 정기세일 단독기획(PRM-2026-001, 할인율 25%, ROI 312.5%) 효과로 일 판매량이 평시 대비 64% 이상 급증했습니다.",
                "11월 22일 기준 H&B스토어 현재고가 85개로 안전재고(300개)의 28.3%에 불과해 행사 종료(11월 24일) 전 품절 위험이 매우 높습니다. SCM운영팀에 48시간 이내 긴급 추가 출고(500개) 요청이 필요합니다.",
            ], None),
            ("3. 더마퓨어 (DERMAPURE) 로켓커머스 성과", [
                "더마퓨어 바이오 베리어 크림 150ml (SKU-DERM-002)는 로켓커머스 가을 보습 대전(PRM-2026-003, 할인율 15%, ROI 278.0%)을 통해 안정적인 고회전 실적을 기록 중이며, 현재고 410개로 안전재고(350개) 이상 정상 유지되고 있습니다.",
            ], None),
        ],
    )


def generate_scenario3():
    d = OUT_DIR / "scenario3_voc_qa"

    make_html_doc(
        d / "01_품질클레임_등급별_대응SOP_v3.html",
        "Cymbal Beauty & Living 고객 VOC 및 품질 클레임 등급별 대응 SOP (v3.2)",
        "문서번호: QA-SOP-2026-03 | 주관부서: 품질보증팀(QA) · 고객상담실(CS)",
        [
            ("1. 클레임 심각도 등급(P1 / P2 / P3) 판정 기준", [
                "모든 고객 VOC는 접수 즉시 심각도 등급을 판정하며, P1-긴급 등급은 4시간 이내 품질보증팀(QA) 및 해당 사업부 담당자에게 1차 보고해야 합니다.",
            ], [
                ["등급", "판정 기준", "초동 응대 SLA", "필수 에스컬레이션 대상"],
                ["P1-긴급", "인체 유해/피부과 진료 수반 트러블, 이물 혼입, 동일 Lot 클레임 10건 이상 집중 발생", "접수 후 4시간 이내", "품질위원회, QA팀장, 사업부장"],
                ["P2-주의", "단발성 용기 파손/누액, 경미한 피부 자극(진료 미수반), 제형/향 이상 문의", "영업일 1일 이내", "CS팀장, 브랜드 담당자"],
                ["P3-일반", "단순 오배송, 사은품 누락, 전성분/사용법 일반 문의", "영업일 2일 이내", "CS 담당자 자체 종결"],
            ]),
            ("2. 동일 Lot 집중 클레임 자동 에스컬레이션 규칙 (중요)", [
                "동일 제품·동일 제조번호(Lot Number)에서 최근 30일 이내 10건 이상의 동일 유형 클레임이 누적될 경우, 개별 건이 경미하더라도 즉시 P1-긴급 품질 이슈로 격상합니다.",
                "예시: 용기 펌프 누액 또는 피부 트러블이 동일 Lot에서 10건 이상 발생 시 (1) 물류센터 해당 Lot 출고 보류(Hold), (2) 생산공장 라인 점검 및 시료 회수, (3) 품질위원회 긴급 소집 보고서 작성을 의무화합니다.",
            ], None),
        ],
    )

    headers = ["클레임유형", "심각도", "기본 보상 기준", "추가 지원 한도", "필수 증빙서류", "표준 고객 회신 핵심 문구"]
    comp_rows = [
        ["피부트러블/알레르기", "P1-긴급", "전액 환불 + 회수", "피부과 진료비·약제비 실비 최대 150,000원", "피부과 진단서/소견서, 진료비 영수증, 구매내역", "사용 중 불편을 드려 진심으로 사과드립니다. 전문의 소견서 확인 후 전액 환불 및 진료비 실비 지원을 신속히 도와드리겠습니다."],
        ["피부트러블/알레르기", "P2-주의", "전액 환불 또는 타 제품 교환", "없음 (무료 반품 수거)", "구매내역, 제품 사진", "피부 컨디션에 맞지 않아 불편하셨을 고객님께 사과드립니다. 무료 회수 후 전액 환불 도와드리겠습니다."],
        ["용기파손/누액", "P1-긴급", "신규 Lot 제품 긴급 재발송 + 사은품", "동일 Lot 10건 이상 시 품질위원회 보고", "파손/누액 사진, 제품 하단 Lot 번호", "제품 용기 이상으로 불편을 드려 죄송합니다. 확인된 제조번호는 품질팀에 즉시 공유했으며, 검수 완료된 정상 제품으로 오늘 바로 재발송해 드리겠습니다."],
        ["용기파손/누액", "P2-주의", "1:1 무료 교환 또는 환불", "없음 (무료 수거)", "파손 사진, 송장번호", "배송 중 파손으로 불편을 드려 죄송합니다. 새 제품으로 신속히 교환 출고해 드리겠습니다."],
        ["향/제형이상", "P2-주의", "제품 회수(QA 분석) + 새 제품 교환", "QA 분석 결과 회신 (7영업일 이내)", "Lot 번호, 개봉일시", "제형 변화에 대한 염려를 드려 죄송합니다. 해당 제품은 품질연구소 정밀 검사를 위해 회수하고 새 제품으로 교환해 드리겠습니다."],
        ["오배송/누락", "P3-일반", "누락분 즉시 발송 / 오배송 맞교환", "없음", "주문번호, 수령 사진", "주문하신 상품과 다르게 배송되어 죄송합니다. 누락/정상 상품을 즉시 출고해 드리겠습니다."],
    ]
    make_xlsx(d / "02_고객VOC_보상기준표_및_응대스크립트.xlsx", "보상기준_응대스크립트", headers, comp_rows)

    make_html_doc(
        d / "03_주요제품_성분_알레르기_FAQ_가이드.html",
        "Cymbal Beauty & Living 주요 제품 성분 및 민감성 피부 FAQ 가이드",
        "문서번호: CS-FAQ-2026-05 | 주관부서: 고객상담실 · 기술연구원",
        [
            ("1. 더마퓨어 바이오 베리어 크림 (SKU-DERM-002) 민감성 피부 안내", [
                "핵심 성분: 바이오세라마이드 복합체(세라마이드NP, 스쿠알란, 마데카소사이드). 인공향료·색소 무첨가 포뮬러입니다.",
                "FAQ: 민감성 피부에서 일시적 따가움이 발생하는 경우 — 피부 장벽이 극도로 손상된 상태에서 고보습 크림 도포 시 일시적 열감이나 따가움이 나타날 수 있습니다. 증상이 24시간 이상 지속되거나 붉어짐이 동반될 경우 즉시 사용을 중단하고 피부과 전문의 상담을 안내하며, P1/P2 보상 기준에 따라 환불 및 진료비 지원 절차를 안내합니다.",
            ], None),
            ("2. 루트케어 바이오틴 탈모증상완화 샴푸 (SKU-ROOT-001) 성분 및 용기 안내", [
                "핵심 기능성 성분: 살리실릭애씨드, 덱스판테놀, 나이아신아마이드 (식약처 보고 완료 탈모증상완화 기능성).",
                "FAQ: 임산부 사용 가능 여부 — 살리실릭애씨드(BHA) 성분이 미량 함유되어 있으므로, 임산부 및 수유부는 안전을 위해 담당 산부인과 전문의와 상담 후 사용을 권장합니다.",
                "FAQ: 펌프 누액 접수 시 필수 확인 사항 — 용기 하단 14자리 제조번호(예: LOT-202610-D01)를 반드시 수집하여 BigQuery VOC 이력에서 동일 Lot 누적 건수를 확인해야 합니다.",
            ], None),
            ("3. 루미에르 로얄 리페어 에센스 (SKU-LUMI-001) & 베르당 아쿠아 밤 (SKU-VERD-004)", [
                "루미에르 로얄 리페어 에센스: 식물 배양 추출물 및 천연 유래 향료가 포함되어 있으므로, 특정 허브 성분에 알레르기 이력이 있는 고객은 팔 안쪽 패치 테스트 후 사용을 권장합니다.",
                "베르당 아쿠아 밤: 에센셜 오일 계열 천연 향 성분이 소량 포함되어 있어, 민감성 고객 문의 시 전성분표 제공 및 무료 샘플 테스트를 안내합니다.",
            ], None),
        ],
    )


def main():
    generate_scenario1()
    generate_scenario2()
    generate_scenario3()
    files = sorted(str(p.relative_to(OUT_DIR)) for p in OUT_DIR.rglob("*") if p.is_file())
    print(json.dumps({"generated_docs_count": len(files), "files": files}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
