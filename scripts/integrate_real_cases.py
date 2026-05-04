"""
把爬到的真實裁罰案例（OSHA + LBR）整合進 GraphRAG schema：
1. 把每筆案例變成節點（裁罰案例.csv）
2. 用「違反法條」字串對映到既有的 5 個事故類型 + 10 條法規
3. 產出新關係檔：R7_案例對應事故.csv、R8_案例違反法條.csv
4. 衍生統計：產業 / 違規類型 / 金額分布
"""
import csv
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent / "資料"
PENALTY_DIR = ROOT / "CSV" / "裁罰"
NODE_DIR = ROOT / "CSV" / "節點"
REL_DIR = ROOT / "CSV" / "關係"


def infer_industry(name: str) -> str:
    if not isinstance(name, str):
        return "未分類"
    keywords = {
        "營造": ["營造", "建設", "建築", "工程行", "土木", "鋼構"],
        "製造": ["工業", "製造", "塑膠", "金屬", "機械", "電子", "科技", "材料", "鋼鋁", "化學", "紡織", "玻璃"],
        "餐飲": ["餐廳", "小吃", "燒烤", "熱炒", "早餐", "便當", "飲料", "咖啡", "食品"],
        "零售批發": ["超商", "商行", "百貨", "零售", "批發", "貿易"],
        "物流運輸": ["運輸", "物流", "貨運", "通運", "搬家"],
        "醫療": ["診所", "醫院", "藥局", "醫療"],
        "教育": ["補習班", "幼兒園", "學校", "托嬰"],
        "金融保險": ["銀行", "保險", "金融", "投資"],
        "資訊服務": ["資訊", "軟體", "網路", "電腦"],
        "保全服務": ["保全"],
        "美容美髮": ["美容", "美髮", "美甲", "髮廊"],
        "農林漁牧": ["農場", "牧場", "畜", "養殖", "漁"],
    }
    for industry, kws in keywords.items():
        for kw in kws:
            if kw in name:
                return industry
    return "其他服務業"


# 事故類型對映規則：法條 keyword → 事故ID
# 邏輯：哪些違反條款最容易導致哪種事故
ACCIDENT_MAPPING = [
    # A002 工地墜落 (高處、營造)
    (r"營造安全衛生設施標準第\s*19", "A002"),  # 高處作業防護
    (r"營造安全衛生設施標準第\s*1[1-8]", "A002"),  # 工地一般安全
    (r"營造安全衛生設施標準", "A002"),
    (r"職業安全衛生法第\s*37", "A002"),  # 重大職災通報，通常是死亡或重大墜落
    # A003 搬運受傷 (起重機具相關)
    (r"職業安全衛生法第\s*6\s*條第\s*1\s*項第\s*5", "A003"),  # 起重機具防護脫落
    (r"起重", "A003"),
    # A004 化學品暴露 (危險物質、特定化學)
    (r"特定化學", "A004"),
    (r"有機溶劑", "A004"),
    (r"危險物", "A004"),
    (r"職業安全衛生設施規則第\s*[3-5][0-9]", "A004"),
    # A005 過勞 (工時、加班)
    (r"勞動基準法第\s*32", "A005"),  # 加班時數
    (r"勞動基準法第\s*30", "A005"),  # 工時、出勤紀錄
    (r"勞動基準法第\s*36", "A005"),  # 例假休息日
    (r"勞動基準法第\s*34", "A005"),  # 輪班制休息
    (r"勞動基準法第\s*22", "A005"),  # 工資給付（過勞情境延伸）
    (r"勞動基準法第\s*24", "A005"),  # 加班費
    # A001 通勤事故 (沒有直接違規對應；通勤是事實認定，非違規)
    # → 無對映；A001 主要靠 災保法裁罰名單關聯
    # 一般職業安全 (對應全部事故)
    (r"職業安全衛生法第\s*6", "ANY"),  # 雇主預防義務
    (r"職業安全衛生設施規則", "ANY"),
]


def map_accidents(law_text: str) -> list[str]:
    """從違反法條字串推測對應的事故類型。"""
    if not isinstance(law_text, str):
        return []
    accidents = set()
    for pattern, aid in ACCIDENT_MAPPING:
        if re.search(pattern, law_text):
            if aid == "ANY":
                accidents.update(["A002", "A003", "A004"])  # 一般職安預防 → 工傷類型
            else:
                accidents.add(aid)
    return sorted(accidents)


