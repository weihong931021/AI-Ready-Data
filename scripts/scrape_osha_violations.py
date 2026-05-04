"""
從 announcement.mol.gov.tw 抓職安法/勞基法違規案例。

方法：純 Python subprocess + curl (session via cookie)

實證的 form↔table 對應（透過實測 hash 變化發現）：
- form 欄位 Page1 → 控制 HTML 中第 2 張 table（idx=1）= 職安法主軸（92,101 頁）
- form 欄位 Page3 → 控制 HTML 中第 1 張 table（idx=0）= 勞基法/性平/最低工資綜合（16,012 頁）
- form 欄位 Page2 → 控制 HTML 中第 3 張 table（idx=2）= 勞退條例（15,230 頁，已從 BLI ODS 取得，不重抓）
"""
import csv
import html
import re
import subprocess
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "資料" / "CSV" / "裁罰"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://announcement.mol.gov.tw/"
NUM_PAGES_OSHA = 100   # table 1 (職安法為主)
NUM_PAGES_LBR = 30     # table 0 (勞基法等綜合)

COOKIE_FILE = "/tmp/announce_session.txt"


def init_session() -> str:
    """GET 首頁，存 cookie，回傳 _csrf_token。"""
    r = subprocess.run(
        ["curl", "-c", COOKIE_FILE, "-sL", "-A", "Mozilla/5.0", BASE_URL],
        capture_output=True, check=True, timeout=30
    )
    h = r.stdout.decode("utf-8", errors="ignore")
    m = re.search(r'name="_csrf_token" value="([^"]+)"', h)
    if not m:
        raise RuntimeError("找不到 _csrf_token")
    return m.group(1)


def fetch_page(token: str, page1: int, page2: int, page3: int) -> str:
    """POST 至首頁取得指定頁面組合的 HTML。"""
    args = [
        "curl", "-b", COOKIE_FILE, "-c", COOKIE_FILE,
        "-sL", "-A", "Mozilla/5.0", "-X", "POST",
        "--data-urlencode", f"_csrf_token={token}",
        "--data-urlencode", f"Page1={page1}",
        "--data-urlencode", f"Page2={page2}",
        "--data-urlencode", f"Page3={page3}",
        "--data-urlencode", "CITYNO=",
        "--data-urlencode", "UNITNAME=",
        "--data-urlencode", "DOCstartDate=",
        "--data-urlencode", "DOCEndDate=",
        "--data-urlencode", "REGNUMBER=",
        "--data-urlencode", "REGNO=",
        "--data-urlencode", "FINE=",
        "--data-urlencode", "sortName1=",
        "--data-urlencode", "sortName2=",
        "--data-urlencode", "sortName3=",
        BASE_URL,
    ]
    r = subprocess.run(args, capture_output=True, check=True, timeout=30)
    return r.stdout.decode("utf-8", errors="ignore")


def extract_rows_from_table(table_html: str) -> list[list[str]]:
    """從一段 <table>...</table> 抽出資料列。"""
    rows = re.findall(r'<tr[\s\S]*?</tr>', table_html)
    out = []
    for row in rows:
        cells = re.findall(r'<t[hd][^>]*>([\s\S]*?)</t[hd]>', row)
        if len(cells) < 5:
            continue
        clean = []
        for c in cells:
            c = re.sub(r'<[^>]+>', '', c)
            c = html.unescape(c)
            c = re.sub(r'\s+', ' ', c).strip()
            clean.append(c)
        # 跳過表頭（第一格不是數字編號）
        if not clean[0].isdigit():
            continue
        out.append(clean)
    return out


def get_tables(h: str) -> list[str]:
    return re.findall(r'<table[\s\S]*?</table>', h)


def parse_amount(s: str) -> int:
    if not s:
        return 0
    s = re.sub(r"[^0-9]", "", s)
    return int(s) if s else 0


def roc_to_iso(s: str) -> str:
    if not s:
        return ""
    m = re.match(r"(\d{2,3})[/.\-](\d{1,2})[/.\-](\d{1,2})", s.strip())
    if not m:
        return s
    return f"{int(m.group(1))+1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def normalize(row: list[str], idx: int, prefix: str) -> dict:
    while len(row) < 10:
        row.append("")
    return {
        "案例ID": f"{prefix}_{idx:05d}",
        "縣市": row[1],
        "處分日期": roc_to_iso(row[2]),
        "違規日期": roc_to_iso(row[3]),
        "處分字號": row[4],
        "違規企業": row[5],
        "違反法條": row[6],
        "違規態樣": row[7],
        "處分金額_元": parse_amount(row[8]),
        "備註": row[9],
    }


def write_csv(rows: list[dict], out: Path):
    headers = ["案例ID", "縣市", "處分日期", "違規日期", "違反法條", "違規態樣",
               "處分金額_元", "違規企業", "處分字號", "備註"]
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in headers})
    print(f"  ✓ {out}（{len(rows)} 筆）")


def main():
    print("初始化 session ...")
    token = init_session()
    print(f"  token: {token[:20]}...")

    osha_rows = []  # table 1 (idx 1)
    lbr_rows = []   # table 0 (idx 0)

    target = max(NUM_PAGES_OSHA, NUM_PAGES_LBR)
    osha_idx = 1
    lbr_idx = 1

    for p in range(1, target + 1):
        # Page1 → Table[1]（職安法），Page3 → Table[0]（勞基法綜合）
        page1 = p if p <= NUM_PAGES_OSHA else 1
        page2 = 1
        page3 = p if p <= NUM_PAGES_LBR else 1

        try:
            h = fetch_page(token, page1, page2, page3)
            # 每次 POST 後 token 都會 rotate，從回應中讀新的
            new_tok = re.search(r'name="_csrf_token" value="([^"]+)"', h)
            if new_tok:
                token = new_tok.group(1)
        except Exception as e:
            print(f"  page {p} 失敗：{e}")
            time.sleep(1.5)
            try:
                token = init_session()
                h = fetch_page(token, page1, page2, page3)
            except Exception:
                continue

        tables = get_tables(h)
        if len(tables) < 3:
            print(f"  page {p} tables 不足（{len(tables)}），跳過")
            time.sleep(1)
            continue

        if p <= NUM_PAGES_OSHA:
            for r in extract_rows_from_table(tables[1]):
                osha_rows.append(normalize(r, osha_idx, "OSHA"))
                osha_idx += 1

        if p <= NUM_PAGES_LBR:
            for r in extract_rows_from_table(tables[0]):
                lbr_rows.append(normalize(r, lbr_idx, "LBR"))
                lbr_idx += 1

        if p % 10 == 0 or p == target:
            print(f"  page {p}/{target}：OSHA={len(osha_rows)}, LBR={len(lbr_rows)}")
        time.sleep(0.3)

    # 去重（依 處分字號）
    def dedup(rows: list[dict]) -> list[dict]:
        seen = set()
        out = []
        for r in rows:
            key = r["處分字號"] or (r["違規企業"] + r["處分日期"])
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        # 重新編號
        for i, r in enumerate(out, 1):
            prefix = r["案例ID"].split("_")[0]
            r["案例ID"] = f"{prefix}_{i:05d}"
        return out

    osha_rows = dedup(osha_rows)
    lbr_rows = dedup(lbr_rows)

    print("\n=== 輸出 ===")
    write_csv(osha_rows, OUTPUT_DIR / "D_職安違規案例.csv")
    write_csv(lbr_rows, OUTPUT_DIR / "D_勞基法違規案例.csv")


if __name__ == "__main__":
    main()
