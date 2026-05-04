"""
從職安署「職災案例宣導」頁面下載真實事故案例 PDF，
合併成職災典型案例摘要集 PDF。

流程：
1. 爬取 osha.gov.tw/48110/48417/48427/lpsimplelist（前 N 頁）
2. 依標題關鍵字分類為 5 類事故（工地墜落、搬運、化學品/感電、機械傷害、過勞/職業病）
3. 每類取 3 個代表案例下載 PDF
4. 在合併 PDF 前加入封面頁（案例標題、發布單位、日期）
5. 用 pypdf 合併所有案例 PDF → 輸出單一 PDF

輸出：
  資料/2_自製整理/案例彙編_教學參考.pdf
  資料/3_EAP上傳/PDF/案例彙編_教學參考.pdf
"""
import io
import re
import sys
import tempfile
import time
from pathlib import Path

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from bs4 import BeautifulSoup

import pypdf
from pypdf import PdfWriter

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_PATH))

OSHA_BASE = "https://www.osha.gov.tw"
LIST_URL  = f"{OSHA_BASE}/48110/48417/48427/lpsimplelist"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

OUT_SELF = Path(__file__).parent.parent / "資料" / "2_自製整理"
OUT_EAP  = Path(__file__).parent.parent / "資料" / "3_EAP上傳" / "PDF"
OUT_NAME = "案例彙編_教學參考.pdf"
MIN_CASES = 6   # 至少要幾個案例才輸出

# 5 類事故的標題關鍵字分類（依本專案的事故 ID 對應）
CATEGORIES: list[tuple[str, str, list[str]]] = [
    ("A002", "工地墜落",  ["墜落", "施工架", "鷹架", "高處", "屋頂", "開口"]),
    ("A003", "搬運受傷",  ["搬運", "物料", "卸貨", "吊掛", "倒塌", "崩塌"]),
    ("A004", "化學品與感電", ["感電", "爆炸", "化學", "有機溶劑", "氣體", "焊接", "燃燒"]),
    ("A001", "機械與車輛", ["輾壓", "夾捲", "被撞", "鏟裝", "起重機", "車"]),
    ("A005", "過勞與職業病", ["過勞", "職業病", "猝死", "腦血管", "心臟", "蜂螫", "溺"]),
]
MAX_PER_CAT = 3   # 每類最多幾個案例
MAX_PAGES   = 8   # 最多爬幾頁（每頁 20 筆，約 160 筆候選）

styles = getSampleStyleSheet()
cover_title = ParagraphStyle("CT", parent=styles["Heading1"], fontName="CJK", fontSize=20, leading=28)
h2_style    = ParagraphStyle("H2", parent=styles["Heading2"], fontName="CJK", fontSize=14, leading=22,
                              textColor="#1a4480")
meta_style  = ParagraphStyle("M",  parent=styles["BodyText"],  fontName="CJK", fontSize=9,  leading=14,
                              textColor="#555555")
body_style  = ParagraphStyle("B",  parent=styles["BodyText"],  fontName="CJK", fontSize=10, leading=16)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def scrape_list(pages: int = MAX_PAGES) -> list[dict]:
    """Scrape case list items → [{title, pdf_url, unit, date}]."""
    items = []
    for page in range(1, pages + 1):
        url = f"{LIST_URL}?page={page}&pageSize=20"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            resp.raise_for_status()
        except Exception as e:
            print(f"  ✗ 清單 p{page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        blocks = soup.select("div.item_list2")
        if not blocks:
            break

        for block in blocks:
            link = block.select_one("div.item_title a")
            if not link:
                continue
            title  = link.get_text(strip=True)
            href   = link.get("href", "")
            if not href.startswith("http"):
                href = OSHA_BASE + href
            # Remove mediaDL=true redirect if any
            if "?" in href and "mediaDL" in href:
                pass  # keep as-is, it's the direct download link

            spans = block.select("div.data span")
            unit = date = ""
            for span in spans:
                t = span.get_text(strip=True)
                if t.startswith("發布單位"):
                    unit = t.replace("發布單位：", "").strip()
                elif t.startswith("發布日期"):
                    date = t.replace("發布日期：", "").strip()
            items.append({"title": title, "pdf_url": href, "unit": unit, "date": date})

        time.sleep(0.3)
        print(f"  清單 p{page}：累計 {len(items)} 筆")
    return items


def classify(items: list[dict]) -> dict[str, list[dict]]:
    """Assign each item to a category."""
    buckets: dict[str, list[dict]] = {cat_id: [] for cat_id, _, _ in CATEGORIES}
    for item in items:
        for cat_id, _, keywords in CATEGORIES:
            if any(kw in item["title"] for kw in keywords):
                if len(buckets[cat_id]) < MAX_PER_CAT:
                    item["cat_id"] = cat_id
                    buckets[cat_id].append(item)
                break  # assign to first matching category only
    return buckets


def download_pdf(url: str) -> bytes | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, verify=False)
        resp.raise_for_status()
        if "application/pdf" in resp.headers.get("Content-Type", "") or url.lower().endswith(".pdf"):
            return resp.content
    except Exception as e:
        print(f"    ✗ 下載失敗：{e}")
    return None


