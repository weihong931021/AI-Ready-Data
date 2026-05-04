"""
整合四份裁罰來源，產出完整裁罰資料層。

輸入（1_原始下載/裁罰_原始/）：
  D_災保法裁罰名單.csv      15,939 筆
  D_勞退條例裁罰名單.csv     9,973 筆
  D_職安違規案例.csv          475 筆（已在 scrape_osha_violations.py 生成）
  D_勞基法違規案例.csv        128 筆（同上）

輸出（3_EAP上傳/CSV/裁罰原始_給EAP/）：
  D_勞退條例裁罰名單.csv               原始格式，補進 EAP 上傳包
  D_勞退條例裁罰名單_清理版.csv         清理後（ISO 日期、數值金額）
  D_全部裁罰案例_清理版.csv            四來源統一格式合併，~26,513 筆
  D_全部裁罰_按來源統計.csv
  D_全部裁罰_按月份統計.csv
  D_全部裁罰_按法條統計.csv
  D_全部裁罰_按產業統計.csv

另輸出（3_EAP上傳/CSV/節點/）：
  10_裁罰案例_精簡版.csv               原有 603 筆 OSHA+LBR（備份留用）
"""
import shutil
from pathlib import Path
import pandas as pd
import re

ROOT      = Path(__file__).parent.parent / "資料"
RAW_DIR   = ROOT / "1_原始下載" / "裁罰_原始"
EAP_PEN   = ROOT / "3_EAP上傳" / "CSV" / "裁罰原始_給EAP"
EAP_NODE  = ROOT / "3_EAP上傳" / "CSV" / "節點"
EAP_PEN.mkdir(parents=True, exist_ok=True)


# ── 日期工具 ─────────────────────────────────────────────────────────────────

