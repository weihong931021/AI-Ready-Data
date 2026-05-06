# Claude 記憶 — 2026 精誠 AI 競賽（第二題）v4

> 最後更新：2026-05-07

## 專案一句話

參加 **2026 精誠資訊 AI 創新競賽**（AI Ready Data — 打造理解關聯的智慧大腦），用 EAP / Gemini Data 平台的 Hybrid RAG（Vector + Graph）+ Vibe Coding，做一個**資訊服務業勞動法規合規風險助手**，聚焦 IT 行業 HR 與 PM 的三大實務痛點。

## 關鍵時程

| 日期 | 事件 |
| --- | --- |
| 2026-04-25 | 工作坊（已過）|
| **2026-05-08** | **EAP 資料上傳截止** ← 明天 |
| **2026-05-10** | **初賽提案 PPT 提交（15 頁上限）** |
| 2026-05-15 | 決賽入圍公告 |
| 2026-05-26 ~ 06-18 | 顧問諮詢（每週二、四 13:30–17:30）|
| 2026-06-21 | 決賽簡報繳交截止 |
| 2026-06-26 | 決賽當日（精誠內湖總部）|

## 題目方向（已鎖定 v4）

**資訊服務業勞動合規風險助手**，三情境架構：

| 情境 | 名稱 | 核心問題 | 圖譜支援 |
| --- | --- | --- | --- |
| A | 應急導航：職災處置 | 事故發生後 HR 如何完成法定 SOP | ★★★★★ 完整 |
| B | 精準止損：資遣爭議 | 資遣解僱流程如何合規、如何舉證 | ★★★ 基本完整 |
| C | 法規風險雷達：產業合規評估 | 輸入公司基本資訊，AI 評估同業違規風險 | ★★★★ 完整 |

**定位原則**（顧問確認）：AI 是公司的「法律防彈衣」，不是放大公司問題的工具。展示同業被罰紀錄，讓公司主動對標，而非被指控。

## 平台關鍵限制（EAP / Gemini Data）

- 平台網址：`https://cloud.geminidata.com`（**只支援 Chrome**）
- 上傳格式：
  - **VectorRAG（Documents）**：PDF（32 份已備妥）
  - **GraphRAG（Data Importer）**：**CSV**
- CSV 規範（嚴格）：
  - 第一列必為欄位名
  - **禁止合併儲存格**
  - 一格一個值，**禁止陣列**（多對多關係要拆關係表）
  - 日期 `YYYY-MM-DD`，數值欄位純數字
- 節點識別：**Category（標籤）+ Unique Key**
  - 同 Category + 同 Unique Key 自動合併
  - 不同 Category 不會合併（即使 Unique Key 同）
- Data Flow = Source + Model + 按 Start
- 編輯後務必 **清空畫布 + 全部 Data Flow 重跑**
- 畫布顯示異常 → 登出再登入

## API（Vibe Coding 用）

- 文件：`https://cloud.geminidata.com/api/docs/`
- 核心三 endpoint：
  1. `POST /api/v1/chat/create` 建聊天室
  2. `POST /api/v1/chat/{chat_id}` 送問題
  3. `GET /api/v1/chat/{chat_id}/messages` 讀歷史
- 一個 chat = 一段完整對話生命週期
- Cypher 語法：**Neo4j v5**，禁用 `OVER()`

## 初賽提案結構

15 頁 PPT，檔名 `隊伍序號_隊伍名稱_提案標題`，必含：

1. **痛點 problem statement** — IT 行業 HR 三大痛點
2. **應用情境與商業價值** — 三情境 × B2B 防守定位
3. **技術應用規劃**：
   - 資料來源（含 URL）：mol.gov.tw、osha.gov.tw、law.moj.gov.tw
   - 資料處理流程（含 scrape scripts）
   - 圖譜模型：17 節點類型 / 24 關係 / 766 節點 / 2,410 邊
   - 技術架構圖：情境 → API → Hybrid RAG → 資料來源
   - Context Engineering（系統提示詞）
   - Prompt Design（三情境 QA 分類）