def make_divider_page(cat_name: str, items: list[dict]) -> bytes:
    """Build a single ReportLab page as category header."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = [
        Paragraph(esc(cat_name), h2_style),
        Spacer(1, 0.2*cm),
    ]
    for i, item in enumerate(items, 1):
        story.append(Paragraph(esc(f"{i}. {item['title']}"), body_style))
        story.append(Paragraph(esc(f"   發布：{item['unit']}　日期：{item['date']}"), meta_style))
    doc.build(story)
    buf.seek(0)
    return buf.read()


def build_cover(cat_summary: dict[str, tuple[str, list[dict]]], total: int) -> bytes:
    """Build cover page listing all categories and case counts."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=3*cm, bottomMargin=2*cm)
    story = [
        Paragraph("職災典型案例摘要集", cover_title),
        Spacer(1, 0.3*cm),
        Paragraph(esc(f"資料來源：勞動部職業安全衛生署職災案例宣導 www.osha.gov.tw"), meta_style),
        Paragraph(esc(f"收錄案例：{total} 份真實職災事故調查報告"), meta_style),
        Spacer(1, 0.5*cm),
    ]
    for cat_id, (cat_name, items) in cat_summary.items():
        story.append(Paragraph(esc(f"▌ {cat_id} {cat_name}（{len(items)} 件）"), h2_style))
        for i, item in enumerate(items, 1):
            story.append(Paragraph(esc(f"  {i}. {item['title']}"), body_style))
            story.append(Paragraph(esc(f"     {item['unit']}　{item['date']}"), meta_style))
        story.append(Spacer(1, 0.3*cm))
    doc.build(story)
    buf.seek(0)
    return buf.read()


def merge_pdfs(pdf_blobs: list[bytes]) -> bytes:
    writer = PdfWriter()
    for blob in pdf_blobs:
        try:
            reader = pypdf.PdfReader(io.BytesIO(blob))
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            print(f"    ⚠ 跳過損壞 PDF：{e}")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def main():
    print("=== 爬取職安署職災案例 ===")

    print("\n[1] 爬取清單...")
    all_items = scrape_list()
    print(f"  總計：{len(all_items)} 筆")

    print("\n[2] 分類...")
    buckets = classify(all_items)
    for cat_id, _, _ in CATEGORIES:
        cat_name = next(n for cid, n, _ in CATEGORIES if cid == cat_id)
        print(f"  {cat_id} {cat_name}：{len(buckets[cat_id])} 筆")

    total_cases = sum(len(v) for v in buckets.values())
    if total_cases < MIN_CASES:
        print(f"  ✗ 案例不足（{total_cases} < {MIN_CASES}），中止。", file=sys.stderr)
        sys.exit(1)

    print("\n[3] 下載 PDF...")
    cat_summary: dict[str, tuple[str, list[dict]]] = {}
    pdf_blobs: list[bytes] = []

    for cat_id, cat_name, _ in CATEGORIES:
        items = buckets[cat_id]
        if not items:
            continue
        cat_summary[cat_id] = (cat_name, items)
        # category divider page
        divider = make_divider_page(f"{cat_id} {cat_name}", items)
        pdf_blobs.append(divider)
        for item in items:
            print(f"  下載：{item['title'][:50]}…")
            blob = download_pdf(item["pdf_url"])
            if blob:
                pdf_blobs.append(blob)
                print(f"    ✓ {len(blob):,} bytes")
            else:
                print(f"    ✗ 跳過")
            time.sleep(0.3)

    if not pdf_blobs:
        print("  ✗ 無可用 PDF，中止。", file=sys.stderr)
        sys.exit(1)

    print("\n[4] 合併 PDF...")
    # prepend cover
    cover = build_cover(cat_summary, sum(len(v) for _, v in cat_summary.values()))
    merged = merge_pdfs([cover] + pdf_blobs)
    print(f"  合併後大小：{len(merged):,} bytes")

    print("\n[5] 寫出...")
    for out_dir in (OUT_SELF, OUT_EAP):
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / OUT_NAME
        with tempfile.NamedTemporaryFile(dir=out_dir, suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            tmp_path.write_bytes(merged)
            tmp_path.replace(out_path)
            print(f"  ✓ {out_path}（{len(merged):,} bytes）")
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise


if __name__ == "__main__":
    main()
