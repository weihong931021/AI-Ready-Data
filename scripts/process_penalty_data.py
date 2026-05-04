"""
處理真實裁罰資料，產生 EAP 可用的乾淨 CSV：
1. D_災保法裁罰名單.csv → 清理 + 統一格式
2. 衍生：按月統計、按法條分布、罰鍰級距分布（aggregate stats）
3. 整合進 GraphRAG schema（新增節點：裁罰案例 / 違規態樣 / 產業分類推測）
"""
from pathlib import Path
import re
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).parent.parent / "資料"
PENALTY_DIR = ROOT / "CSV" / "裁罰"
NODE_DIR = ROOT / "CSV" / "節點"
REL_DIR = ROOT / "CSV" / "關係"


def roc_to_iso(roc_str):
    """民國 1150330 → 2026-03-30"""
    s = str(roc_str).strip()
    if not s or s == "nan" or len(s) < 6:
        return ""
    s = s.zfill(7)
    try:
        year = int(s[:3]) + 1911
        month = int(s[3:5])
        day = int(s[5:7])
        return f"{year:04d}-{month:02d}-{day:02d}"
    except Exception:
        return ""


def infer_industry(name: str) -> str:
    """從公司名稱推測行業（粗略，但能 demo 用）"""
    if not isinstance(name, str):
        return "未分類"
    keywords = {
        "營造": ["營造", "建設", "建築", "工程行", "土木", "鋼構"],
        "製造": ["工業", "製造", "塑膠", "金屬", "機械", "電子", "科技", "材料", "鋼鋁", "化學"],
        "餐飲": ["餐廳", "小吃", "燒烤", "熱炒", "早餐", "便當", "飲料", "咖啡", "食品"],
        "零售批發": ["超商", "商行", "百貨", "零售", "批發", "貿易"],
        "物流運輸": ["運輸", "物流", "貨運", "通運", "搬家"],
        "醫療": ["診所", "醫院", "藥局", "醫療"],
        "教育": ["補習班", "幼兒園", "學校", "托嬰"],
        "金融保險": ["銀行", "保險", "金融", "投資"],
        "資訊服務": ["資訊", "軟體", "網路", "科技", "電腦"],
        "保全服務": ["保全"],
        "美容美髮": ["美容", "美髮", "美甲", "髮廊"],
        "農林漁牧": ["農場", "牧場", "畜", "養殖", "漁"],
    }
    for industry, kws in keywords.items():
        for kw in kws:
            if kw in name:
                return industry
    return "其他服務業"


def clean_penalty_csv():
    src = PENALTY_DIR / "D_災保法裁罰名單.csv"
    df = pd.read_csv(src, encoding="utf-8-sig")
    df.columns = [c.lstrip("*") for c in df.columns]
    df = df.rename(columns={
        "公告日期": "公告日期_民國",
        "公司名稱/負責人": "違規企業",
        "違反法規條款": "違反條款",
        "違反法規內容": "違規態樣",
        "處分字號": "處分字號",
        "處分日期": "處分日期_民國",
        "處分金額": "處分金額_元",
        "備註": "備註",
    })
    df["處分日期"] = df["處分日期_民國"].apply(roc_to_iso)
    df["公告日期"] = df["公告日期_民國"].apply(roc_to_iso)
    df["推測產業"] = df["違規企業"].apply(infer_industry)
    df["處分金額_元"] = pd.to_numeric(df["處分金額_元"], errors="coerce").fillna(0).astype(int)
    df["案例ID"] = ["PNL_" + str(i).zfill(6) for i in range(1, len(df) + 1)]

    cols = ["案例ID", "處分日期", "公告日期", "違規企業", "推測產業",
            "違反條款", "違規態樣", "處分金額_元", "處分字號"]
    out_clean = df[cols]
    out_path = PENALTY_DIR / "D_災保法裁罰名單_清理版.csv"
    out_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  ✓ 清理版：{out_path}（{len(out_clean)} 筆）")
    return df