def roc_to_iso(val) -> str:
    """民國 1150415 / '115/04/15' / '2026-04-15' → '2026-04-15'."""
    s = str(val).strip()
    if not s or s.lower() in ("nan", "", "none"):
        return ""
    # Already ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    # 民國 compact: 7 digits (e.g. 1150415)
    m = re.match(r"^(\d{2,3})(\d{2})(\d{2})$", s.replace(" ", ""))
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 200:
            y += 1911
        return f"{y:04d}-{mo:02d}-{d:02d}"
    # 民國 slash: 115/04/15 or 115-04-15
    m = re.match(r"^(\d{2,3})[/\-.](\d{1,2})[/\-.](\d{1,2})$", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 200:
            y += 1911
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return s


def clean_amount(val) -> int:
    """' 5,000 ' / 20000 / '' → int."""
    s = re.sub(r"[^0-9]", "", str(val))
    return int(s) if s else 0


# ── 產業推測 ─────────────────────────────────────────────────────────────────

INDUSTRY_MAP = {
    "營造":     ["營造", "建設", "建築", "工程行", "土木", "鋼構", "施工"],
    "製造":     ["工業", "製造", "塑膠", "金屬", "機械", "電子", "材料", "鋼鋁", "化學", "印刷", "包裝"],
    "餐飲":     ["餐廳", "小吃", "燒烤", "熱炒", "早餐", "便當", "飲料", "咖啡", "食品", "餐飲"],
    "零售批發": ["超商", "商行", "百貨", "零售", "批發", "貿易", "商店"],
    "物流運輸": ["運輸", "物流", "貨運", "通運", "搬家", "快遞"],
    "醫療":     ["診所", "醫院", "藥局", "醫療", "健康"],
    "教育":     ["補習班", "幼兒園", "學校", "托嬰", "才藝"],
    "金融保險": ["銀行", "保險", "金融", "投資", "證券"],
    "資訊服務": ["資訊", "軟體", "網路", "科技", "電腦", "數位"],
    "保全服務": ["保全", "保安"],
    "美容美髮": ["美容", "美髮", "美甲", "髮廊", "美睫"],
    "農林漁牧": ["農場", "牧場", "畜", "養殖", "漁", "農業"],
    "住宿旅遊": ["旅館", "民宿", "旅遊", "飯店", "hotel"],
}

def infer_industry(name: str) -> str:
    if not isinstance(name, str):
        return "未分類"
    name_l = name.lower()
    for industry, kws in INDUSTRY_MAP.items():
        for kw in kws:
            if kw in name_l or kw.lower() in name_l:
                return industry
    return "其他服務業"


# ── 讀取各來源 ────────────────────────────────────────────────────────────────

def load_pnl() -> pd.DataFrame:
    """災保法（D_災保法裁罰名單.csv）"""
    src = RAW_DIR / "D_災保法裁罰名單.csv"
    df = pd.read_csv(src, encoding="utf-8-sig")
    df.columns = [c.lstrip("*") for c in df.columns]
    df = df.rename(columns={
        "公告日期": "公告日期_raw",
        "公司名稱/負責人": "違規企業",
        "違反法規條款": "違反法條",
        "違反法規內容": "違規態樣",
        "處分日期": "處分日期_raw",
        "處分金額": "金額_raw",
    })
    df["資料來源"] = "災保法"
    df["法規類別"] = "勞工職業災害保險及保護法"
    df["處分日期"]  = df["處分日期_raw"].apply(roc_to_iso)
    df["公告日期"]  = df["公告日期_raw"].apply(roc_to_iso)
    df["處分金額_元"] = df["金額_raw"].apply(clean_amount)
    df["推測產業"]   = df["違規企業"].apply(infer_industry)
    df["縣市"]       = ""
    df["案例ID"]     = ["PNL_" + str(i).zfill(6) for i in range(1, len(df) + 1)]
    return df[_COLS]


def load_lpr() -> pd.DataFrame:
    """勞退條例（D_勞退條例裁罰名單.csv，跳過前 2 列描述行）"""
    src = RAW_DIR / "D_勞退條例裁罰名單.csv"
    df = pd.read_csv(src, encoding="utf-8-sig", skiprows=2)
    df.columns = [c.strip() for c in df.columns]
    # 欄位名可能有 trailing comma → 最後一欄是空欄
    df = df.loc[:, [c for c in df.columns if c.strip() != ""]]
    df = df.rename(columns={
        "公告日期": "公告日期_raw",
        "處分日期": "處分日期_raw",
        "單位名稱(負責人)或自然人姓名": "違規企業",
        "違反勞工退休金條例條款": "違反法條",
        "違反法規內容": "違規態樣",
        "處分金額": "金額_raw",
        "備註": "備註",
    })
    df["資料來源"] = "勞退條例"
    df["法規類別"] = "勞工退休金條例"
    df["處分日期"]  = df["處分日期_raw"].apply(roc_to_iso)
    df["公告日期"]  = df["公告日期_raw"].apply(roc_to_iso)
    df["處分金額_元"] = df["金額_raw"].apply(clean_amount)
    df["推測產業"]   = df["違規企業"].apply(infer_industry)
    df["縣市"]       = ""
    df["案例ID"]     = ["LPR_" + str(i).zfill(6) for i in range(1, len(df) + 1)]
    if "備註" not in df.columns:
        df["備註"] = ""
    return df[_COLS]


def load_osha() -> pd.DataFrame:
    """職安違規案例（已在 EAP 上傳包中，格式已清理）"""
    src = EAP_PEN / "D_職安違規案例.csv"
    df = pd.read_csv(src, encoding="utf-8-sig")
    df = df.rename(columns={"違反法條": "違反法條"})
    df["資料來源"] = "職安法"
    df["法規類別"] = "職業安全衛生法"
    df["公告日期"]  = ""
    if "推測產業" not in df.columns:
        df["推測產業"] = df["違規企業"].apply(infer_industry)
    if "備註" not in df.columns:
        df["備註"] = ""
    # 欄位對應
    df = df.rename(columns={"處分金額_元": "處分金額_元"})
    return df[_COLS]


def load_lbr() -> pd.DataFrame:
    """勞基法違規案例（已在 EAP 上傳包中，格式已清理）"""
    src = EAP_PEN / "D_勞基法違規案例.csv"
    df = pd.read_csv(src, encoding="utf-8-sig")
    df["資料來源"] = "勞基/性平/最低工資"
    df["法規類別"] = "勞動基準法等"
    df["公告日期"]  = ""
    if "推測產業" not in df.columns:
        df["推測產業"] = df["違規企業"].apply(infer_industry)
    if "備註" not in df.columns:
        df["備註"] = ""
    return df[_COLS]


# 統一欄位順序
_COLS = ["案例ID", "資料來源", "法規類別", "處分日期", "公告日期",
         "違規企業", "推測產業", "違反法條", "違規態樣",
         "處分金額_元", "縣市", "處分字號", "備註"]


# ── 統計 ──────────────────────────────────────────────────────────────────────

def build_stats(df: pd.DataFrame):
    # 按來源
    by_src = df.groupby("資料來源").agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
        金額平均=("處分金額_元", "mean"),
        金額最高=("處分金額_元", "max"),
    ).reset_index().sort_values("件數", ascending=False)
    by_src["金額平均"] = by_src["金額平均"].round(0).astype(int)
    _save(by_src, "D_全部裁罰_按來源統計.csv")

    # 按月份
    df2 = df.copy()
    df2["處分年月"] = df2["處分日期"].str[:7]
    by_month = df2.groupby("處分年月").agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
    ).reset_index().sort_values("處分年月")
    _save(by_month, "D_全部裁罰_按月份統計.csv")

    # 按法條（前 50）
    by_law = df.groupby(["法規類別", "違反法條"]).agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
        金額平均=("處分金額_元", "mean"),
    ).reset_index().sort_values("件數", ascending=False).head(100)
    by_law["金額平均"] = by_law["金額平均"].round(0).astype(int)
    _save(by_law, "D_全部裁罰_按法條統計.csv")

    # 按產業
    by_ind = df.groupby(["推測產業", "資料來源"]).agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
        金額平均=("處分金額_元", "mean"),
    ).reset_index().sort_values(["推測產業", "件數"], ascending=[True, False])
    by_ind["金額平均"] = by_ind["金額平均"].round(0).astype(int)
    _save(by_ind, "D_全部裁罰_按產業統計.csv")


