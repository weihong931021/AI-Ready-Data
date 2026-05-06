"""
build_eap_package.py
產生 EAP_上傳包/ — 精選內容，直接上傳到 EAP 平台用。

結構：
  EAP_上傳包/
    PDF/           15 份核心 PDF（三情境對應）
    CSV/
      01_節點/     17 個節點 CSV（全保留）
      02_關係/     24 個關係 CSV（全保留）
      03_裁罰參考/ 2,000 筆精選裁罰 + 4 份統計 CSV
"""

import csv
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_CSV_NODE = ROOT / "資料/3_EAP上傳/CSV/節點"
SRC_CSV_REL  = ROOT / "資料/3_EAP上傳/CSV/關係"
SRC_CSV_PNL  = ROOT / "資料/3_EAP上傳/CSV/裁罰原始_給EAP"
SRC_PDF      = ROOT / "資料/3_EAP上傳/PDF"

OUT = ROOT / "EAP_上傳包"

# ── 1. 15 份核心 PDF ──────────────────────────────────────────
CORE_PDFS = [
    # 情境A 應急導航：職災處置
    "L_勞動基準法.pdf",
    "L_勞工職業災害保險及保護法.pdf",
    "L_勞工職業災害保險職業傷病審查準則.pdf",
    "L_職業安全衛生法.pdf",
    "L_性別平等工作法.pdf",
    "G_勞保局_職災給付指南合輯.pdf",
    "C_職安署_執行職務遭受不法侵害預防指引_第四版.pdf",
    "C_職安署_異常工作負荷促發疾病預防指引.pdf",
    # 情境B 精準止損：資遣爭議
    "L_大量解僱勞工保護法.pdf",
    "L_勞動事件法.pdf",
    "L_勞資爭議處理法.pdf",
    "案例彙編_教學參考.pdf",
    # 情境C 法規風險雷達
    "C_職安署_114年重大職災死亡統計報告.pdf",
    "C_職災勞訴判決摘要集.pdf",
    # 刑責補強（三情境共用）
    "L_刑法.pdf",
]

# ── 2. 統計 CSV（直接整份帶走）────────────────────────────────
STAT_CSVS = [
    "D_全部裁罰_按法條統計.csv",
    "D_全部裁罰_按產業統計.csv",
    "D_職安勞基_按法條統計.csv",
    "D_職安勞基_按產業統計.csv",
]

# ── 3. 裁罰案例抽樣：IT 1500 + 其他 500 ─────────────────────
SAMPLE_IT    = 1500
SAMPLE_OTHER = 500
RAW_CSV = SRC_CSV_PNL / "D_全部裁罰案例_清理版.csv"


def sample_penalty(src: Path, it_n: int, other_n: int) -> list[dict]:
    it_rows, other_rows = [], []
    with open(src, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("推測產業", "") == "資訊服務":
                it_rows.append(row)
            else:
                other_rows.append(row)

    random.seed(42)
    it_sample    = random.sample(it_rows, min(it_n, len(it_rows)))
    other_sample = random.sample(other_rows, min(other_n, len(other_rows)))
    result = it_sample + other_sample
    random.shuffle(result)
    return result


def copy_files(srcs: list[Path], dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    ok, miss = 0, []
    for src in srcs:
        if src.exists():
            shutil.copy2(src, dest_dir / src.name)
            ok += 1
        else:
            miss.append(src.name)
    return ok, miss


def main():
    print("── 建立 EAP_上傳包/ ─────────────────────────────")
    OUT.mkdir(exist_ok=True)

    # PDF
    pdf_srcs = [SRC_PDF / f for f in CORE_PDFS]
    ok, miss = copy_files(pdf_srcs, OUT / "PDF")
    print(f"PDF：{ok} 份已複製" + (f"，找不到：{miss}" if miss else ""))

    # 節點 CSV
    node_srcs = [p for p in sorted(SRC_CSV_NODE.glob("*.csv"))
                 if "精簡版" not in p.name]
    ok, _ = copy_files(node_srcs, OUT / "CSV/01_節點")
    print(f"節點 CSV：{ok} 個")

    # 關係 CSV
    rel_srcs = sorted(SRC_CSV_REL.glob("*.csv"))
    ok, _ = copy_files(rel_srcs, OUT / "CSV/02_關係")
    print(f"關係 CSV：{ok} 個")

    # 統計 CSV
    stat_srcs = [SRC_CSV_PNL / f for f in STAT_CSVS]
    ok, miss = copy_files(stat_srcs, OUT / "CSV/03_裁罰參考")
    print(f"統計 CSV：{ok} 份" + (f"，找不到：{miss}" if miss else ""))

    # 裁罰抽樣
    pnl_out = OUT / "CSV/03_裁罰參考/D_裁罰樣本_IT優先_2000筆.csv"
    rows = sample_penalty(RAW_CSV, SAMPLE_IT, SAMPLE_OTHER)
    with open(pnl_out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"裁罰樣本：{len(rows)} 筆（IT {min(SAMPLE_IT, 3340)} + 其他 {SAMPLE_OTHER}）→ {pnl_out.name}")

    print("\n✓ 完成。EAP_上傳包/ 結構：")
    for p in sorted(OUT.rglob("*")):
        indent = "  " * (len(p.relative_to(OUT).parts) - 1)
        icon = "📁" if p.is_dir() else "  "
        print(f"  {indent}{icon} {p.name}")


if __name__ == "__main__":
    main()