# 對映到既有的法規條文 ID（02_法規條文.csv 中的 L001-L010）
LAW_MAPPING = [
    (r"勞動基準法第\s*59", "L001"),
    (r"勞動基準法第\s*63\s*-\s*1", "L002"),
    (r"勞動基準法", "L001"),  # 其他勞基法條 → 歸到 L001 主條文
    (r"職業安全衛生法第\s*37", "L007"),
    (r"職業安全衛生法第\s*6", "L008"),
    (r"職業安全衛生法第\s*20", "L009"),
    (r"職業安全衛生法", "L008"),
    (r"職業安全衛生設施規則", "L008"),
    (r"營造安全衛生", "L008"),
]


def map_laws(law_text: str) -> list[str]:
    if not isinstance(law_text, str):
        return []
    out = []
    for pattern, lid in LAW_MAPPING:
        if re.search(pattern, law_text):
            if lid not in out:
                out.append(lid)
            break  # 取第一個匹配
    return out


def process():
    # 讀檔
    osha = pd.read_csv(PENALTY_DIR / "D_職安違規案例.csv", encoding="utf-8-sig")
    lbr = pd.read_csv(PENALTY_DIR / "D_勞基法違規案例.csv", encoding="utf-8-sig")

    # 補產業
    osha["推測產業"] = osha["違規企業"].apply(infer_industry)
    lbr["推測產業"] = lbr["違規企業"].apply(infer_industry)

    # 合併成一個 案例節點
    cases = []
    for _, r in osha.iterrows():
        cases.append({
            "案例ID": r["案例ID"],
            "資料來源": "勞動部違反勞動法令查詢系統",
            "處分日期": r["處分日期"],
            "違規企業": r["違規企業"],
            "推測產業": r["推測產業"],
            "違反法條": r["違反法條"],
            "違規態樣": r["違規態樣"],
            "處分金額_元": r["處分金額_元"],
            "縣市": r["縣市"],
            "處分字號": r["處分字號"],
        })
    for _, r in lbr.iterrows():
        cases.append({
            "案例ID": r["案例ID"],
            "資料來源": "勞動部違反勞動法令查詢系統",
            "處分日期": r["處分日期"],
            "違規企業": r["違規企業"],
            "推測產業": r["推測產業"],
            "違反法條": r["違反法條"],
            "違規態樣": r["違規態樣"],
            "處分金額_元": r["處分金額_元"],
            "縣市": r["縣市"],
            "處分字號": r["處分字號"],
        })

    out = pd.DataFrame(cases)
    out_path = NODE_DIR / "10_裁罰案例.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  ✓ {out_path}（{len(out)} 筆案例節點）")

    # R7：案例 ↔ 事故類型
    r7 = []
    for _, r in out.iterrows():
        for aid in map_accidents(r["違反法條"]):
            r7.append({"案例ID": r["案例ID"], "事故ID": aid})
    pd.DataFrame(r7).to_csv(REL_DIR / "R7_案例對應事故.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ R7_案例對應事故.csv（{len(r7)} 條邊）")

    # R8：案例 ↔ 法規條文
    r8 = []
    for _, r in out.iterrows():
        for lid in map_laws(r["違反法條"]):
            r8.append({"案例ID": r["案例ID"], "條文ID": lid})
    pd.DataFrame(r8).to_csv(REL_DIR / "R8_案例違反法條.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ R8_案例違反法條.csv（{len(r8)} 條邊）")

    # 衍生統計
    by_law = out.groupby("違反法條").agg(
        件數=("案例ID", "count"),
        金額平均=("處分金額_元", "mean"),
        金額最高=("處分金額_元", "max"),
    ).reset_index().sort_values("件數", ascending=False)
    by_law["金額平均"] = by_law["金額平均"].round(0).astype(int)
    by_law.to_csv(PENALTY_DIR / "D_職安勞基_按法條統計.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ D_職安勞基_按法條統計.csv（{len(by_law)} 條法條）")

    by_industry = out.groupby("推測產業").agg(
        件數=("案例ID", "count"),
        金額平均=("處分金額_元", "mean"),
        金額總和=("處分金額_元", "sum"),
    ).reset_index().sort_values("件數", ascending=False)
    by_industry["金額平均"] = by_industry["金額平均"].round(0).astype(int)
    by_industry.to_csv(PENALTY_DIR / "D_職安勞基_按產業統計.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ D_職安勞基_按產業統計.csv（{len(by_industry)} 個產業）")

    # 印 sample 看對映品質
    print(f"\n=== 案例 → 事故對映 sample ===")
    sample = out.sample(min(8, len(out)), random_state=2)
    for _, r in sample.iterrows():
        accidents = map_accidents(r["違反法條"])
        laws = map_laws(r["違反法條"])
        print(f"  {r['案例ID']} | {r['違反法條'][:35]:35} → 事故{accidents} 法規{laws}")


if __name__ == "__main__":
    process()
