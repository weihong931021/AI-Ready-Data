"""
從勞動部勞動法令查詢系統爬取職業災害相關函釋，
產生真實官方內容的函釋彙編 PDF。

搜尋策略：
- 用「職業災害」搜尋，掃前 10 頁（共約 200 筆原始）
- 篩選「號函」（解釋性函件）而非「號公告」（行政公告）
- 進一步依要旨內容過濾：補償、給付、認定、義務等
- 抓全文（主旨 + 說明 + 相關法條）
- 目標：15–25 筆有效函釋

輸出：
  資料/2_自製整理/函釋彙編_教學參考.pdf
  資料/3_EAP上傳/PDF/函釋彙編_教學參考.pdf
"""
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_PATH))

BASE    = "https://laws.mol.gov.tw"
KW_ENC  = "%e8%81%b7%e6%a5%ad%e7%81%bd%e5%ae%b3"  # 職業災害
KW_STR  = "職業災害"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

OUT_SELF = Path(__file__).parent.parent / "資料" / "2_自製整理"
OUT_EAP  = Path(__file__).parent.parent / "資料" / "3_EAP上傳" / "PDF"
OUT_NAME = "函釋彙編_教學參考.pdf"
MIN_VALID   = 8
MAX_PAGES   = 10   # 掃幾頁（每頁 20 筆）
MAX_RESULTS = 20   # 最多取幾筆有效函釋

# 要旨中必須含有任一詞才算相關
RELEVANCE_KW = [
    "補償", "給付", "通勤", "工資", "認定",
    "義務", "責任", "申請", "保險", "雇主",
    "勞工", "職業病", "失能", "傷病",
]

styles = getSampleStyleSheet()
title_style = ParagraphStyle("T", parent=styles["Heading1"], fontName="CJK", fontSize=20, leading=28)
h2_style    = ParagraphStyle("H2", parent=styles["Heading2"], fontName="CJK", fontSize=12, leading=20,
                              spaceBefore=10, textColor="#1a4480")
meta_style  = ParagraphStyle("M", parent=styles["BodyText"],  fontName="CJK", fontSize=8,  leading=12,
                              textColor="#777777")
body_style  = ParagraphStyle("B", parent=styles["BodyText"],  fontName="CJK", fontSize=10, leading=16)
label_style = ParagraphStyle("L", parent=styles["BodyText"],  fontName="CJK", fontSize=10, leading=16,
                              textColor="#1a4480")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def roc_to_ad(s: str) -> str:
    m = re.search(r"(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日", s)
    if m:
        y = int(m.group(1))
        return f"{y+1911 if y < 200 else y}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return s.strip()


def parse_list_page(html: str, page: int, total: int) -> list[dict]:
    """
    Parse a 函釋 search results HTML page.
    Returns list of {doc_no, date_roc, date, summary, recordno, cnt}.
    """
    raw = BeautifulSoup(html, "html.parser").get_text(separator="\n")
    # Normalize whitespace within lines, keep line breaks
    lines = [re.sub(r"[ \t\r　]+", " ", l).strip() for l in raw.split("\n")]
    lines = [l for l in lines if l]

    base_no = (page - 1) * 20 + 1
    items = []
    doc_no = date_roc = date = ""
    summary_parts: list[str] = []
    state = None
    item_idx = 0

    def flush():
        nonlocal doc_no, date_roc, date, summary_parts, item_idx
        if doc_no:
            summary = " ".join(summary_parts).strip()
            items.append({
                "doc_no":   doc_no,
                "date_roc": date_roc,
                "date":     date,
                "summary":  summary[:500],
                "recordno": base_no + item_idx - 1,
                "cnt":      total,
            })
        doc_no = date_roc = date = ""
        summary_parts = []
        item_idx += 1

    for line in lines:
        if re.match(r"^\d+\.$", line):
            flush()
            state = "start"
        elif re.match(r"^發文字號[：:]$", line) or line == "發文字號：":
            state = "doc_no"
        elif re.match(r"^發文日期[：:]$", line) or line == "發文日期：":
            state = "date"
        elif re.match(r"^要\s*旨[：:]", line):
            # 要旨 may have content on the same line after ：
            rest = re.sub(r"^要\s*旨[：:]\s*", "", line).strip()
            if rest:
                summary_parts.append(rest)
            state = "summary"
        elif state == "doc_no" and line and not doc_no:
            doc_no = line
            state = None
        elif state == "date" and line and not date_roc:
            date_roc = line
            date = roc_to_ad(line)
            state = None
        elif state == "summary":
            # Stop collecting summary when hitting pagination or footer
            if re.match(r"共\s*\d+\s*筆", line) or "隱私權" in line:
                state = None
            else:
                summary_parts.append(line)

    flush()  # Last item
    return items


def get_list_page(page: int) -> tuple[list[dict], int]:
    """Return (items, total) for a results page."""
    url = (f"{BASE}/FINT/results.aspx"
           f"?etype=%2a%2c%20002%2c%20007&now=1&lnabndn=1"
           f"&keyword={KW_ENC}&title=out&type=etype%2c&page={page}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ✗ 清單 p{page}: {e}")
        return [], 0

    raw = resp.text
    cnt_m = re.search(r"共\s*(\d+)\s*筆", BeautifulSoup(raw, "html.parser").get_text())
    total = int(cnt_m.group(1)) if cnt_m else 0
    items = parse_list_page(raw, page, total)
    return items, total