def build_stats(df):
    # 按法條統計
    by_law = df.groupby("違反條款").agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
        金額平均=("處分金額_元", "mean"),
        金額最高=("處分金額_元", "max"),
    ).reset_index().sort_values("件數", ascending=False)
    by_law["金額平均"] = by_law["金額平均"].round(0).astype(int)
    out1 = PENALTY_DIR / "D_裁罰_按法條統計.csv"
    by_law.to_csv(out1, index=False, encoding="utf-8-sig")
    print(f"  ✓ {out1}（{len(by_law)} 條法條）")

    # 按產業統計
    by_industry = df.groupby("推測產業").agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
        金額平均=("處分金額_元", "mean"),
    ).reset_index().sort_values("件數", ascending=False)
    by_industry["金額平均"] = by_industry["金額平均"].round(0).astype(int)
    out2 = PENALTY_DIR / "D_裁罰_按產業統計.csv"
    by_industry.to_csv(out2, index=False, encoding="utf-8-sig")
    print(f"  ✓ {out2}（{len(by_industry)} 個產業類別）")

    # 按月統計
    df["處分年月"] = df["處分日期"].str[:7]
    by_month = df.groupby("處分年月").agg(
        件數=("案例ID", "count"),
        金額總和=("處分金額_元", "sum"),
    ).reset_index().sort_values("處分年月")
    out3 = PENALTY_DIR / "D_裁罰_按月份統計.csv"
    by_month.to_csv(out3, index=False, encoding="utf-8-sig")
    print(f"  ✓ {out3}（{len(by_month)} 個月）")


def build_violation_pattern_node(df):
    """違規態樣 → 節點表（GraphRAG 新增節點類型）"""
    patterns = df.groupby("違規態樣").agg(
        件數=("案例ID", "count"),
        金額平均=("處分金額_元", "mean"),
        違反條款=("違反條款", "first"),
    ).reset_index()
    patterns["金額平均"] = patterns["金額平均"].round(0).astype(int)
    patterns["態樣ID"] = ["VP_" + str(i).zfill(3) for i in range(1, len(patterns) + 1)]
    patterns = patterns[["態樣ID", "違規態樣", "違反條款", "件數", "金額平均"]]
    out = NODE_DIR / "08_違規態樣.csv"
    patterns.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  ✓ {out}（{len(patterns)} 種態樣）")


def build_industry_node(df):
    """產業 → 節點表"""
    industries = df["推測產業"].unique()
    rows = []
    for i, ind in enumerate(sorted(industries), 1):
        case_count = (df["推測產業"] == ind).sum()
        avg_fine = df[df["推測產業"] == ind]["處分金額_元"].mean()
        rows.append({
            "產業ID": "IND_" + str(i).zfill(2),
            "產業名稱": ind,
            "災保法裁罰件數": int(case_count),
            "平均罰鍰_元": int(round(avg_fine)),
        })
    pd.DataFrame(rows).to_csv(NODE_DIR / "09_產業.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ 09_產業.csv（{len(rows)} 個產業）")


def build_relations(df):
    """產業 ↔ 違規態樣（多對多）"""
    pairs = df.groupby(["推測產業", "違規態樣"]).size().reset_index(name="件數")
    # 建索引
    industries = sorted(df["推測產業"].unique())
    ind_idx = {ind: f"IND_{i:02d}" for i, ind in enumerate(industries, 1)}
    patterns = sorted(df["違規態樣"].unique())
    pat_idx = {pat: f"VP_{i:03d}" for i, pat in enumerate(patterns, 1)}
    pairs["產業ID"] = pairs["推測產業"].map(ind_idx)
    pairs["態樣ID"] = pairs["違規態樣"].map(pat_idx)
    out = pairs[["產業ID", "態樣ID", "件數"]]
    out.to_csv(REL_DIR / "R6_產業常見違規態樣.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ R6_產業常見違規態樣.csv（{len(out)} 對）")


if __name__ == "__main__":
    print("=== 處理裁罰資料 ===")
    df = clean_penalty_csv()
    print("\n=== 統計衍生 ===")
    build_stats(df)
    print("\n=== GraphRAG 節點擴充 ===")
    build_violation_pattern_node(df)
    build_industry_node(df)
    print("\n=== GraphRAG 關係擴充 ===")
    build_relations(df)
    print("\n完成。")