4. **實作成果 DEMO** ← **必須有 EAP 平台真實 QA 截圖（7 題）**
5. **介面設計初步構想**

評分權重推測：25% 痛點 / 30% 技術 / 20% 實作 / 10% 介面 / 10% 商業

## 圖譜現況（v4 最終狀態）

- **節點**：766 個（17 種類型）
- **邊**：2,410 條（24 種關係 R1–R24）
- **懸空邊**：0
- **孤立節點**：0
- **事故類型**：6 種（A001–A005 職災 + A006 資遣爭議）
- **法規條文**：39 條（L001–L039）
- **工作情境**：8 種（S001–S007 IT 職安 + S008 資遣）
- **裁罰案例（圖內）**：603 筆（OSHA 475 + LBR 精選 128）
- **裁罰原始資料**：58,496 筆（LBR 32,111 + 其他三來源）

## 主要資料來源

| 來源 | 用途 | 取得方式 |
| --- | --- | --- |
| 全國法規資料庫 law.moj.gov.tw | 22 份法規 PDF | 手動下載 |
| 勞保局 bli.gov.tw | 給付指南 PDF | 手動下載 |
| 勞動部 mol.gov.tw | 裁罰 CSV（LBR 32,111 筆）| scrape_lbr_history.py |
| 職安署 osha.gov.tw | OSHA 違規案例 | scrape_osha_cases.py |
| 勞動部函釋查詢 laws.mol.gov.tw | 函釋彙編 | scrape_mol_interpretations.py |

## 資料夾結構

```
資料/
  1_原始下載/       原始爬蟲與下載產物
    裁罰_原始/      D_勞基法違規案例.csv（32,111 筆）等
  2_自製整理/       函釋彙編 + 案例彙編 PDF
  3_EAP上傳/        ← 上傳到 EAP 的最終版本
    PDF/            32 份 VectorRAG 文件
    CSV/
      節點/         17 個節點 CSV
      關係/         24 個關係 CSV
      裁罰原始_給EAP/ D_全部裁罰案例_清理版.csv（58,496 筆）
      補丁_patch/   Codex 補丁存檔（已套用，可刪）
資料_舊版備份/      舊版資料備份
scripts/            5 個爬蟲 + 整合腳本
```

## 分工切點

| Claude 已完成 | 團隊待操作 |
| --- | --- |
| 全部 17 個節點 CSV | 上傳 PDF 到 EAP |
| 全部 24 個關係 CSV | 建 17 個節點 Data Flow |
| LBR 擴充至 32,111 筆 | 建 24 個關係 Data Flow |
| 0 孤立節點、0 懸空邊 | 視覺化驗證（Explore）|
| Robot Setting 提示詞草稿 | 設定 Robot Setting |
| 7 題 Demo Query 腳本 | 跑 QA 截圖 |
| 實作流程 v4 完整步驟 | 提案 PPT 製作 |

## 專案內檔案

### 主要文件（v4 最新）

- [資料總覽_v4.md](資料總覽_v4.md) — 節點/關係/PDF 完整清單與統計
- [實作流程.md](實作流程.md) — EAP 上傳步驟、節點/關係設定對照表
- [CLAUDE.md](CLAUDE.md) — 本檔（專案記憶）
- [README.md](README.md) — 專案入口

### 參考 PDF（主辦方提供）

- [12_關公都點頭(決賽第一名).pdf](12_關公都點頭(決賽第一名).pdf)
- [2026 AI Ready Data工作坊簡報(講義).pdf](2026%20AI%20Ready%20Data工作坊簡報(講義).pdf)
- [2026 初賽提案簡報範例.pdf](2026%20初賽提案簡報範例.pdf)

## 關鍵風險

- **5/8 截止，今天必須開始上傳** → 實作流程.md 有完整步驟
- **5/10 PPT 必須有 EAP QA 截圖** → 至少跑 7 題 Demo Query
- xlsx/CSV 合併儲存格 / 陣列值 → 全部已拆成關係表，應無問題
- 編輯 Data Flow 後沒清空畫布 → 務必清空重跑