def get_detail(item: dict) -> dict:
    """Fetch full text: 主旨 + 說明 + 相關法條."""
    url = (f"{BASE}/FLAW/FLAWDOC03.aspx"
           f"?datatype=etype&keyword={KW_ENC}&cnt={item['cnt']}"
           f"&now=1&lnabndn=1&recordno={item['recordno']}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        resp.raise_for_status()
        raw = BeautifulSoup(resp.text, "html.parser").get_text(separator="\n")
        lines = [re.sub(r"[ \t\r　]+", " ", l).strip() for l in raw.split("\n")]
        lines = [l for l in lines if l]
        text = "\n".join(lines)
    except Exception as e:
        print(f"  ✗ 全文 {item['doc_no']}: {e}")
        return item

    law_m  = re.search(r"相關法條[：:]\s*([\s\S]+?)(?=要\s*旨|主\s*旨|$)", text)
    subj_m = re.search(r"主\s*旨[：:]\s*([\s\S]+?)(?=說\s*明|正\s*本|副\s*本|共\s*\d|$)", text)
    expl_m = re.search(r"說\s*明[：:]\s*([\s\S]+?)(?=正\s*本|副\s*本|共\s*\d|$)", text)

    def clean(s: str, limit: int) -> str:
        return re.sub(r"\s+", " ", s).strip()[:limit]

    item["law_ref"]     = clean(law_m.group(1),  300) if law_m  else ""
    item["subject"]     = clean(subj_m.group(1), 600) if subj_m else ""
    item["explanation"] = clean(expl_m.group(1), 1200) if expl_m else ""
    item["detail_url"]  = url
    return item


def build_pdf(items: list[dict], out_path: Path):
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = [
        Paragraph("職災法規常見函釋摘要彙編", title_style),
        Spacer(1, 0.3*cm),
        Paragraph(esc("資料來源：勞動部勞動法令查詢系統 laws.mol.gov.tw（解釋令函公告）"), meta_style),
        Paragraph(esc(f"收錄函釋：{len(items)} 筆｜關鍵字：職業災害｜篩選：補償、給付、認定等"), meta_style),
        Paragraph(esc("資料截止：民國 115 年 03 月 31 日"), meta_style),
    ]
    for idx, item in enumerate(items, 1):
        story.append(PageBreak() if idx > 1 else Spacer(1, 0.5*cm))
        title_txt = item["summary"][:70] if item["summary"] else item["doc_no"]
        story.append(Paragraph(esc(f"{idx}. {title_txt}"), h2_style))
        story.append(Paragraph(esc(f"發文字號：{item['doc_no']}　日期：{item['date']}"), meta_style))
        if item.get("law_ref"):
            story.append(Paragraph(esc(f"相關法條：{item['law_ref']}"), meta_style))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(esc("【要旨】"), label_style))
        story.append(Paragraph(esc(item["summary"]), body_style))
        if item.get("subject"):
            story.append(Paragraph(esc("【主旨】"), label_style))
            story.append(Paragraph(esc(item["subject"]), body_style))
        if item.get("explanation"):
            story.append(Paragraph(esc("【說明】"), label_style))
            story.append(Paragraph(esc(item["explanation"]), body_style))
        if item.get("detail_url"):
            story.append(Paragraph(esc(f"來源：{item['detail_url']}"), meta_style))
    doc.build(story)


def main():
    print(f"=== 爬取勞動部函釋（關鍵字：{KW_STR}）===")
    all_items: list[dict] = []
    seen: set[str] = set()

    for page in range(1, MAX_PAGES + 1):
        if len(all_items) >= MAX_RESULTS:
            break
        rows, total = get_list_page(page)
        if not rows:
            break

        kept = 0
        for row in rows:
            if len(all_items) >= MAX_RESULTS:
                break
            if row["doc_no"] in seen:
                continue
            # 僅保留解釋性函件（號函），排除行政公告（號公告）
            if "號公告" in row["doc_no"]:
                continue
            # 要旨相關性過濾
            if not any(kw in row["summary"] for kw in RELEVANCE_KW):
                continue
            print(f"  ○ p{page} #{row['recordno']}: {row['doc_no']}")
            row = get_detail(row)
            time.sleep(0.4)
            seen.add(row["doc_no"])
            all_items.append(row)
            kept += 1

        print(f"  → p{page}：掃 {len(rows)} 筆，保留 {kept} 筆 | 累計：{len(all_items)}/{MAX_RESULTS}")
        time.sleep(0.5)

    print(f"\n共收集有效函釋：{len(all_items)} 筆")
    if len(all_items) < MIN_VALID:
        print(f"  ✗ 不足 {MIN_VALID} 筆，中止輸出。", file=sys.stderr)
        sys.exit(1)

    all_items.sort(key=lambda x: x.get("date", ""), reverse=True)

    for out_dir in (OUT_SELF, OUT_EAP):
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / OUT_NAME
        with tempfile.NamedTemporaryFile(dir=out_dir, suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            build_pdf(all_items, tmp_path)
            tmp_path.replace(out_path)
            print(f"  ✓ {out_path}（{len(all_items)} 筆）")
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise


if __name__ == "__main__":
    main()