def _save(df: pd.DataFrame, name: str):
    path = EAP_PEN / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  ✓ {name}（{len(df)} 列）")


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    print("=== 建立完整裁罰資料包 ===\n")

    # 1. 複製勞退原始到 EAP 上傳包
    src_lpr = RAW_DIR / "D_勞退條例裁罰名單.csv"
    dst_lpr = EAP_PEN / "D_勞退條例裁罰名單.csv"
    shutil.copy2(src_lpr, dst_lpr)
    print(f"[1] 複製勞退原始 → {dst_lpr}")

    # 2. 讀取四個來源
    print("\n[2] 讀取四份來源...")
    df_pnl  = load_pnl();  print(f"  災保法：{len(df_pnl):,} 筆")
    df_lpr  = load_lpr();  print(f"  勞退條例：{len(df_lpr):,} 筆")
    df_osha = load_osha(); print(f"  職安：{len(df_osha):,} 筆")
    df_lbr  = load_lbr();  print(f"  勞基/性平：{len(df_lbr):,} 筆")

    # 3. 輸出勞退清理版
    print("\n[3] 輸出勞退清理版...")
    df_lpr.to_csv(EAP_PEN / "D_勞退條例裁罰名單_清理版.csv",
                  index=False, encoding="utf-8-sig")
    print(f"  ✓ D_勞退條例裁罰名單_清理版.csv（{len(df_lpr):,} 筆）")

    # 4. 合併全部
    print("\n[4] 合併全部裁罰資料...")
    all_df = pd.concat([df_pnl, df_lpr, df_osha, df_lbr], ignore_index=True)
    # 過濾無效列（企業名空、日期空）
    all_df = all_df[all_df["違規企業"].notna() & (all_df["違規企業"].str.strip() != "")]
    print(f"  合併後：{len(all_df):,} 筆")

    all_df.to_csv(EAP_PEN / "D_全部裁罰案例_清理版.csv",
                  index=False, encoding="utf-8-sig")
    print(f"  ✓ D_全部裁罰案例_清理版.csv（{len(all_df):,} 筆）")

    # 5. 統計
    print("\n[5] 產出統計...")
    build_stats(all_df)

    # 6. 備份舊版 GraphRAG 節點 → 精簡版
    node_src = EAP_NODE / "10_裁罰案例.csv"
    if node_src.exists():
        node_slim = EAP_NODE / "10_裁罰案例_精簡版.csv"
        shutil.copy2(node_src, node_slim)
        print(f"\n[6] 備份 10_裁罰案例.csv → 10_裁罰案例_精簡版.csv（{len(pd.read_csv(node_slim)):,} 筆）")

    print("\n=== 完成 ===")
    print(f"\n資料層摘要：")
    for src, cnt in all_df.groupby("資料來源").size().items():
        print(f"  {src}：{cnt:,} 筆")
    print(f"  ─────────────")
    print(f"  合計：{len(all_df):,} 筆")
    print(f"\nEAP 上傳建議：")
    print(f"  初賽 demo → 用 10_裁罰案例_精簡版.csv（{len(pd.read_csv(node_src)) if node_src.exists() else 0} 筆，速度快）")
    print(f"  提案數據  → 引用 D_全部裁罰案例_清理版.csv（{len(all_df):,} 筆）")
    print(f"  若 EAP 扛得住 → 可改用完整版取代 10_裁罰案例.csv")


if __name__ == "__main__":
    main()
