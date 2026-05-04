"""
從勞保局網站抓出職災給付每個子頁面的實際內容，組合成完整 PDF。

策略：
1. 對每個主頁面（如 0106056），解析 #rptPageMenu 區塊下的所有子 URL
2. 逐一以 curl 抓取每個子頁面
3. 抽出 <div class="title"> 之後到 <div class="lastupdated"> 之間的純文字
4. 用 reportlab 產生分類好的 PDF
"""
import html as html_lib
import re
import subprocess
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_PATH))

OUTPUT_DIR = Path(__file__).parent.parent / "資料" / "PDF原始" / "給付指南"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAIN_PAGES = [
    ("0106055", "災保醫療給付"),
    ("0106056", "災保傷病給付及照護補助"),
    ("0106057", "災保失能給付及照護補助"),
    ("0106058", "災保死亡給付"),
    ("0106113", "未加保勞工職災死亡補助"),
    ("0106099", "退保後經診斷罹患職業病醫療補助"),
    ("0106100", "退保後經診斷罹患職業病失能津貼"),
    ("0106101", "退保後經診斷罹患職業病死亡津貼"),
]

CACHE: dict[str, str] = {}


def fetch(url: str) -> str:
    if url in CACHE:
        return CACHE[url]
    result = subprocess.run(
        ["curl", "-sL", "-A", "Mozilla/5.0", url],
        capture_output=True, timeout=30, check=True
    )
    CACHE[url] = result.stdout.decode("utf-8", errors="ignore")
    return CACHE[url]


def get_sub_urls(html: str) -> list[str]:
    """抽出 rptPageMenu 區塊下所有子頁面 URL。"""
    pattern = r'href="(/0[0-9]+\.html)"[^>]*id="ContentPlaceHolder1_ContentPlaceHolder1_ctl00_rptPageMenu'
    urls = re.findall(pattern, html)
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(f"https://www.bli.gov.tw{u}")
    return out


def get_sub_title(html: str) -> str:
    m = re.search(r'<div[^>]+class="title"[^>]*>(.+?)</div>', html, re.DOTALL)
    if not m:
        return "(無標題)"
    title = re.sub(r'<[^>]+>', '', m.group(1))
    title = html_lib.unescape(title).strip()
    return title


def get_sub_content(html: str) -> str:
    """抽出 div.text-area 範圍純文字（不含 lastupdated）。"""
    # 找 text-area 開始位置
    m = re.search(r'<div[^>]+class="text-area"[^>]*>', html)
    if not m:
        return ""
    start = m.end()
    # 找 text-area 結束位置（<div class="lastupdated"> 之前）
    end_m = re.search(r'<div[^>]+class="lastupdated"', html[start:])
    end = start + end_m.start() if end_m else start + 8000
    body = html[start:end]
    # 移除 JavaScript / CSS
    body = re.sub(r'<script[\s\S]*?</script>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'<style[\s\S]*?</style>', '', body, flags=re.IGNORECASE)
    # 段落標記
    body = re.sub(r'<(p|div|li|tr|br|h[1-6])[^>]*>', '\n', body, flags=re.IGNORECASE)
    body = re.sub(r'</(p|div|li|tr|h[1-6])>', '\n', body, flags=re.IGNORECASE)
    # 移除剩餘 tag
    body = re.sub(r'<[^>]+>', '', body)
    body = html_lib.unescape(body)
    # 清理空白
    body = re.sub(r'[ \t]+', ' ', body)
    body = re.sub(r'\n[ \t]+', '\n', body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body.strip()


def main():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CJKTitle", parent=styles["Heading1"], fontName="CJK", fontSize=20, leading=26)
    h2_style = ParagraphStyle("CJKH2", parent=styles["Heading2"], fontName="CJK", fontSize=15, leading=22, spaceBefore=14)
    h3_style = ParagraphStyle("CJKH3", parent=styles["Heading3"], fontName="CJK", fontSize=12, leading=18, spaceBefore=10, leftIndent=10)
    body_style = ParagraphStyle("CJKBody", parent=styles["BodyText"], fontName="CJK", fontSize=10, leading=16, leftIndent=15)
    meta_style = ParagraphStyle("CJKMeta", parent=styles["BodyText"], fontName="CJK", fontSize=8, leading=12, textColor="#777777")

    output_path = OUTPUT_DIR / "G_勞保局_職災給付指南合輯.pdf"
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    story.append(Paragraph("勞保局職災給付指南合輯", title_style))
    story.append(Paragraph("資料來源：勞動部勞工保險局 www.bli.gov.tw（職災保險專區）", body_style))

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for code, main_name in MAIN_PAGES:
        main_url = f"https://www.bli.gov.tw/{code}.html"
        print(f"\n=== {main_name} ({main_url}) ===")
        try:
            main_html = fetch(main_url)
        except Exception as e:
            print(f"  主頁面失敗：{e}")
            continue

        sub_urls = get_sub_urls(main_html)
        if not sub_urls:
            sub_urls = [main_url]
        print(f"  子頁面 {len(sub_urls)} 個")

        story.append(PageBreak())
        story.append(Paragraph(esc(main_name), h2_style))
        story.append(Paragraph(esc(f"主頁：{main_url}"), meta_style))
        story.append(Spacer(1, 0.3 * cm))

        for sub_url in sub_urls:
            try:
                sub_html = fetch(sub_url)
            except Exception as e:
                print(f"    {sub_url} 失敗：{e}")
                continue
            sub_title = get_sub_title(sub_html)
            sub_content = get_sub_content(sub_html)
            if not sub_content or len(sub_content) < 10:
                continue
            print(f"    ✓ {sub_title} ({len(sub_content)} 字)")
            story.append(Paragraph(esc(sub_title), h3_style))
            story.append(Paragraph(esc(sub_url), meta_style))
            for para in sub_content.split("\n\n"):
                para = para.strip()
                if not para:
                    continue
                # 段內換行轉空格
                para = re.sub(r"\s*\n\s*", " ", para)
                story.append(Paragraph(esc(para), body_style))
            story.append(Spacer(1, 0.2 * cm))

    doc.build(story)
    print(f"\n完成：{output_path}")


if __name__ == "__main__":
    main()
