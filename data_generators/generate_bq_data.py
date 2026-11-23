#!/usr/bin/env python3
"""Deterministic medium-scale synthetic BigQuery dataset generator for Cymbal Beauty & Living (CBL).

Generates 4 relational CSV files (6,460 rows total) with strict FK integrity and embedded Hero scenarios,
plus a 12-row marketing campaign draft CSV for Google Antigravity (agy) batch audit exercises:
  1. generated_data/csv/products_master.csv           (120 rows)
  2. generated_data/csv/channel_sales_inventory.csv   (3,600 rows)
  3. generated_data/csv/promotions_calendar.csv       (240 rows)
  4. generated_data/csv/voc_quality_claims.csv        (2,500 rows)
  5. agy_workspace/samples/campaign_copies_draft.csv  (12 rows)
"""

import csv
import datetime
import json
import random
from pathlib import Path

SEED = 20261123
random.seed(SEED)

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT_DIR / "generated_data" / "csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)
AGY_SAMPLES_DIR = ROOT_DIR / "agy_workspace" / "samples"
AGY_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

BRANDS = [
    ("LUMI", "루미에르", "Beauty", "프레스티지 스킨케어", 145000, "골든실크펩타이드, 인삼배양추출물, 나이아신아마이드", "기능성(주름/미백)"),
    ("VERD", "베르당", "Beauty", "허브 수분 코스메틱", 48000, "컴프리리프추출물, 레이디스맨틀, 판테놀", "일반화장품"),
    ("DERM", "더마퓨어", "Beauty", "더마 코스메틱", 34000, "바이오세라마이드 복합체, 스쿠알란, 마데카소사이드", "일반화장품(민감성)"),
    ("FERM", "페르망", "Beauty", "발효 스킨케어", 98000, "마이크로발효효모액, 히알루론산, 아데노신", "기능성(주름개선)"),
    ("CELL", "셀라쥬", "Beauty", "안티에이징 스킨케어", 112000, "리커버리펩타이드, 레티놀 유도체, 토코페롤", "기능성(주름/미백)"),
    ("ROOT", "루트케어", "HDB", "기능성 헤어케어", 24000, "비오틴, 카페인, 살리실릭애씨드, 덱스판테놀", "기능성(탈모증상완화)"),
    ("MINT", "퓨어민트", "HDB", "프리미엄 오럴케어", 12900, "티몰, 유칼립톨, 불소 1000ppm", "의약외품"),
    ("WAVE", "클린웨이브", "HDB", "패브릭케어", 16500, "7종 효소복합체, 베이킹소다, 식물유래계면활성제", "생활화학제품"),
    ("SPRK", "스파크제로", "Refreshment", "제로 탄산음료", 2200, "정제수, 탄산가스, 에리스리톨, 천연시트러스향", "식품(음료)"),
    ("HYDR", "하이드라텐", "Refreshment", "수분보충 이온음료", 1900, "복합과채수분추출액, 비타민B군, 구연산나트륨", "식품(음료)"),
]

CHANNELS = [
    "H&B스토어",
    "백화점",
    "면세점",
    "자사몰",
    "로켓커머스",
    "오픈마켓스토어",
]

HERO_PRODUCTS = [
    ("SKU-LUMI-001", "루미에르", "Beauty", "루미에르 로얄 리페어 에센스 90ml", "에센스", 210000, 200, "2024-03-15", "골든실크펩타이드, 인삼배양추출물, 나이아신아마이드", "기능성(주름/미백)"),
    ("SKU-VERD-004", "베르당", "Beauty", "베르당 허브 아쿠아 밤 50ml", "수분크림", 48000, 300, "2024-05-01", "레이디스맨틀, 판테놀, 글리세린", "일반화장품"),
    ("SKU-DERM-002", "더마퓨어", "Beauty", "더마퓨어 바이오 베리어 크림 150ml", "보습크림", 36000, 350, "2023-09-10", "바이오세라마이드 복합체, 세라마이드NP, 스쿠알란", "일반화장품(민감성)"),
    ("SKU-ROOT-001", "루트케어", "HDB", "루트케어 바이오틴 탈모증상완화 샴푸 680ml", "샴푸", 28000, 400, "2024-08-20", "살리실릭애씨드, 덱스판테놀, 나이아신아마이드", "기능성(탈모증상완화)"),
    ("SKU-FERM-001", "페르망", "Beauty", "페르망 마이크로 발효 에센스 150ml", "에센스", 135000, 150, "2024-01-10", "마이크로발효효모액, 페룰릭애씨드", "기능성(주름개선)"),
    ("SKU-MINT-001", "퓨어민트", "HDB", "퓨어민트 화이트닝 퍼플코렉터 치약 106g", "치약", 13900, 500, "2025-02-01", "메타인산나트륨, 불소, 페퍼민트오일", "의약외품"),
]


