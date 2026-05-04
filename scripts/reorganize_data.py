"""
重整資料夾結構：明確區分「原始下載」「自製整理」「EAP 上傳」三類。

新結構：
資料/
├── 1_原始下載/        ← 從官方/爬蟲取得的未動過資料
│   ├── 法條_PDF/      ← law.moj.gov.tw 23 部
│   ├── 給付指南_PDF/  ← BLI 子頁組合 PDF（內容仍為 BLI 官方）
│   ├── 重大職災_PDF/  ← 職安署官方統計與列管
│   ├── 司法判決/       ← 司法院爬蟲輸出
│   └── 裁罰_原始/      ← BLI ODS/CSV + announcement.mol 爬蟲
├── 2_自製整理/        ← 我整理的（明確標示「教學參考」）
│   ├── 函釋彙編_教學參考.pdf
│   └── 案例彙編_教學參考.pdf
└── 3_EAP上傳/         ← 上傳到 EAP 的整合版（含節點/關係 CSV）
    ├── PDF/           ← 28 份（軟連結到 1+2）
    └── CSV/
        ├── 節點/     13 份
        └── 關係/     11 份
"""
import shutil
from pathlib import Path

ROOT = Path("/Users/weihong/Documents/精誠ai/資料")
NEW = ROOT.parent / "資料_新"

# 清掉舊新資料夾
if NEW.exists():
    shutil.rmtree(NEW)
NEW.mkdir()

# 1. 原始下載/
RAW = NEW / "1_原始下載"
(RAW / "法條_PDF").mkdir(parents=True)
(RAW / "給付指南_PDF").mkdir()
(RAW / "重大職災_PDF").mkdir()
(RAW / "司法判決").mkdir()
(RAW / "裁罰_原始").mkdir()

# 法條：搬全部 23 個 L_*.pdf（純官方）
for pdf in (ROOT / "PDF原始" / "法條").glob("L_*.pdf"):
    shutil.copy2(pdf, RAW / "法條_PDF" / pdf.name)

# 給付指南：BLI 真內容
gpath = ROOT / "PDF原始" / "給付指南" / "G_勞保局_職災給付指南合輯.pdf"
if gpath.exists():
    shutil.copy2(gpath, RAW / "給付指南_PDF" / gpath.name)

# 重大職災：職安署官方
for fn in ["C_職安署_114年重大職災死亡統計報告.pdf",
           "C_職安署_高職災與高違規廠場列管名冊.pdf"]:
    p = ROOT / "PDF原始" / "案例" / fn
    if p.exists():
        shutil.copy2(p, RAW / "重大職災_PDF" / fn)

# 司法判決
jpath = ROOT / "PDF原始" / "案例" / "C_職災勞訴判決摘要集.pdf"
if jpath.exists():
    shutil.copy2(jpath, RAW / "司法判決" / jpath.name)
jcsv = ROOT / "CSV" / "裁罰" / "D_職災判決案例.csv"
if jcsv.exists():
    shutil.copy2(jcsv, RAW / "司法判決" / jcsv.name)

# 裁罰原始：BLI ODS + 兩份 CSV + 兩份爬蟲 CSV
import urllib.request
penalty_files = [
    ROOT / "CSV" / "裁罰" / "D_災保法裁罰名單.csv",       # BLI ODS 轉的原始 CSV
    ROOT / "CSV" / "裁罰" / "D_勞退條例裁罰名單.csv",     # BLI 直接下載
    ROOT / "CSV" / "裁罰" / "D_職安違規案例.csv",          # 爬蟲
    ROOT / "CSV" / "裁罰" / "D_勞基法違規案例.csv",        # 爬蟲
]
for p in penalty_files:
    if p.exists():
        shutil.copy2(p, RAW / "裁罰_原始" / p.name)

# 2. 自製整理/
GEN = NEW / "2_自製整理"
GEN.mkdir()
gen_map = {
    ROOT / "PDF原始" / "函釋" / "I_職災法規常見函釋摘要彙編.pdf": "函釋彙編_教學參考.pdf",
    ROOT / "PDF原始" / "案例" / "C_職災典型案例摘要集.pdf": "案例彙編_教學參考.pdf",
}
for src, new_name in gen_map.items():
    if src.exists():
        shutil.copy2(src, GEN / new_name)

# 3. EAP 上傳/
EAP = NEW / "3_EAP上傳"
EAP.mkdir()
(EAP / "PDF").mkdir()
(EAP / "CSV" / "節點").mkdir(parents=True)
(EAP / "CSV" / "關係").mkdir()
(EAP / "CSV" / "裁罰原始_給EAP").mkdir()

# 把所有 PDF 集中到 EAP/PDF
for pdf in RAW.rglob("*.pdf"):
    shutil.copy2(pdf, EAP / "PDF" / pdf.name)
for pdf in GEN.glob("*.pdf"):
    shutil.copy2(pdf, EAP / "PDF" / pdf.name)

# CSV 節點 + 關係（核心 GraphRAG 餵料）
for csv in (ROOT / "CSV" / "節點").glob("*.csv"):
    shutil.copy2(csv, EAP / "CSV" / "節點" / csv.name)
for csv in (ROOT / "CSV" / "關係").glob("*.csv"):
    shutil.copy2(csv, EAP / "CSV" / "關係" / csv.name)

# 裁罰原始 CSV 也可以丟進 EAP 給 GraphRAG / VectorRAG 都用
for csv in (ROOT / "CSV" / "裁罰").glob("*.csv"):
    if "統計" in csv.name or "清理" in csv.name or csv.stem in ["D_災保法裁罰名單", "D_職安違規案例", "D_勞基法違規案例"]:
        shutil.copy2(csv, EAP / "CSV" / "裁罰原始_給EAP" / csv.name)

# 印新結構
print("=== 新結構 ===")
for sub in sorted(NEW.rglob("*")):
    if sub.is_file():
        rel = sub.relative_to(NEW)
        size = sub.stat().st_size
        print(f"  {size:>10,} B  {rel}")

# 替換舊資料夾
OLD_BACKUP = ROOT.parent / "資料_舊版備份"
if OLD_BACKUP.exists():
    shutil.rmtree(OLD_BACKUP)
ROOT.rename(OLD_BACKUP)
NEW.rename(ROOT)
print(f"\n舊資料夾備份至：{OLD_BACKUP}")
print(f"新資料夾：{ROOT}")
