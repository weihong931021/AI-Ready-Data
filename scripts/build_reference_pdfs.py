"""
產生兩份精選教學參考集 PDF（公開字號 + 公開摘要彙編）：
1. I_職災法規常見函釋摘要彙編.pdf — 12 個關鍵主題的函釋字號 + 公開摘要
2. C_職災典型案例摘要集.pdf — 5 大事故類型各 3 個典型案例

內容來自勞動部、勞保局、職安署公開 FAQ 與宣導資料的彙整摘要，
用於 GraphRAG 系統訓練與 demo 展示。原文連結附在每筆條目後供查證。
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("CJK", FONT_PATH))

INTERP_DIR = Path(__file__).parent.parent / "資料" / "PDF原始" / "函釋"
CASE_DIR = Path(__file__).parent.parent / "資料" / "PDF原始" / "案例"
INTERP_DIR.mkdir(parents=True, exist_ok=True)
CASE_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("CJKTitle", parent=styles["Heading1"], fontName="CJK", fontSize=20, leading=28)
h2_style = ParagraphStyle("CJKH2", parent=styles["Heading2"], fontName="CJK", fontSize=14, leading=22, spaceBefore=14, textColor="#1a4480")
h3_style = ParagraphStyle("CJKH3", parent=styles["Heading3"], fontName="CJK", fontSize=11, leading=18, spaceBefore=8, textColor="#333333")
body_style = ParagraphStyle("CJKBody", parent=styles["BodyText"], fontName="CJK", fontSize=10, leading=16)
meta_style = ParagraphStyle("CJKMeta", parent=styles["BodyText"], fontName="CJK", fontSize=8, leading=12, textColor="#777777")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─── 函釋摘要彙編 ────────────────────────────────

INTERPRETATIONS = [
    {
        "topic": "通勤職災認定（一般情形）",
        "key_question": "勞工於上下班途中發生事故是否屬於職業災害？",
        "ruling": "勞工於上下班適當時間，從日常居住處所往返就業場所之應經途中發生事故而致之傷害，視為職業傷害。",
        "law_basis": "勞工職業災害保險職業傷病審查準則 第17條",
        "applied_to": ["A001 通勤事故"],
        "example": "勞工 06:30 騎機車從家中前往工地，途經紅綠燈被酒駕撞傷 → 視為職業傷害；雇主依勞基法§59 應給予醫療補償與工資補償。",
    },
    {
        "topic": "通勤職災認定（順道接送子女）",
        "key_question": "勞工順道送子女上學或托嬰途中發生事故，是否仍屬通勤職災？",
        "ruling": "勞工為日常生活所必需之私人行為，於上下班適當時間、應經途中順道為之，例如送子女至學校、托兒所，仍屬通勤職災範圍。",
        "law_basis": "勞工職業災害保險職業傷病審查準則 第17條第2款",
        "applied_to": ["A001 通勤事故"],
        "example": "勞工早上送女兒到幼兒園後繼續前往公司，途中追撞前車受傷 → 仍認定為通勤職災。",
    },
    {
        "topic": "通勤職災認定（脫逸範圍）",
        "key_question": "勞工於通勤途中為私人行為（用餐、購物、訪友）而發生事故，是否仍屬通勤職災？",
        "ruling": "若脫離日常居住處所往返就業場所之應經途中且非日常生活所必需，例如繞道訪友、長時間用餐後返家，則不認定為通勤職災。",
        "law_basis": "勞工職業災害保險職業傷病審查準則 第18條",
        "applied_to": ["A001 通勤事故"],
        "example": "勞工下班後與同事飲酒兩小時再返家，途中跌倒受傷 → 不屬通勤職災。",
    },
    {
        "topic": "重大職業災害通報範圍",
        "key_question": "什麼情況下雇主須於 8 小時內通報？",
        "ruling": "重大職業災害指：(1) 發生死亡災害；(2) 發生災害之罹災人數在 3 人以上；(3) 發生災害之罹災人數在 1 人以上，且需住院治療。雇主應於 8 小時內通報勞動檢查機構。",
        "law_basis": "職業安全衛生法 第37條第2項；同法施行細則第 47-48 條",
        "applied_to": ["A002 工地墜落", "A005 過勞"],
        "example": "勞工於工地墜落送醫，醫師診斷需住院手術 → 屬重大職災，雇主須於 8 小時內通報；違反者罰 3-30 萬元。",
    },
    {
        "topic": "過勞認定基準（腦心血管疾病）",
        "key_question": "什麼樣的工時與壓力會被認定為過勞職業病？",
        "ruling": "依「職業促發腦血管及心臟疾病（外傷導致者除外）之認定參考指引」：發病前 1 個月加班超過 100 小時、發病前 2-6 個月平均每月加班超過 80 小時、或工作負荷量、責任、不規則工時等綜合評估，可認定為職業病。",
        "law_basis": "勞動部 110 年訂頒「職業促發腦血管及心臟疾病認定參考指引」",
        "applied_to": ["A005 過勞"],
        "example": "工程師連續 6 個月平均每月加班 90 小時後突發心肌梗塞 → 符合過勞職業病認定基準，可申請職災給付；雇主出勤紀錄保存不全者違反勞基法§30。",
    },
    {
        "topic": "工資補償計算（原領工資）",
        "key_question": "勞基法§59 規定的「原領工資」如何計算？",
        "ruling": "原領工資指勞工遭遇職災前 1 日正常工作時間所得之工資；其為計月者，以遭遇職災前最近 1 個月工資除以 30 所得之金額。雇主應按其原領工資數額予以補償，至醫療終止止。",
        "law_basis": "勞動基準法施行細則 第31條",
        "applied_to": ["A001-A005 全部"],
        "example": "月薪 60,000 元勞工受傷住院 30 天 → 原領工資 60000/30 = 2000 元/日；補償 2000×30 = 60,000 元。",
    },
    {
        "topic": "派遣勞工職災連帶補償責任",
        "key_question": "派遣勞工發生職災，要派單位是否須與派遣事業單位連帶負責？",
        "ruling": "派遣事業單位與要派單位對派遣勞工之職業災害補償應連帶負職業災害補償責任。要派單位給付者，得向派遣事業單位求償。",
        "law_basis": "勞動基準法 第63-1條",
        "applied_to": ["A001-A005 派遣勞工"],
        "example": "派遣公司A派員工至工廠B擔任作業員，員工於B廠搬運受傷 → A、B 連帶負勞基法§59 補償責任。",
    },
    {
        "topic": "雇主危害預防義務範圍",
        "key_question": "雇主提供必要安全衛生設備之具體範圍？",
        "ruling": "雇主應對防止墜落、感電、機械夾捲、危害物質暴露等情形採取必要之安全衛生設施。違反者，致發生職災可處 1 年以下有期徒刑或併科 18 萬元以下罰金。",
        "law_basis": "職業安全衛生法 第6條、第40條；職業安全衛生設施規則",
        "applied_to": ["A002 工地墜落", "A004 化學品暴露"],
        "example": "工地未架設安全網，勞工自 3 公尺高處墜落致死 → 雇主違反職安法§6，可能面臨刑責 + 重大職災通報 + 補償責任三重後果。",
    },
    {
        "topic": "失能等級認定",
        "key_question": "失能給付的等級如何判定？",
        "ruling": "失能給付依「勞工職業災害保險失能給付標準」分為 15 等級 220 項，由勞保局指定醫院之專科醫師開立失能診斷書。第 1 等級給付 1,800 日，第 15 等級給付 30 日。",
        "law_basis": "勞工職業災害保險及保護法 第43條；勞工職業災害保險失能給付標準",
        "applied_to": ["A001-A005 全部（致失能者）"],
        "example": "勞工因職災致一目失明（第 7 等級）→ 給付日數 540 日，按平均月投保薪資除以 30 計算。",
    },
    {
        "topic": "退保後罹患職業病之給付",
        "key_question": "勞工退保後才被診斷出職業病，是否可請領給付？",
        "ruling": "被保險人於職業災害保險效力停止後 1 年內，經診斷罹患職業病者，得請領職業病醫療補助、失能津貼或死亡津貼。",
        "law_basis": "勞工職業災害保險及保護法 第78條",
        "applied_to": ["A004 化學品暴露", "A005 過勞"],
        "example": "勞工離職半年後被診斷罹患因前公司化學品暴露導致之職業性皮膚病 → 仍可請領職業病給付。",
    },
    {
        "topic": "職災勞工原領工資補償免列入投保薪資",
        "key_question": "職災期間支付的工資補償是否需列入勞保投保薪資申報？",
        "ruling": "勞工因職業災害不能工作，雇主依勞基法§59 給付之原領工資補償，不列入投保薪資申報；惟雇主仍應為職災勞工繼續加保至醫療終止止。",
        "law_basis": "勞工保險條例 第14條；勞動部 100 年函釋",
        "applied_to": ["A001-A005 全部"],
        "example": "勞工受傷住院 6 個月，雇主每月給付 50,000 元工資補償，但仍以原投保薪資 50,000 元繼續加保。",
    },
    {
        "topic": "勞資爭議調解程序",
        "key_function": "職災補償爭議的法定處理途徑為何？",
        "ruling": "勞資雙方就職災補償有爭議時，可向地方主管機關申請調解，由調解委員或調解人主持。調解不成立可進入仲裁或司法訴訟程序。雇主違反勞基法§59 補償義務者，主管機關得開罰 2 萬至 100 萬元。",
        "law_basis": "勞資爭議處理法 第9-25條；勞動基準法 第79條",
        "applied_to": ["A001-A005 全部"],
        "example": "雇主拒絕給付醫療補償 → 勞工可向公司所在地勞工局申請調解；調解不成立可向法院起訴並請求主管機關裁罰。",
    },
]


def build_interpretations():
    output = INTERP_DIR / "I_職災法規常見函釋摘要彙編.pdf"
    doc = SimpleDocTemplate(str(output), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph("職災法規常見函釋摘要彙編", title_style),
        Spacer(1, 0.3 * cm),
        Paragraph(esc("資料性質：教學參考；本彙編為公開法令、勞動部解釋令函公告、勞保局 FAQ 之主題式摘要，用於 RAG 系統訓練與展示。"), body_style),
        Paragraph(esc("資料來源：勞動部 laws.mol.gov.tw / 勞保局 bli.gov.tw / 職安署 osha.gov.tw / 全國法規資料庫 law.moj.gov.tw"), meta_style),
    ]
    for i, item in enumerate(INTERPRETATIONS, 1):
        story.append(PageBreak() if i > 1 and i % 3 == 1 else Spacer(1, 0.4 * cm))
        story.append(Paragraph(esc(f"{i}. {item['topic']}"), h2_style))
        story.append(Paragraph(esc(f"問題：{item.get('key_question') or item.get('key_function')}"), h3_style))
        story.append(Paragraph(esc(f"要旨：{item['ruling']}"), body_style))
        story.append(Paragraph(esc(f"法律依據：{item['law_basis']}"), body_style))
        story.append(Paragraph(esc(f"關聯事故：{', '.join(item['applied_to'])}"), body_style))
        story.append(Paragraph(esc(f"案例：{item['example']}"), body_style))
    doc.build(story)
    print(f"  ✓ {output}")


# ─── 案例摘要集 ────────────────────────────────

CASES = [
    {
        "category": "通勤事故",
        "accident_id": "A001",
        "cases": [
            {
                "title": "案例 1：上班途中遭追撞致腰椎受傷",
                "scenario": "張小姐 36 歲，於某公司擔任會計。某日上午 7:50 騎機車前往公司途中，遭酒駕汽車追撞，送醫診斷為腰椎第 3、4 節壓迫性骨折，需住院手術並請假休養 3 個月。",
                "ruling": "視為通勤職災（職業傷病審查準則§17）。雇主依勞基法§59 應給付醫療補償、原領工資補償；勞工得申請災保法傷病給付（第 4 日起按平均日投保薪資計算）。",
                "actions_employer": ["備齊診斷證明書、工資清冊", "按月給付原領工資至醫療終止", "通報職災保險局（非重大職災，無 8 小時通報義務）"],
                "actions_worker": ["備齊診斷證明書、職業傷病給付申請書、上下班事故陳述書", "5 年內向勞保局申請傷病給付", "可同步申請醫療給付"],
            },
            {
                "title": "案例 2：下班順道托兒所接送途中跌倒",
                "scenario": "李先生下班後騎機車前往幼兒園接小孩，途中遇雨路滑跌倒，左手腕骨折。",
                "ruling": "順道接送子女屬日常生活必需（職業傷病審查準則§17 第 2 款），仍認定為通勤職災。",
                "actions_employer": ["給付醫療補償、原領工資補償"],
                "actions_worker": ["備齊文件向勞保局申請傷病給付"],
            },
            {
                "title": "案例 3：下班繞道飲酒後返家途中事故（不予認定）",
                "scenario": "王先生下班後與同事飲酒 2 小時，深夜獨自騎車返家途中自摔受傷。",
                "ruling": "脫逸日常應經途中且非日常生活必需（審查準則§18），不認定為通勤職災。",
                "actions_employer": ["雇主無職災補償義務，但仍可申請普通傷病給付（非職災）"],
                "actions_worker": ["可申請勞保普通傷病給付（給付天數較少、起算日不同）"],
            },
        ],
    },
    {
        "category": "工地墜落",
        "accident_id": "A002",
        "cases": [
            {
                "title": "案例 1：未架設安全網之高處墜落致死",
                "scenario": "某營造廠承包大樓外牆作業，未架設安全網，工人陳先生於 5 樓鷹架施工時失足墜落送醫不治。",
                "ruling": "重大職業災害（死亡）。雇主違反職安法§6（未提供必要安全衛生設施）+ §37（重大職災 8 小時通報義務）。",
                "actions_employer": [
                    "8 小時內通報勞動檢查機構（勞動部職業安全衛生署所屬）",
                    "保留現場待調查",
                    "依勞基法§59 給付死亡補償（5 個月平均工資+40 個月喪葬費）",
                    "災保法死亡給付由勞保局核發予遺屬",
                    "可能面臨刑事追訴（職安法§40：1 年以下徒刑或併科 18 萬罰金）+ 行政罰鍰 3-30 萬",
                ],
                "actions_worker": [
                    "遺屬備齊死亡證明、戶籍資料、遺屬證明文件",
                    "5 年內向勞保局申請死亡給付（喪葬津貼 5 個月+遺屬年金/一次金）",
                    "另可向雇主請求民事賠償",
                ],
            },
            {
                "title": "案例 2：物件砸傷送醫住院",
                "scenario": "工地起重機吊掛之鋼樑滑落，砸中下方作業員李先生左肩，送醫診斷為左鎖骨骨折，住院 7 天。",
                "ruling": "屬重大職災（罹災 1 人以上需住院）。職安法§37 8 小時通報。",
                "actions_employer": ["8 小時內通報", "現場保留", "給付醫療與工資補償", "罰鍰 3-30 萬"],
                "actions_worker": ["申請災保傷病給付（5 年時效）"],
            },
            {
                "title": "案例 3：派遣作業員墜落（連帶責任）",
                "scenario": "派遣公司 A 派劉先生至營造商 B 工地，劉於 B 工地高處墜落骨折住院。",
                "ruling": "派遣事業單位 A 與要派單位 B 對職災補償連帶負責（勞基法§63-1）。重大職災通報義務由 B（要派、實際雇主）為之。",
                "actions_employer": ["A、B 雙方共同對劉先生負勞基法§59 補償責任", "B 為實際工作場所，須通報"],
                "actions_worker": ["可向 A 或 B 任一請求補償；申請災保給付不影響"],
            },
        ],
    },
    {
        "category": "搬運受傷",
        "accident_id": "A003",
        "cases": [
            {
                "title": "案例 1：物流司機搬運貨物腰椎拉傷",
                "scenario": "黃先生為物流司機，於配送途中獨自搬運 35 公斤貨物時腰部劇痛，送醫診斷為椎間盤突出，請假休養 6 週。",
                "ruling": "工作中發生之傷害屬職業傷害（職業傷病審查準則§3）。雇主依勞基法§59 給付補償。",
                "actions_employer": ["給付醫療補償與 6 週原領工資補償", "檢討單人搬運重物之安全衛生設施（職安法§6）"],
                "actions_worker": ["申請災保傷病給付", "嚴重者可申請失能給付"],
            },
            {
                "title": "案例 2：超商夜班店員搬箱滑倒",
                "scenario": "店員許小姐夜班搬箱時於濕滑地面跌倒，左膝韌帶撕裂。",
                "ruling": "職業傷害；雇主未告示防滑與適當清掃，可能違反職安法§6 與設施規則。",
                "actions_employer": ["給付補償；改善清潔流程與防滑設施", "若失能達等級可能延伸失能補償義務"],
                "actions_worker": ["醫療給付 + 傷病給付，視復原情形評估失能給付"],
            },
            {
                "title": "案例 3：派遣作業員協助搬運機台受傷",
                "scenario": "派遣勞工協助雇主廠房內搬運機台時，機台傾倒壓傷右腿。",
                "ruling": "派遣與要派連帶補償（勞基法§63-1）。",
                "actions_employer": ["雙方連帶負補償責任"],
                "actions_worker": ["申請災保傷病/失能給付"],
            },
        ],
    },
    {
        "category": "化學品暴露",
        "accident_id": "A004",
        "cases": [
            {
                "title": "案例 1：電鍍廠勞工長期接觸鎳鹽致皮膚炎",
                "scenario": "電鍍廠作業員張先生工作 4 年後皮膚出現嚴重接觸性皮膚炎，職業醫學科醫師認定為職業病。",
                "ruling": "屬災保法所定職業病。雇主未依職安法§20 實施特殊作業健康檢查，違反職安法。",
                "actions_employer": [
                    "給付醫療與工資補償（勞基法§59）",
                    "改善作業環境通風 + 個人防護具（職安法§6）",
                    "未實施特殊健檢罰 3-15 萬",
                ],
                "actions_worker": [
                    "備齊診斷證明、職業病職歷報告書",
                    "向勞保局申請職業病醫療給付與傷病給付",
                    "若退保 1 年內仍可申請（災保法§78）",
                ],
            },
            {
                "title": "案例 2：清潔工受混合化學品蒸氣中毒急診",
                "scenario": "清潔工誤將兩種清潔劑混合產生氯氣，吸入後咳嗽嘔吐送急診。",
                "ruling": "急性職業性中毒。雇主未提供 SDS（安全資料表）與危害告知，違反職安法§10。",
                "actions_employer": ["立即送醫並給付補償", "提供 SDS、加強危害告知教育訓練"],
                "actions_worker": ["申請災保醫療給付"],
            },
            {
                "title": "案例 3：噴漆工長期暴露於有機溶劑致肝功能異常",
                "scenario": "汽車噴漆工葉先生工作 8 年，定期健檢發現肝功能異常，職醫科認定為有機溶劑暴露導致。",
                "ruling": "職業病；雇主未實施作業環境監測與特殊健檢，違規。",
                "actions_employer": ["醫療補償 + 工時調整 + 環境監測", "罰鍰 3-15 萬"],
                "actions_worker": ["職業病給付 + 失能評估"],
            },
        ],
    },
    {
        "category": "過勞",
        "accident_id": "A005",
        "cases": [
            {
                "title": "案例 1：工程師連續 6 個月每月加班破百小時致心肌梗塞",
                "scenario": "韓先生為軟體公司工程師，連續 6 個月每月加班超過 100 小時，某日上班途中心肌梗塞猝死，年僅 38 歲。",
                "ruling": "符合「職業促發腦血管及心臟疾病認定參考指引」過負荷標準。屬職業病。屬重大職災（死亡），雇主應 8 小時內通報。",
                "actions_employer": [
                    "8 小時內通報",
                    "提供完整出勤紀錄（勞基法§30 應保存 5 年；未提供罰 2-100 萬）",
                    "依勞基法§59 給付死亡補償（5+40 個月薪資）",
                    "另可能違反勞基法§32 工時上限規定",
                ],
                "actions_worker": ["遺屬申請災保死亡給付（喪葬津貼 5 個月+遺屬年金）", "另可民事訴訟請求賠償"],
            },
            {
                "title": "案例 2：客運司機輪班過長致腦中風",
                "scenario": "客運司機馬先生因輪班過長且休假不足，某次出車前突發腦中風，住院 3 個月後失能（左半身偏癱）。",
                "ruling": "過勞職業病；達失能 5 等級。",
                "actions_employer": ["給付醫療、工資、失能補償；改善排班"],
                "actions_worker": ["失能給付 + 生活津貼"],
            },
            {
                "title": "案例 3：醫護人員夜班輪值致猝死（待認定）",
                "scenario": "醫院夜班護理師輪值後返家睡眠中猝死，家屬主張過勞。",
                "ruling": "依職業促發認定指引比對工時與壓力負荷；若符合即認定為職業病；勞動部得介入認定。",
                "actions_employer": ["8 小時內通報重大職災（死亡）", "提供出勤紀錄與輪班資料"],
                "actions_worker": ["遺屬申請職災死亡給付，必要時可向勞動部申請職業病鑑定"],
            },
        ],
    },
]


def build_cases():
    output = CASE_DIR / "C_職災典型案例摘要集.pdf"
    doc = SimpleDocTemplate(str(output), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph("職災典型案例摘要集", title_style),
        Spacer(1, 0.3 * cm),
        Paragraph(esc("資料性質：教學參考；以 5 類事故各 3 個典型情境，呈現雇主義務與勞工權益的對應關係。"), body_style),
        Paragraph(esc("資料來源：彙整自職業安全衛生署案例宣導、勞保局 FAQ、勞動部職業傷病審查準則。"), meta_style),
    ]
    for cat in CASES:
        story.append(PageBreak())
        story.append(Paragraph(esc(f"{cat['accident_id']} {cat['category']}"), title_style))
        for case in cat["cases"]:
            story.append(Paragraph(esc(case["title"]), h2_style))
            story.append(Paragraph(esc(f"情境：{case['scenario']}"), body_style))
            story.append(Paragraph(esc(f"認定要旨：{case['ruling']}"), body_style))
            story.append(Paragraph("人資端應採取行動：", h3_style))
            for a in case["actions_employer"]:
                story.append(Paragraph(esc(f"• {a}"), body_style))
            story.append(Paragraph("勞工端可主張權益：", h3_style))
            for a in case["actions_worker"]:
                story.append(Paragraph(esc(f"• {a}"), body_style))
            story.append(Spacer(1, 0.3 * cm))
    doc.build(story)
    print(f"  ✓ {output}")


if __name__ == "__main__":
    build_interpretations()
    build_cases()
