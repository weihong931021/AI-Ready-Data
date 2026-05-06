"""
從 announcement.mol.gov.tw 批量下載勞基法/性平法歷史裁罰 CSV。

策略：
- 使用 /Download/ endpoint，一次按年份 + 法規類別下載整年資料
- 目標：民國 111-114 年（2022-2025），REGNUMBER=1（勞基）+ 2（性平）
- 合併現有 128 筆 2026 資料，統一欄位格式，輸出到兩個位置

下載欄位：編號,縣市/單位別,公告日期,事業單位名稱(負責人)/自然人姓名,
          處分日期,處分字號,違反法規條款,法條敘述,罰鍰金額,備註
現有欄位：案例ID,縣市,處分日期,違規日期,違反法條,違規態樣,處分金額_元,
          違規企業,處分字號,備註

輸出：
  資料/1_原始下載/裁罰_原始/D_勞基法違規案例.csv
  資料/3_EAP上傳/CSV/裁罰原始_給EAP/D_勞基法違規案例.csv
"""
import csv
import io
import re
import subprocess
import time
from pathlib import Path

RAW_CSV = Path(__file__).parent.parent / "資料" / "1_原始下載" / "裁罰_原始" / "D_勞基法違規案例.csv"
EAP_CSV = Path(__file__).parent.parent / "資料" / "3_EAP上傳" / "CSV" / "裁罰原始_給EAP" / "D_勞基法違規案例.csv"

BASE_URL    = "https://announcement.mol.gov.tw/"
COOKIE_FILE = "/tmp/mol_dl_session.txt"

# REGNUMBER: 1=勞動基準法, 2=性別平等工作法, 4=就業服務法, 6=中高齡
# 以下下載 1+2（與現有 CSV 一致，現有 CSV 已含性平違規）
REG_NUMBERS = ["1", "2"]

# 民國年份範圍（ROC format YYYMMDD）
YEAR_RANGES = [
    ("1110101", "1111231"),  # 2022
    ("1120101", "1121231"),  # 2023
    ("1130101", "1131231"),  # 2024
    ("1140101", "1141231"),  # 2025
]

HEADERS = ["案例ID", "縣市", "處分日期", "違規日期", "違反法條",
           "違規態樣", "處分金額_元", "違規企業", "處分字號", "備註"]


def roc_to_iso(s: str) -> str:
    if not s:
        return ""
    s = s.strip().strip('"')
    m = re.match(r"(\d{2,3})[/.\-](\d{1,2})[/.\-](\d{1,2})", s)
    if m:
        return f"{int(m.group(1))+1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return s


def parse_amount(s: str) -> int:
    s = re.sub(r"[^0-9]", "", s)
    return int(s) if s else 0


def get_token() -> str:
    r = subprocess.run(
        ["curl", "-sc", COOKIE_FILE, "-sL", "-A", "Mozilla/5.0", BASE_URL],
        capture_output=True, check=True, timeout=30
    )
    h = r.stdout.decode("utf-8", errors="ignore")
    m = re.search(r'name="_csrf_token" value="([^"]+)"', h)
    if not m:
        raise RuntimeError("找不到 _csrf_token")
    return m.group(1)


def download_year_reg(token: str, start: str, end: str, regnumber: str) -> tuple[list[dict], str]:
    """Download one year+regulation CSV. Returns (rows, new_token)."""
    args = [
        "curl", "-sb", COOKIE_FILE, "-sc", COOKIE_FILE,
        "-L", "-A", "Mozilla/5.0", "-X", "POST",
        "-F", f"_csrf_token={token}",
        "-F", "Page1=1", "-F", "Page2=1", "-F", "Page3=1",
        "-F", "CITYNO=", "-F", "UNITNAME=",
        "-F", f"DOCstartDate={start}",
        "-F", f"DOCEndDate={end}",
        "-F", f"REGNUMBER={regnumber}",
        "-F", "REGNO=", "-F", "FINE=",
        "-F", "sortName1=", "-F", "sortName2=", "-F", "sortName3=",
        "-F", "downloadType=3",
        f"{BASE_URL}Download/",
    ]
    r = subprocess.run(args, capture_output=True, check=True, timeout=120)
    content = r.stdout.decode("utf-8-sig", errors="replace")

    # Extract new token if redirected through HTML
    new_tok = re.search(r'name="_csrf_token" value="([^"]+)"', content)
    new_token = new_tok.group(1) if new_tok else token

    # Check if response is CSV (starts with "違反雇主清冊" or has numeric first column)
    if "違反雇主清冊" not in content and "縣市" not in content:
        print(f"    ⚠ 非 CSV 回應（前50字）: {content[:50]!r}")
        return [], new_token

    rows = parse_download_csv(content)
    return rows, new_token


