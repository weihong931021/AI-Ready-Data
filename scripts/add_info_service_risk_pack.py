"""
資訊服務業增強包：
- 補強系統上線過勞、夜間值班、incident 緊急維運、駐點客戶現場、IDC 維運、職場不法侵害/性騷擾情境。
- 新增工作情境、證據資料、處置任務、企業角色節點。
- 新增工作情境到事故/法規/證據/任務/產業，以及任務到角色、證據到法規的關係。
- 補充 L031-L035，讓 GraphRAG 能接住工時、異常工作負荷與不法侵害指引。

可重跑；既有節點和關係會去重保留。
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EAP = ROOT / "資料" / "3_EAP上傳" / "CSV"
NODE = EAP / "節點"
REL = EAP / "關係"


def read_rows(path: Path):
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def write_rows(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def upsert(path: Path, header, new_rows, key_cols=(0,)):
    old_header, rows = read_rows(path)
    if old_header and old_header != header:
        raise ValueError(f"欄位不一致: {path}\n現有: {old_header}\n預期: {header}")
    index = {tuple(row[i] for i in key_cols): row for row in rows}
    added = 0
    for row in new_rows:
        key = tuple(row[i] for i in key_cols)
        if key not in index:
            rows.append(row)
            index[key] = row
            added += 1
    write_rows(path, header, rows)
    return added, len(rows)


def replace_file(path: Path, header, rows):
    write_rows(path, header, rows)
    return len(rows)


LAWS = [
    ["L031", "職業安全衛生設施規則", "第324-2條", "異常工作負荷促發疾病預防措施（過勞風險評估與改善）"],
    ["L032", "職業安全衛生設施規則", "第324-3條", "執行職務遭受不法侵害預防措施（職場霸凌/暴力/第三方侵害）"],
    ["L033", "勞動基準法", "第30條", "正常工時、出勤紀錄記載與保存義務"],
    ["L034", "勞動基準法", "第32條", "延長工時限制、加班程序與工時上限"],
    ["L035", "勞動基準法", "第36條", "例假、休息日與連續出勤限制"],
]

SCENARIOS = [
    ["S001", "系統上線長工時", "IND_08", "過勞職業病", "系統上線 deploy cutover 熬夜 值班 on-call 心血管", "主Demo"],
    ["S002", "夜間值班與 on-call", "IND_08", "異常工作負荷", "夜間值班 on-call 待命 告警 半夜維運", "主Demo補充"],
    ["S003", "Incident 緊急維運", "IND_08", "精神緊張與長時間工作", "incident SLA 緊急修復 客戶壓力 障礙排除", "主Demo補充"],
    ["S004", "駐點客戶機房搬運受傷", "IND_08", "客戶現場職災與責任邊界", "駐點 客戶現場 機房 搬伺服器 機櫃 腰傷", "主Demo"],
    ["S005", "客戶拜訪或公出途中事故", "IND_08", "通勤/公出職災", "客戶拜訪 出差 維修途中 車禍 公出", "雙面介面"],
    ["S006", "客戶或主管職場不法侵害", "IND_08", "不法侵害/霸凌/性騷擾", "客戶辱罵 主管霸凌 性騷擾 申訴 第三方侵害", "主Demo"],
    ["S007", "IDC 機房維運事故", "IND_08", "機房職安/人因/電氣風險", "IDC 資料中心 機房 線路 電源 跌倒 搬運", "延伸案例"],
]

EVIDENCE = [
    ["E001", "出勤紀錄", "計算工時、加班、輪班與連續出勤", "HR/差勤系統", "S001;S002;S003"],
    ["E002", "加班申請與核准紀錄", "證明延長工時與主管核准", "OA/HR 系統", "S001;S002;S003"],
    ["E003", "值班表 / on-call 排班", "證明待命、夜間工作與輪班安排", "PM/維運排班系統", "S001;S002"],
    ["E004", "Incident ticket / 告警紀錄", "證明突發事件、處理時間與精神負荷", "ITSM/Jira/ServiceNow", "S002;S003"],
    ["E005", "系統上線計畫 / 割接紀錄", "證明高壓上線時程與工作內容", "專案文件/變更管理", "S001;S003"],
    ["E006", "客戶派工單 / 工作指派", "證明公出、駐點、客戶現場工作與指揮來源", "PM/客戶系統", "S004;S005;S007"],
    ["E007", "客戶現場簽到 / 門禁紀錄", "證明事故地點、時間與是否在執行職務", "客戶場域/門禁系統", "S004;S005;S007"],
    ["E008", "機房作業申請 / 變更單", "證明機房作業內容與風險控制", "變更管理系統", "S004;S007"],
    ["E009", "診斷證明 / 病歷摘要", "證明傷病結果與醫療處置", "醫療院所", "S001;S004;S005;S006;S007"],
    ["E010", "申訴紀錄 / 通報單", "啟動不法侵害或性騷擾事件處理", "申訴系統/HR", "S006"],
    ["E011", "調查訪談紀錄", "釐清不法侵害、霸凌、性騷擾或第三方侵害事實", "HR/調查小組", "S006"],
    ["E012", "諮商 / 調整工作紀錄", "證明補救、保護與追蹤措施", "HR/EAP/主管", "S006"],
    ["E013", "專案會議紀錄 / 即時訊息紀錄", "補強精神緊張、客戶壓力與工作負荷時序", "PM/Teams/Slack/Email", "S001;S003;S006"],
    ["E014", "合約 / 駐點服務範圍", "判斷承攬、派遣、駐點與客戶責任邊界", "法務/業務/PM", "S004;S005;S007"],
]

TASKS = [
    ["T001", "啟動職災初判", "24小時內", "事故初判紀錄", "判斷工傷、職業病、通勤、公出或不法侵害類型"],
    ["T002", "蒐集工時與值班證據", "3日內", "工時與值班證據清單", "整理發病前1日、1週、1個月與6個月工作負荷"],
    ["T003", "評估異常工作負荷", "7日內", "過勞風險評估表", "對照職業促發腦心血管疾病認定指引與預防指引"],
    ["T004", "通知 HR / 法務 / PM / 職安窗口", "即時", "內部通知紀錄", "建立事故或申訴處理責任分工"],
    ["T005", "評估職災給付與雇主補償", "7日內", "給付與補償清單", "對照勞基法§59與災保法給付"],
    ["T006", "檢查客戶現場責任邊界", "3日內", "合約/派工責任檢核", "釐清駐點、承攬、派遣、客戶指揮與雇主責任"],
    ["T007", "啟動不法侵害申訴處理", "即時", "受理紀錄", "處理職場霸凌、暴力、性騷擾或第三方侵害"],
    ["T008", "成立調查或處理小組", "3日內", "小組名單與調查計畫", "對應不法侵害預防指引與性平處理義務"],
    ["T009", "採取保護與工作調整", "即時", "保護/調整措施紀錄", "避免二次傷害、報復或持續接觸風險"],
    ["T010", "提供諮商、醫療或外部資源", "7日內", "轉介紀錄", "支援身心健康、醫療與心理諮商"],
    ["T011", "完成改善與教育訓練", "30日內", "改善計畫/訓練紀錄", "更新制度並預防再發"],
    ["T012", "盤點同業裁罰與制度缺口", "14日內", "資訊服務業風險雷達報告", "接 IND_08 與完整裁罰資料層"],
]

ROLES = [
    ["ROLE_HR", "人資", "受理職災/申訴、蒐集差勤與補償資料、協調保護措施", "受理紀錄、差勤證據、補償清單"],
    ["ROLE_PM", "專案經理", "提供上線、值班、派工與客戶現場工作脈絡", "專案時序、派工單、上線紀錄"],
    ["ROLE_EHS", "職安/勞安窗口", "執行職災初判、職安風險評估、通報與改善追蹤", "職災初判、風險評估、改善計畫"],
    ["ROLE_LEGAL", "法務", "判斷合約責任、民刑事風險與調查程序合規", "責任邊界、法規風險意見"],
    ["ROLE_MANAGER", "單位主管/高階主管", "決定保護措施、資源投入、制度改善與治理回報", "決策紀錄、改善承諾"],
    ["ROLE_WORKER", "勞工/申訴人", "提供事件經過、醫療資料、申訴與權益需求", "陳述、申請資料、申訴資料"],
    ["ROLE_CLIENT", "客戶窗口", "提供客戶現場紀錄、門禁、派工與第三方事實資料", "門禁紀錄、派工確認、現場證明"],
]

REL_SCENARIO_ACCIDENT = [
    ["S001", "A005"], ["S002", "A005"], ["S003", "A005"],
    ["S004", "A003"], ["S005", "A001"],
    ["S007", "A003"], ["S007", "A004"],
]

REL_SCENARIO_LAW = [
    *[["S001", x] for x in ["L001", "L004", "L005", "L006", "L010", "L024", "L025", "L027", "L028", "L031", "L033", "L034", "L035"]],
    *[["S002", x] for x in ["L004", "L005", "L010", "L024", "L025", "L031", "L033", "L034", "L035"]],
    *[["S003", x] for x in ["L004", "L005", "L010", "L024", "L025", "L031", "L033", "L034"]],
    *[["S004", x] for x in ["L001", "L002", "L004", "L005", "L008", "L011", "L012", "L024", "L025"]],
    *[["S005", x] for x in ["L001", "L003", "L004", "L005", "L024", "L025"]],
    *[["S006", x] for x in ["L008", "L021", "L022", "L024", "L025", "L032"]],
    *[["S007", x] for x in ["L001", "L004", "L005", "L008", "L009", "L011", "L012", "L024", "L025"]],
]

REL_SCENARIO_EVIDENCE = [
    *[["S001", x] for x in ["E001", "E002", "E003", "E004", "E005", "E009", "E013"]],
    *[["S002", x] for x in ["E001", "E002", "E003", "E004", "E009"]],
    *[["S003", x] for x in ["E001", "E002", "E004", "E005", "E009", "E013"]],
    *[["S004", x] for x in ["E006", "E007", "E008", "E009", "E014"]],
    *[["S005", x] for x in ["E006", "E007", "E009", "E014"]],
    *[["S006", x] for x in ["E010", "E011", "E012", "E013", "E009"]],
    *[["S007", x] for x in ["E006", "E007", "E008", "E009", "E014"]],
]

REL_SCENARIO_TASK = [
    *[["S001", x] for x in ["T001", "T002", "T003", "T004", "T005", "T012"]],
    *[["S002", x] for x in ["T001", "T002", "T003", "T004", "T005", "T012"]],
    *[["S003", x] for x in ["T001", "T002", "T003", "T004", "T005", "T012"]],
    *[["S004", x] for x in ["T001", "T004", "T005", "T006", "T012"]],
    *[["S005", x] for x in ["T001", "T004", "T005", "T006"]],
    *[["S006", x] for x in ["T004", "T007", "T008", "T009", "T010", "T011", "T012"]],
    *[["S007", x] for x in ["T001", "T004", "T005", "T006", "T011", "T012"]],
]

REL_TASK_ROLE = [
    ["T001", "ROLE_HR"], ["T001", "ROLE_EHS"],
    ["T002", "ROLE_HR"], ["T002", "ROLE_PM"],
    ["T003", "ROLE_EHS"], ["T003", "ROLE_HR"],
    ["T004", "ROLE_HR"], ["T004", "ROLE_PM"], ["T004", "ROLE_LEGAL"], ["T004", "ROLE_EHS"],
    ["T005", "ROLE_HR"], ["T005", "ROLE_LEGAL"],
    ["T006", "ROLE_PM"], ["T006", "ROLE_LEGAL"], ["T006", "ROLE_CLIENT"],
    ["T007", "ROLE_HR"], ["T007", "ROLE_WORKER"],
    ["T008", "ROLE_HR"], ["T008", "ROLE_LEGAL"], ["T008", "ROLE_MANAGER"],
    ["T009", "ROLE_HR"], ["T009", "ROLE_MANAGER"],
    ["T010", "ROLE_HR"], ["T010", "ROLE_WORKER"],
    ["T011", "ROLE_HR"], ["T011", "ROLE_EHS"], ["T011", "ROLE_MANAGER"],
    ["T012", "ROLE_HR"], ["T012", "ROLE_LEGAL"], ["T012", "ROLE_MANAGER"],
]

REL_EVIDENCE_LAW = [
    ["E001", "L010"], ["E001", "L031"], ["E001", "L033"], ["E001", "L034"], ["E001", "L035"],
    ["E002", "L034"], ["E003", "L031"], ["E004", "L031"], ["E005", "L031"],
    ["E006", "L002"], ["E006", "L003"], ["E007", "L003"], ["E008", "L008"], ["E008", "L031"],
    ["E009", "L004"], ["E009", "L005"], ["E009", "L006"],
    ["E010", "L021"], ["E010", "L032"], ["E011", "L021"], ["E011", "L022"], ["E011", "L032"],
    ["E012", "L021"], ["E012", "L032"], ["E013", "L031"], ["E014", "L002"], ["E014", "L011"], ["E014", "L012"],
]

REL_SCENARIO_INDUSTRY = [[row[0], "IND_08"] for row in SCENARIOS]

R2_NEW = [
    ["L031", "D007"], ["L031", "D006"],
    ["L032", "D007"], ["L032", "D006"],
    ["L033", "D006"], ["L034", "D006"], ["L035", "D006"],
]

R3_NEW = [
    ["L031", "B001"], ["L031", "B005"],
    ["L032", "B001"], ["L032", "B005"],
]


def main():
    outputs = []
    added, total = upsert(NODE / "02_法規條文.csv", ["條文ID", "法規", "條號", "條文摘要"], LAWS, (0,))
    outputs.append(("02_法規條文.csv", added, total))

    outputs.append(("14_工作情境.csv", replace_file(NODE / "14_工作情境.csv", ["情境ID", "情境名稱", "產業ID", "主要風險", "描述關鍵字", "Demo定位"], SCENARIOS), len(SCENARIOS)))
    outputs.append(("15_證據資料.csv", replace_file(NODE / "15_證據資料.csv", ["證據ID", "證據名稱", "用途", "取得來源", "適用情境"], EVIDENCE), len(EVIDENCE)))
    outputs.append(("16_處置任務.csv", replace_file(NODE / "16_處置任務.csv", ["任務ID", "任務名稱", "時限", "輸出物", "說明"], TASKS), len(TASKS)))
    outputs.append(("17_企業角色.csv", replace_file(NODE / "17_企業角色.csv", ["角色ID", "角色名稱", "責任範圍", "常見輸出"], ROLES), len(ROLES)))

    added, total = upsert(REL / "R2_法規衍生義務.csv", ["條文ID", "義務ID"], R2_NEW, (0, 1))
    outputs.append(("R2_法規衍生義務.csv", added, total))
    added, total = upsert(REL / "R3_法規衍生權益.csv", ["條文ID", "權益ID"], R3_NEW, (0, 1))
    outputs.append(("R3_法規衍生權益.csv", added, total))

    relation_files = [
        ("R14_工作情境對應事故.csv", ["情境ID", "事故ID"], REL_SCENARIO_ACCIDENT),
        ("R15_工作情境適用法規.csv", ["情境ID", "條文ID"], REL_SCENARIO_LAW),
        ("R16_工作情境需證據.csv", ["情境ID", "證據ID"], REL_SCENARIO_EVIDENCE),
        ("R17_工作情境衍生任務.csv", ["情境ID", "任務ID"], REL_SCENARIO_TASK),
        ("R18_任務負責角色.csv", ["任務ID", "角色ID"], REL_TASK_ROLE),
        ("R19_證據支持法規判斷.csv", ["證據ID", "條文ID"], REL_EVIDENCE_LAW),
        ("R20_工作情境對應產業.csv", ["情境ID", "產業ID"], REL_SCENARIO_INDUSTRY),
    ]
    for filename, header, rows in relation_files:
        count = replace_file(REL / filename, header, rows)
        outputs.append((filename, count, count))

    print("資訊服務業增強包已更新")
    for name, added_or_count, total in outputs:
        if name.startswith("R14_") or name.startswith("R15_") or name.startswith("R16_") or name.startswith("R17_") or name.startswith("R18_") or name.startswith("R19_") or name.startswith("R20_") or name.startswith("14_") or name.startswith("15_") or name.startswith("16_") or name.startswith("17_"):
            print(f"- {name}: {total} 列")
        else:
            print(f"- {name}: 新增 {added_or_count}，目前 {total} 列")


if __name__ == "__main__":
    main()
