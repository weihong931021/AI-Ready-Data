"""
Playwright 抓司法院判決書系統的職災勞訴判決摘要。

策略：
1. 開啟 simple query
2. 搜尋「職業災害損害賠償」+ 民事案件
3. 篩選：案由包含「職業災害」或「勞工補償」才保留
4. 抓前 20 個有效（篩選後）判決的標題、案由、字號、要旨
5. 組成 PDF（VectorRAG 用）+ CSV（GraphRAG 用）
"""
import asyncio
import csv
import re
import sys
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_PATH))

# 輸出路徑（已對齊 EAP 上傳目錄）
OUT_PDF_PATH = Path(__file__).parent.parent / "資料" / "3_EAP上傳" / "PDF" / "C_職災勞訴判決摘要集.pdf"
OUT_CSV_PATH = Path(__file__).parent.parent / "資料" / "1_原始下載" / "司法判決" / "D_職災判決案例.csv"
OUT_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

KEYWORD = "職業災害損害賠償"   # ← 改為更精確的關鍵字
NUM_VALID = 20                 # 篩選後有效筆數上限（非原始點擊數）

# 案由篩選條件：包含任一關鍵詞才保留
CASE_REASON_KEYWORDS = ["職業災害", "勞工補償"]


def is_valid_case(case_type_str: str) -> bool:
    """案由包含職業災害或勞工補償才算有效案件。"""
    return any(kw in case_type_str for kw in CASE_REASON_KEYWORDS)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh)")
        page = await ctx.new_page()

        print("開啟司法院判決書系統 ...")
        await page.goto("https://judgment.judicial.gov.tw/FJUD/default.aspx",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(1000)

        # 填關鍵字（職業災害損害賠償）
        await page.fill("input[name='txtKW']", KEYWORD)
        # 點送出查詢
        await page.click("input[name='ctl00$cp_content$btnSimpleQry']")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        print(f"  current url: {page.url}")
        frames = page.frames
        print(f"  frames: {len(frames)}")
        for f in frames:
            print(f"    name={f.name} url={f.url[:80]}")

        # 找結果清單 frame
        list_frame = None
        for f in frames:
            if "qryresult" in f.url.lower() or "list" in f.name.lower() or len(f.url) > len(page.url):
                list_frame = f
                break
        if not list_frame:
            list_frame = frames[-1] if len(frames) > 1 else page
        print(f"  使用 frame: {list_frame.url[:80]}")

        # 抓所有判決連結（最多抓 200 個原始結果，再由篩選決定）
        RAW_LIMIT = 200
        items = await list_frame.evaluate(f"""() => {{
            const links = Array.from(document.querySelectorAll('a[href*="data.aspx"]'));
            return links.slice(0, {RAW_LIMIT}).map(a => ({{
                text: a.innerText.trim(),
                href: a.href,
            }}));
        }}""")
        print(f"  原始結果：{len(items)} 個判決連結")
        for i, it in enumerate(items[:5]):
            print(f"    {i+1}. {it['text'][:60]}")

        # 進每個判決頁抓內容，篩選後收集有效案件
        judgments = []
        valid_count = 0
        raw_idx = 0

        for it in items:
            if valid_count >= NUM_VALID:
                break
            raw_idx += 1
            try:
                await page.goto(it["href"], wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(500)

                content = ""
                title = it["text"]
                for f in page.frames:
                    try:
                        text = await f.evaluate("() => document.body.innerText")
                        if text and len(text) > 200 and "理由" in text:
                            content = text
                            break
                    except Exception:
                        continue
                if not content:
                    content = await page.evaluate("() => document.body.innerText")

                # 取案號、案由、日期
                case_no = re.search(r"裁判字號[：:]\s*(\S+)", content)
                case_type = re.search(r"案由[：:]\s*(\S+?)\s*$", content, re.MULTILINE)
                date_m = re.search(r"裁判日期[：:]\s*(\S+)", content)
                case_type_str = case_type.group(1) if case_type else ""

                # ── 篩選：案由必須含職業災害或勞工補償 ──
                if not is_valid_case(case_type_str):
                    print(f"    ✗ 原始#{raw_idx} 跳過（案由：{case_type_str!r}）")
                    continue

                # 取理由段前 1500 字
                reason_m = re.search(r"理\s*由([\s\S]*)", content)
                reason = reason_m.group(1).strip()[:1500] if reason_m else content[:1500]

                valid_count += 1
                judgments.append({
                    "ID": f"JUD_{valid_count:03d}",
                    "標題": title[:80],
                    "字號": case_no.group(1) if case_no else "",
                    "案由": case_type_str,
                    "裁判日期": date_m.group(1) if date_m else "",
                    "url": it["href"],
                    "摘要": reason,
                })
                print(f"    ✓ 有效#{valid_count}/{NUM_VALID}（原始#{raw_idx}）: {title[:50]}")

            except Exception as e:
                print(f"    ✗ 原始#{raw_idx}: {e}")

        print(f"\n  共收集有效判決：{len(judgments)} 筆（掃描原始連結：{raw_idx} 個）")
        await browser.close()

    # ── 輸出 PDF / CSV ──
    MIN_VALID = 1
    if len(judgments) < MIN_VALID:
        print(f"  ✗ 有效判決不足：{len(judgments)} 筆，至少需要 {MIN_VALID} 筆；保留既有輸出檔不變", file=sys.stderr)
        sys.exit(1)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CJKTitle", parent=styles["Heading1"], fontName="CJK", fontSize=20, leading=26)
    h2_style = ParagraphStyle("CJKH2", parent=styles["Heading2"], fontName="CJK", fontSize=14, leading=22, spaceBefore=14)
    body_style = ParagraphStyle("CJKBody", parent=styles["BodyText"], fontName="CJK", fontSize=10, leading=16)
    meta_style = ParagraphStyle("CJKMeta", parent=styles["BodyText"], fontName="CJK", fontSize=8, leading=12, textColor="#777")

    tmp_pdf_path = None
    tmp_csv_path = None
    with tempfile.NamedTemporaryFile(dir=OUT_PDF_PATH.parent, suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf_path = Path(tmp_pdf.name)
    with tempfile.NamedTemporaryFile(dir=OUT_CSV_PATH.parent, suffix=".csv", delete=False) as tmp_csv:
        tmp_csv_path = Path(tmp_csv.name)

    doc = SimpleDocTemplate(str(tmp_pdf_path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph("職災勞訴判決摘要集", title_style),
        Paragraph(
            f"資料來源：司法院判決書系統 judgment.judicial.gov.tw"
            f"（關鍵字：{KEYWORD}；篩選條件：案由含「職業災害」或「勞工補償」）",
            body_style,
        ),
    ]

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for j in judgments:
        story.append(PageBreak())
        story.append(Paragraph(esc(j["標題"]), h2_style))
        story.append(Paragraph(esc(f"字號：{j['字號']} | 案由：{j['案由']} | 日期：{j['裁判日期']}"), meta_style))
        story.append(Paragraph(esc(f"來源：{j['url']}"), meta_style))
        story.append(Spacer(1, 0.3 * cm))
        for para in j["摘要"].split("\n"):
            para = para.strip()
            if not para:
                continue
            story.append(Paragraph(esc(para), body_style))

    try:
        doc.build(story)
        with tmp_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["案例ID", "字號", "案由", "裁判日期", "標題", "url"])
            w.writeheader()
            for j in judgments:
                w.writerow({
                    "案例ID": j["ID"],
                    "字號": j["字號"],
                    "案由": j["案由"],
                    "裁判日期": j["裁判日期"],
                    "標題": j["標題"],
                    "url": j["url"],
                })

        tmp_pdf_path.replace(OUT_PDF_PATH)
        tmp_csv_path.replace(OUT_CSV_PATH)
    except Exception:
        if tmp_pdf_path and tmp_pdf_path.exists():
            tmp_pdf_path.unlink()
        if tmp_csv_path and tmp_csv_path.exists():
            tmp_csv_path.unlink()
        raise

    print(f"  ✓ PDF：{OUT_PDF_PATH}（{len(judgments)} 筆）")
    print(f"  ✓ CSV：{OUT_CSV_PATH}（{len(judgments)} 筆）")


if __name__ == "__main__":
    asyncio.run(main())
