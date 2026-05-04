"""
Playwright 抓司法院判決書系統的職災勞訴判決摘要。

策略：
1. 開啟 simple query
2. 搜尋「職業災害」+ 民事 案由
3. 抓前 N 個判決的標題、案由、字號、要旨
4. 組成 PDF（VectorRAG 用）+ CSV（GraphRAG 用）
"""
import asyncio
import csv
import re
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

OUT_PDF_DIR = Path(__file__).parent.parent / "資料" / "PDF原始" / "案例"
OUT_CSV_DIR = Path(__file__).parent.parent / "資料" / "CSV" / "裁罰"
OUT_PDF_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)

KEYWORD = "職業災害"
NUM_JUDGMENTS = 30  # 抓前 30 個


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh)")
        page = await ctx.new_page()

        print("開啟司法院判決書系統 ...")
        await page.goto("https://judgment.judicial.gov.tw/FJUD/default.aspx",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(1000)

        # 填關鍵字
        await page.fill("input[name='txtKW']", KEYWORD)
        # 點送出查詢
        await page.click("input[name='ctl00$cp_content$btnSimpleQry']")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # 看當前頁面 frame 結構
        print(f"  current url: {page.url}")
        # 通常結果頁是 frameset → 切到 right frame
        frames = page.frames
        print(f"  frames: {len(frames)}")
        for f in frames:
            print(f"    name={f.name} url={f.url[:80]}")

        # 找到 list frame
        list_frame = None
        for f in frames:
            if "qryresult" in f.url.lower() or "list" in f.name.lower() or len(f.url) > len(page.url):
                list_frame = f
                break
        if not list_frame:
            list_frame = frames[-1] if len(frames) > 1 else page
        print(f"  使用 frame: {list_frame.url[:80]}")

        # 抓所有判決連結
        items = await list_frame.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href*="data.aspx"]'));
            return links.slice(0, 30).map(a => ({
                text: a.innerText.trim(),
                href: a.href,
            }));
        }""")
        print(f"  抓到 {len(items)} 個判決")
        for i, it in enumerate(items[:5]):
            print(f"    {i+1}. {it['text'][:60]}")

        # 進每個判決頁抓內容
        judgments = []
        for i, it in enumerate(items[:NUM_JUDGMENTS]):
            try:
                await page.goto(it["href"], wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(500)
                # 找 frame 含 內容
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

                # 取案號 + 案由 + 摘要
                case_no = re.search(r"裁判字號[：:]\s*(\S+)", content)
                case_type = re.search(r"案由[：:]\s*(\S+?)\s*$", content, re.MULTILINE)
                date_m = re.search(r"裁判日期[：:]\s*(\S+)", content)
                # 取理由前 800 字
                reason_m = re.search(r"理\s*由([\s\S]*)", content)
                reason = reason_m.group(1).strip()[:1500] if reason_m else content[:1500]

                judgments.append({
                    "ID": f"JUD_{i+1:03d}",
                    "標題": title[:80],
                    "字號": case_no.group(1) if case_no else "",
                    "案由": case_type.group(1) if case_type else "",
                    "裁判日期": date_m.group(1) if date_m else "",
                    "url": it["href"],
                    "摘要": reason,
                })
                print(f"    ✓ {i+1}/{NUM_JUDGMENTS}: {title[:50]}")
            except Exception as e:
                print(f"    ✗ {i+1}: {e}")

        await browser.close()

    # 輸出 PDF
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CJKTitle", parent=styles["Heading1"], fontName="CJK", fontSize=20, leading=26)
    h2_style = ParagraphStyle("CJKH2", parent=styles["Heading2"], fontName="CJK", fontSize=14, leading=22, spaceBefore=14)
    body_style = ParagraphStyle("CJKBody", parent=styles["BodyText"], fontName="CJK", fontSize=10, leading=16)
    meta_style = ParagraphStyle("CJKMeta", parent=styles["BodyText"], fontName="CJK", fontSize=8, leading=12, textColor="#777")

    pdf_path = OUT_PDF_DIR / "C_職災勞訴判決摘要集.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph("職災勞訴判決摘要集", title_style),
        Paragraph(f"資料來源：司法院判決書系統 judgment.judicial.gov.tw（關鍵字：{KEYWORD}）", body_style),
    ]
    def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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
    if judgments:
        doc.build(story)
        print(f"\n  ✓ PDF：{pdf_path}（{len(judgments)} 筆）")

    # 輸出 CSV
    csv_path = OUT_CSV_DIR / "D_職災判決案例.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
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
    print(f"  ✓ CSV：{csv_path}（{len(judgments)} 筆）")


if __name__ == "__main__":
    asyncio.run(main())