def parse_download_csv(content: str) -> list[dict]:
    """Parse the downloaded CSV into normalized dicts."""
    lines = content.splitlines()

    # Skip first line if it's the title "違反雇主清冊"
    start = 0
    if lines and "違反雇主清冊" in lines[0]:
        start = 1

    # Parse with csv reader
    reader = csv.reader(io.StringIO("\n".join(lines[start:])))
    headers = None
    rows = []

    for row in reader:
        if not row:
            continue
        # Strip quotes that csv reader might not handle
        row = [c.strip().strip('"') for c in row]
        if headers is None:
            # Check if this is the header row
            if any(k in row for k in ["縣市", "編號", "處分日期"]):
                headers = row
            continue
        if not row[0].isdigit():
            continue
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))

        # Map columns to our schema
        # Expected: 編號,縣市/單位別,公告日期,事業單位名稱...,處分日期,處分字號,違反法規條款,法條敘述,罰鍰金額,備註
        col = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}

        city_key    = next((k for k in col if "縣市" in k or "單位" in k), "")
        company_key = next((k for k in col if "名稱" in k or "姓名" in k or "事業" in k), "")
        law_key     = next((k for k in col if "法規條款" in k or "法條" in k and "敘述" not in k), "")
        desc_key    = next((k for k in col if "敘述" in k or "法條敘述" in k), "")
        amount_key  = next((k for k in col if "金額" in k or "罰鍰" in k), "")

        rows.append({
            "縣市":      col.get(city_key, ""),
            "處分日期":  roc_to_iso(col.get("處分日期", "")),
            "違規日期":  roc_to_iso(col.get("處分日期", "")),  # 無獨立違規日期欄，暫同處分日期
            "違反法條":  col.get(law_key, ""),
            "違規態樣":  col.get(desc_key, ""),
            "處分金額_元": parse_amount(col.get(amount_key, "")),
            "違規企業":  col.get(company_key, ""),
            "處分字號":  col.get("處分字號", ""),
            "備註":      col.get("備註", ""),
        })
    return rows


def load_existing(path: Path) -> tuple[list[dict], set[str]]:
    if not path.exists():
        return [], set()
    rows, seen = [], set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            key = r.get("處分字號") or (r.get("違規企業", "") + r.get("處分日期", ""))
            if key and key not in seen:
                seen.add(key)
                rows.append(dict(r))
    return rows, seen


def write_csv(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEADERS})
    print(f"  ✓ {path.name}（{len(rows):,} 筆）")


def main():
    print("=== 批量下載勞基法/性平法歷史裁罰資料 ===\n")

    existing, seen = load_existing(RAW_CSV)
    print(f"現有資料：{len(existing):,} 筆")

    new_rows: list[dict] = []

    token = get_token()
    print(f"Session 初始化完成\n")

    for start_d, end_d in YEAR_RANGES:
        roc_year = int(start_d[:3])
        ad_year  = roc_year + 1911
        print(f"--- 民國 {roc_year} 年（{ad_year}）---")

        for regnumber in REG_NUMBERS:
            reg_name = {"1": "勞動基準法", "2": "性別平等工作法"}.get(regnumber, regnumber)
            try:
                rows, token = download_year_reg(token, start_d, end_d, regnumber)
                added = 0
                for r in rows:
                    key = r["處分字號"] or (r["違規企業"] + r["處分日期"])
                    if key and key not in seen:
                        seen.add(key)
                        new_rows.append(r)
                        added += 1
                print(f"  {reg_name}：下載 {len(rows):,} 筆，新增 {added:,} 筆")
            except Exception as e:
                print(f"  {reg_name}：✗ 下載失敗 {e}")
                # Re-init session and retry
                try:
                    time.sleep(2)
                    token = get_token()
                    rows, token = download_year_reg(token, start_d, end_d, regnumber)
                    added = sum(1 for r in rows
                                if (r["處分字號"] or r["違規企業"]+r["處分日期"]) not in seen
                                and seen.add(r["處分字號"] or r["違規企業"]+r["處分日期"]) is None)
                    new_rows.extend(rows[:added])
                    print(f"    重試成功：新增 {added:,} 筆")
                except Exception as e2:
                    print(f"    重試也失敗：{e2}")
            time.sleep(1)

    print(f"\n合計新增：{len(new_rows):,} 筆")

    if not new_rows:
        print("⚠ 未下載到新資料，保留現有 CSV 不變。")
        return

    # Merge, sort newest first, renumber
    all_rows = existing + new_rows
    all_rows.sort(key=lambda x: x.get("處分日期", ""), reverse=True)
    for i, r in enumerate(all_rows, 1):
        r["案例ID"] = f"LBR_{i:05d}"

    print(f"合計（含現有）：{len(all_rows):,} 筆")
    write_csv(all_rows, RAW_CSV)
    write_csv(all_rows, EAP_CSV)
    print("\n完成！")


if __name__ == "__main__":
    main()
