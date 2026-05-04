"""
從職安署網站下載「高職災與高違規廠場列管名冊」並轉存為 PDF。

流程：
1. GET https://www.osha.gov.tw/1106/1164/1165/ 解析頁面
2. 若找到 Excel 連結 → 下載 → 用 ReportLab 轉 PDF
3. 若找到 PDF 連結  → 直接下載覆蓋
4. 若都找不到     → 查 data.gov.tw 開放資料，印出結果提示手動下載

輸出：資料/3_EAP上傳/PDF/C_職安署_高職災與高違規廠場列管名冊.pdf
"""

import io
import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ── ReportLab ──
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# ── openpyxl ──
import openpyxl

# ────────────────────────────────────────────────
OSHA_URL = "https://www.osha.gov.tw/1106/1164/1165/"
DATA_GOV_URL = "https://data.gov.tw/api/v2/rest/dataset"
GOVDATA_KEYWORD = "高職災廠場"

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_PATH))

OUT_PDF = (
    Path(__file__).parent.parent
    / "資料" / "3_EAP上傳" / "PDF"
    / "C_職安署_高職災與高違規廠場列管名冊.pdf"
)
OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# 判斷連結是否為目標文件（列管名冊）
LIST_KEYWORDS = ["列管", "名冊", "高職災", "高違規", "廠場"]


def is_target_link(text: str, href: str) -> bool:
    combined = (text + href).lower()
    return any(kw in combined for kw in LIST_KEYWORDS)


def download_bytes(url: str) -> bytes:
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.content


def excel_to_pdf(excel_bytes: bytes, out_path: Path):
    """將 Excel 內容轉成 ReportLab 表格 PDF。"""
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
    ws = wb.active

    rows = []
    for row in ws.iter_rows(values_only=True):
        # 過濾全空列
        if any(cell is not None for cell in row):
            rows.append([str(c) if c is not None else "" for c in row])

    if not rows:
        print("  ⚠ Excel 無資料，PDF 未輸出")
        return

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CJKTitle", parent=styles["Heading1"],
        fontName="CJK", fontSize=16, leading=22
    )
    body_style = ParagraphStyle(
        "CJKBody", parent=styles["BodyText"],
        fontName="CJK", fontSize=8, leading=12
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    # 表格 cell 用 Paragraph 包裝以支援自動換行
    table_data = []
    for r_idx, row in enumerate(rows):
        table_row = []
        for cell in row:
            style = body_style
            p = Paragraph(cell.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)
            table_row.append(p)
        table_data.append(table_row)

    col_count = max(len(r) for r in table_data)
    page_width = landscape(A4)[0] - 3 * cm  # usable width
    col_width = page_width / col_count

    table = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "CJK"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#dce6f1")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    story = [
        Paragraph("職安署 高職災與高違規廠場列管名冊", title_style),
        Paragraph("資料來源：職安署 https://www.osha.gov.tw/1106/1164/1165/", body_style),
        Spacer(1, 0.5 * cm),
        table,
    ]
    doc.build(story)
    print(f"  ✓ PDF（由 Excel 轉換）：{out_path}（{len(rows)} 列）")


def fallback_data_gov():
    """查 data.gov.tw 開放資料平台。"""
    print("\n  ⚠ 未找到可下載連結，嘗試 data.gov.tw 開放資料 ...")
    params = {"keyword": GOVDATA_KEYWORD, "size": 5}
    try:
        resp = requests.get(DATA_GOV_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("result", {}).get("results", [])
        if results:
            print(f"  找到 {len(results)} 筆相關資料集：")
            for ds in results:
                print(f"    - {ds.get('title', '(無標題)')}")
                print(f"      URL: {ds.get('landingPage', '')}")
        else:
            print("  data.gov.tw 也未找到相關資料集。")
        print("\n請手動下載後存至：")
        print(f"  {OUT_PDF}")
    except Exception as e:
        print(f"  data.gov.tw 查詢失敗：{e}")
        print("\n請手動前往以下網址下載：")
        print(f"  {OSHA_URL}")
        print(f"  存至：{OUT_PDF}")


def main():
    print(f"GET {OSHA_URL} ...")
    try:
        resp = requests.get(OSHA_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ✗ 無法取得頁面：{e}")
        fallback_data_gov()
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    # 找所有 <a> 連結
    excel_url = None
    pdf_url = None

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        full_url = urljoin(OSHA_URL, href)

        if not is_target_link(text, href):
            continue

        ext = href.lower().split("?")[0]
        if excel_url is None and (ext.endswith(".xlsx") or ext.endswith(".xls")):
            excel_url = full_url
            print(f"  找到 Excel：{full_url}")
        elif pdf_url is None and ext.endswith(".pdf"):
            pdf_url = full_url
            print(f"  找到 PDF：{full_url}")

    # ── 優先下載 Excel 轉 PDF ──
    if excel_url:
        print(f"  下載 Excel：{excel_url}")
        try:
            excel_bytes = download_bytes(excel_url)
            excel_to_pdf(excel_bytes, OUT_PDF)
            return
        except Exception as e:
            print(f"  ✗ Excel 下載/轉換失敗：{e}")

    # ── 其次直接下載 PDF ──
    if pdf_url:
        print(f"  下載 PDF：{pdf_url}")
        try:
            pdf_bytes = download_bytes(pdf_url)
            OUT_PDF.write_bytes(pdf_bytes)
            print(f"  ✓ PDF 已儲存：{OUT_PDF}（{len(pdf_bytes):,} bytes）")
            return
        except Exception as e:
            print(f"  ✗ PDF 下載失敗：{e}")

    # ── 都找不到 → fallback ──
    print("  未找到目標 Excel / PDF 連結。")
    fallback_data_gov()
    sys.exit(1)


if __name__ == "__main__":
    main()