def generate_products():
    rows = []
    seen = set()
    for p in HERO_PRODUCTS:
        rows.append({
            "sku_id": p[0],
            "brand": p[1],
            "division": p[2],
            "product_name": p[3],
            "category": p[4],
            "unit_price_krw": p[5],
            "safety_stock_qty": p[6],
            "launch_date": p[7],
            "key_ingredients": p[8],
            "ra_claim_grade": p[9],
        })
        seen.add(p[0])

    variants = ["스탠다드", "대용량 기획", "리필 세트", "트래블 키트", "프리미엄 에디션", "민감성 전용", "프레시", "인텐시브", "모이스처", "데일리", "나이트케어", "스페셜 듀오"]
    idx = 1
    while len(rows) < 120:
        code, brand, div, cat, base_price, ingr, grade = BRANDS[idx % len(BRANDS)]
        num = (idx // len(BRANDS)) + 10
        sku_id = f"SKU-{code}-{num:03d}"
        idx += 1
        if sku_id in seen:
            continue
        seen.add(sku_id)
        var = variants[len(rows) % len(variants)]
        price = int(base_price * random.uniform(0.75, 1.35) // 100 * 100)
        safety = random.choice([120, 150, 200, 250, 300, 400, 500])
        launch = datetime.date(2023, 1, 1) + datetime.timedelta(days=random.randint(0, 1000))
        rows.append({
            "sku_id": sku_id,
            "brand": brand,
            "division": div,
            "product_name": f"{brand} {cat} {var}",
            "category": cat,
            "unit_price_krw": price,
            "safety_stock_qty": safety,
            "launch_date": launch.isoformat(),
            "key_ingredients": ingr,
            "ra_claim_grade": grade,
        })

    out = OUT_DIR / "products_master.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def generate_sales_inventory(products):
    end_date = datetime.date(2026, 11, 22)
    start_date = end_date - datetime.timedelta(days=119)

    prod_map = {p["sku_id"]: p for p in products}
    hero_pairs = [
        ("SKU-LUMI-001", "면세점"),
        ("SKU-LUMI-001", "백화점"),
        ("SKU-VERD-004", "H&B스토어"),
        ("SKU-VERD-004", "자사몰"),
        ("SKU-DERM-002", "로켓커머스"),
        ("SKU-DERM-002", "H&B스토어"),
        ("SKU-ROOT-001", "로켓커머스"),
        ("SKU-ROOT-001", "오픈마켓스토어"),
        ("SKU-FERM-001", "백화점"),
        ("SKU-MINT-001", "H&B스토어"),
    ]
    other_skus = [p["sku_id"] for p in products[6:26]]
    pairs = list(hero_pairs)
    for i, sku in enumerate(other_skus):
        pairs.append((sku, CHANNELS[i % len(CHANNELS)]))

    rows = []
    rec_id = 1
    for day_offset in range(120):
        dt = start_date + datetime.timedelta(days=day_offset)
        is_nov = dt >= datetime.date(2026, 11, 1)
        is_recent = dt >= datetime.date(2026, 11, 15)
        for sku_id, channel in pairs:
            p = prod_map[sku_id]
            price = p["unit_price_krw"]
            safety = p["safety_stock_qty"]

            base_units = random.randint(25, 95)
            stock_qty = random.randint(int(safety * 1.1), int(safety * 2.4))
            promo_applied = "N"
            discount_pct = 0.0

            if sku_id == "SKU-LUMI-001" and channel == "면세점":
                if is_nov:
                    base_units = random.randint(18, 28)
                    stock_qty = 42 if dt == end_date else random.randint(45, 95)
                else:
                    base_units = random.randint(30, 42)
                    stock_qty = random.randint(220, 340)
            elif sku_id == "SKU-VERD-004" and channel == "H&B스토어":
                if is_recent:
                    base_units = random.randint(120, 165)
                    promo_applied = "Y"
                    discount_pct = 25.0
                    stock_qty = 85 if dt == end_date else random.randint(90, 180)
                else:
                    base_units = random.randint(70, 95)
                    stock_qty = random.randint(350, 520)
            elif sku_id == "SKU-DERM-002" and channel == "로켓커머스":
                base_units = random.randint(110, 155)
                if is_nov:
                    promo_applied = "Y"
                    discount_pct = 15.0
                stock_qty = 410 if dt == end_date else random.randint(380, 620)
            else:
                if day_offset % 14 in (0, 1, 2):
                    promo_applied = "Y"
                    discount_pct = random.choice([10.0, 15.0, 20.0])
                    base_units = int(base_units * 1.25)

            gross_rev = int(base_units * price * (1.0 - discount_pct / 100.0))
            stock_status = "긴급발주필요" if stock_qty < safety * 0.5 else ("주의" if stock_qty < safety else "정상")

            rows.append({
                "record_id": f"SL-{rec_id:06d}",
                "sales_date": dt.isoformat(),
                "sku_id": sku_id,
                "brand": p["brand"],
                "division": p["division"],
                "channel": channel,
                "units_sold": base_units,
                "revenue_krw": gross_rev,
                "ending_stock_qty": stock_qty,
                "safety_stock_qty": safety,
                "stock_status": stock_status,
                "promo_applied": promo_applied,
                "discount_rate_pct": discount_pct,
            })
            rec_id += 1

    out = OUT_DIR / "channel_sales_inventory.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def generate_promotions(products):
    rows = [
        {
            "promo_id": "PRM-2026-001",
            "promo_name": "2026 11월 H&B 정기세일 베르당 아쿠아밤 단독기획",
            "sku_id": "SKU-VERD-004",
            "brand": "베르당",
            "channel": "H&B스토어",
            "start_date": "2026-11-15",
            "end_date": "2026-11-24",
            "discount_rate_pct": 25.0,
            "budget_krw": 85000000,
            "actual_roi_pct": 312.5,
            "approval_level": "사업부장 승인",
            "status": "진행중",
        },
        {
            "promo_id": "PRM-2026-002",
            "promo_name": "루미에르 면세점 VIP 기프트 증정 프로모션",
            "sku_id": "SKU-LUMI-001",
            "brand": "루미에르",
            "channel": "면세점",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
            "discount_rate_pct": 10.0,
            "budget_krw": 120000000,
            "actual_roi_pct": 118.4,
            "approval_level": "부문장 승인",
            "status": "저조(점검필요)",
        },
        {
            "promo_id": "PRM-2026-003",
            "promo_name": "더마퓨어 로켓커머스 가을 보습 대전",
            "sku_id": "SKU-DERM-002",
            "brand": "더마퓨어",
            "channel": "로켓커머스",
            "start_date": "2026-11-01",
            "end_date": "2026-11-25",
            "discount_rate_pct": 15.0,
            "budget_krw": 65000000,
            "actual_roi_pct": 278.0,
            "approval_level": "팀장 승인",
            "status": "진행중",
        },
    ]

    promo_themes = ["시즌 기획전", "브랜드 위크", "신제품 런칭 특가", "멤버십 데이", "라이브 커머스 특가", "연말 홀리데이 세트"]
    for i in range(4, 241):
        p = products[i % len(products)]
        ch = CHANNELS[i % len(CHANNELS)]
        start = datetime.date(2026, 1, 5) + datetime.timedelta(days=random.randint(0, 310))
        end = start + datetime.timedelta(days=random.randint(5, 20))
        disc = random.choice([10.0, 15.0, 20.0, 25.0, 30.0])
        budget = random.randint(15, 110) * 1000000
        roi = round(random.uniform(115.0, 340.0), 1)
        appr = "팀장 승인" if disc <= 20.0 else "사업부장 승인"
        status = "완료" if end < datetime.date(2026, 11, 22) else "진행중"
        rows.append({
            "promo_id": f"PRM-2026-{i:03d}",
            "promo_name": f"2026 {p['brand']} {ch} {promo_themes[i % len(promo_themes)]}",
            "sku_id": p["sku_id"],
            "brand": p["brand"],
            "channel": ch,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "discount_rate_pct": disc,
            "budget_krw": budget,
            "actual_roi_pct": roi,
            "approval_level": appr,
            "status": status,
        })

    out = OUT_DIR / "promotions_calendar.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def generate_voc_claims(products):
    rows = []
    # Hero Cluster 1: 18 pump leakage claims on LOT-202610-D01 (SKU-ROOT-001) -> triggers SOP >= 10 same-Lot P1 escalation!
    for i in range(1, 19):
        dt = datetime.date(2026, 11, 3) + datetime.timedelta(days=(i % 18))
        rows.append({
            "claim_id": f"VOC-2026-{i:05d}",
            "received_date": dt.isoformat(),
            "sku_id": "SKU-ROOT-001",
            "brand": "루트케어",
            "division": "HDB",
            "channel": random.choice(["로켓커머스", "오픈마켓스토어", "자사몰"]),
            "claim_type": "용기파손/누액",
            "severity": "P1-긴급" if i <= 6 else "P2-주의",
            "lot_number": "LOT-202610-D01",
            "summary": "배송 수령 시 샴푸 펌프 헤드 결합부 풀림으로 내용물 누액 발생",
            "resolution_status": "품질위원회 에스컬레이션" if i <= 6 else "교환처리완료",
            "compensation_krw": 28000,
        })

    # Hero Cluster 2: 12 skin irritation VOCs on SKU-DERM-002 LOT-202610-P02
    for j in range(19, 31):
        dt = datetime.date(2026, 11, 5) + datetime.timedelta(days=(j % 16))
        rows.append({
            "claim_id": f"VOC-2026-{j:05d}",
            "received_date": dt.isoformat(),
            "sku_id": "SKU-DERM-002",
            "brand": "더마퓨어",
            "division": "Beauty",
            "channel": random.choice(["H&B스토어", "로켓커머스"]),
            "claim_type": "피부트러블/알레르기",
            "severity": "P1-긴급" if j <= 22 else "P2-주의",
            "lot_number": "LOT-202610-P02",
            "summary": "민감성 피부 도포 후 일시적 붉어짐 및 따가움 호소, 피부과 소견서 제출 문의",
            "resolution_status": "진료비심사중" if j <= 22 else "환불완료",
            "compensation_krw": 86000 if j <= 22 else 36000,
        })

    claim_types = [
        ("오배송/누락", "P3-일반", "주문 옵션과 상이한 용량 또는 사은품 누락 문의"),
        ("용기파손/누액", "P2-주의", "외박스 찌그러짐 및 캡 미세 누액 접수"),
        ("피부트러블/알레르기", "P2-주의", "사용 초기 가려움 및 트러블 반응으로 반품 요청"),
        ("향/제형이상", "P2-주의", "기존 사용 제품 대비 제형 점도 및 향 미세 차이 문의"),
        ("표시광고문의", "P3-일반", "전성분 표기 및 임산부 사용 가능 여부 확인 요청"),
    ]

    for k in range(31, 2501):
        p = products[k % len(products)]
        ctype, sev, desc = random.choices(claim_types, weights=[35, 22, 18, 12, 13], k=1)[0]
        dt = datetime.date(2026, 1, 1) + datetime.timedelta(days=random.randint(0, 325))
        lot_ym = dt.strftime("%Y%m")
        lot = f"LOT-{lot_ym}-{p['sku_id'].split('-')[1][:2]}{random.randint(1, 5)}"
        status = random.choice(["처리완료", "교환처리완료", "환불완료", "상담종결"])
        comp = 0 if status == "상담종결" else p["unit_price_krw"]
        rows.append({
            "claim_id": f"VOC-2026-{k:05d}",
            "received_date": dt.isoformat(),
            "sku_id": p["sku_id"],
            "brand": p["brand"],
            "division": p["division"],
            "channel": random.choice(CHANNELS),
            "claim_type": ctype,
            "severity": sev,
            "lot_number": lot,
            "summary": f"{p['product_name']} - {desc}",
            "resolution_status": status,
            "compensation_krw": comp,
        })

    out = OUT_DIR / "voc_quality_claims.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def generate_agy_batch_copies():
    copies = [
        {"copy_id": "CP-001", "sku_id": "SKU-DERM-002", "brand": "더마퓨어", "channel": "H&B스토어", "draft_copy": "아토피와 피부염을 완벽하게 치료하고 부작용 제로인 저자극 더마 크림", "has_clinical_footnote": "N"},
        {"copy_id": "CP-002", "sku_id": "SKU-LUMI-001", "brand": "루미에르", "channel": "자사몰", "draft_copy": "바르는 순간 손상된 피부 세포를 100% 재생시키는 기적의 리페어 에센스", "has_clinical_footnote": "N"},
        {"copy_id": "CP-003", "sku_id": "SKU-VERD-004", "brand": "베르당", "channel": "H&B스토어", "draft_copy": "단 1회 사용으로 보습력 145% 개선! 48시간 촉촉한 수분 폭탄 크림", "has_clinical_footnote": "N"},
        {"copy_id": "CP-004", "sku_id": "SKU-ROOT-001", "brand": "루트케어", "channel": "로켓커머스", "draft_copy": "2주 만에 머리카락이 새로 자라는 탈모 치료 발모 샴푸", "has_clinical_footnote": "N"},
        {"copy_id": "CP-005", "sku_id": "SKU-FERM-001", "brand": "페르망", "channel": "면세점", "draft_copy": "마이크로 발효 성분이 외부 자극으로 거칠어진 피부결을 편안하게 진정시켜 줍니다", "has_clinical_footnote": "Y"},
        {"copy_id": "CP-006", "sku_id": "SKU-MINT-001", "brand": "퓨어민트", "channel": "오픈마켓스토어", "draft_copy": "단 3일 양치로 치아 미백 완성 및 충치 100% 완벽 예방", "has_clinical_footnote": "N"},
        {"copy_id": "CP-007", "sku_id": "SKU-DERM-002", "brand": "더마퓨어", "channel": "로켓커머스", "draft_copy": "피부과 전문의 지정 스테로이드 대체 보습 치료제", "has_clinical_footnote": "N"},
        {"copy_id": "CP-008", "sku_id": "SKU-VERD-004", "brand": "베르당", "channel": "자사몰", "draft_copy": "단 1회 사용으로 피부 보습량 145% 개선 (한국피부임상센터, 2026.08, 성인여성 32명, 개인차 있음)", "has_clinical_footnote": "Y"},
    ]
    out = AGY_SAMPLES_DIR / "campaign_copies_draft.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(copies[0].keys()))
        writer.writeheader()
        writer.writerows(copies)
    return copies


def main():
    products = generate_products()
    sales = generate_sales_inventory(products)
    promos = generate_promotions(products)
    voc = generate_voc_claims(products)
    copies = generate_agy_batch_copies()

    summary = {
        "products_master": len(products),
        "channel_sales_inventory": len(sales),
        "promotions_calendar": len(promos),
        "voc_quality_claims": len(voc),
        "total_bq_rows": len(products) + len(sales) + len(promos) + len(voc),
        "agy_campaign_copies": len(copies),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
