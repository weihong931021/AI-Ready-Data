# 競賽策略與 API 使用

> 從工作坊講義整理出的 API 用法 + 對標主辦方範例的得名分析。

---

## 一、EAP API 速查（決賽才需實作，初賽展示研究即可）

### 1.1 規格

- API 文件：`https://cloud.geminidata.com/api/docs/` （Swagger UI，給人看）
- API 原始定義：`https://cloud.geminidata.com/api/docs/openapi.json` （給 AI Vibe Coding 用）
- Base URL：`https://cloud.geminidata.com/api/v1`
- 規格版本：OpenAPI 3.0
- 認證：Token + Project ID
- 串流：支援 streaming（JSON chunk 格式）
- 內容：回應可含 Markdown + Mermaid（前端要能渲染）

### 1.2 核心 3 個 endpoint

| Method | Path | 用途 |
| --- | --- | --- |
| POST | `/api/v1/chat/create` | 建立聊天室，綁定專案 → 回傳 chat_id |
| POST | `/api/v1/chat/{chat_id}` | 送出問題，取得 AI 回應 + message_id |
| GET | `/api/v1/chat/{chat_id}/messages` | 讀取整個聊天歷史，畫到前端 |

加分功能：

| Method | Path | 用途 |
| --- | --- | --- |
| POST | `/api/v1/chat/{chat_id}/{message_id}/chartgen` | 為訊息生成圖表 |

> 工作坊講義第 1690-1730 行的核心觀念：**所有對話功能集中在 chat API；以 chat_id 作為所有操作的核心識別；一個 chat = 一段完整對話生命週期**。

### 1.3 取得 Project ID 與 Token

工作坊講義第 1750-1755 行提到「專案金鑰怎麼拿」。在平台介面：

1. 進入專案 → 右上角設定 / 鑰匙圖示
2. 複製 `Project ID` 與 `Token`
3. 暫不考慮安全性處理（直接寫進前端 demo 用）

### 1.4 Vibe Coding 串接 API 的 Prompt 範例

直接拿這段給 Cursor / Claude Code 等工具：

```text
請使用 EAP RAG AI Chat API 完成「職災法規助手」的對話功能。

需求：
- 使用 React + TypeScript（或你的框架）打造一個雙面介面 Web App
- 進入頁面先讓使用者選擇身分：人資 / 勞工
- 主畫面：左側對話框、右側即時呈現 GraphRAG 推理路徑（簡單的 Mermaid 流程圖）
- 系統需支援 streaming 回傳，並能正確解析 API 回傳內容（JSON chunk 格式）
- 回應內容可能包含 Markdown 與 Mermaid，請在前端正確渲染
- 每則回覆右上角提供「複製」按鈕
- 加分：人資端額外顯示「期限倒數計時器」；若 AI 回應提到 8 小時通報義務，則彈出倒數元件

API 串接資訊：
- API Web Link：https://cloud.geminidata.com/api/docs/
- API Base URL：https://cloud.geminidata.com/api/v1
- Project ID：<貼上你的 Project ID>
- Token：<貼上你的 Token>

流程：
1. 進入頁面時 POST /api/v1/chat/create 建立聊天室，存 chat_id 在 state
2. 使用者送出訊息 → POST /api/v1/chat/{chat_id}（含使用者身分前綴）
3. 顯示 streaming 回應
4. 切換身分時新建 chat（保留歷史在 sidebar）

請先生成 plan.md 規劃專案結構，再開始寫 code。
```

### 1.5 樣板程式碼

工作坊講義第 1740 行提示有 sample code，網址：[https://shorturl.at/0udxP](https://shorturl.at/0udxP)（平台操作補充簡報）。

實際 fetch 範例（你可以拿這個給 Vibe Coding 工具當起點）：

```typescript
const PROJECT_ID = "your_project_id";
const TOKEN = "your_token";
const BASE = "https://cloud.geminidata.com/api/v1";

// 1. 建聊天室
async function createChat() {
  const r = await fetch(`${BASE}/chat/create`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ project_id: PROJECT_ID }),
  });
  const data = await r.json();
  return data.chat_id;
}

// 2. 送問題（streaming）
async function askWithStreaming(chatId: string, question: string, onChunk: (s: string) => void) {
  const r = await fetch(`${BASE}/chat/${chatId}`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: question, stream: true }),
  });
  const reader = r.body!.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    // 解析 SSE / chunk 格式（依實際回傳格式調整）
    onChunk(text);
  }
}

// 3. 讀歷史
async function getMessages(chatId: string) {
  const r = await fetch(`${BASE}/chat/${chatId}/messages`, {
    headers: { "Authorization": `Bearer ${TOKEN}` },
  });
  return r.json();
}
```

### 1.6 初賽 vs 決賽的 API 要求

| 階段 | API 要求 |
| --- | --- |
| **初賽（5/10）** | 不需實作 API。**展示研究過 API 文件 + Vibe Coding prompt 設計**即可加分 |
| **決賽（6/26）** | **必須實作 API 串接 + 完整介面 demo**（從 [2026 初賽提案簡報範例.pdf](2026%20初賽提案簡報範例.pdf) 第 30 行明示） |

→ 初賽提案 PPT 建議放一頁「**API 串接規劃**」展示已研究文件 + 截一張 Swagger UI 圖即可。

---

## 二、得名分析

### 2.1 對標主辦方範例

從 [2026 初賽提案簡報範例.pdf](2026%20初賽提案簡報範例.pdf) 看，主辦方示範題目是「**颱風百問智慧小幫手**」。它的特色：

| 主辦範例特色 | 我們的對應 |
| --- | --- |
| 4 種受眾（政府、企業、民眾、學術） | 我們 2 種（人資 + 勞工/工會），但**雙面介面 = 整合創新** |
| 結構化（颱風列表）+ 非結構化（颱風百問） | 我們 7 節點 + 5 關係 + 13 PDF |
| 風險評估（類似颱風路徑比對） | 我們罰則風險、過勞認定（**金錢風險可量化**，比颱風更具體） |
| 客製化 prompt（自稱「精誠家阿呆」） | 我們 Robot Setting 已寫，可加角色化 |

### 2.2 去年第一名 [12_關公都點頭] 的關鍵成功因素

從去年得獎簡報看：

1. **強記憶點命名**：RAGTIRE = RAG + Retire + Tired（退休不疲累）
2. **量化痛點**：「7 年 23 家銀行 35 張罰單，總罰金 2.51 億元」
3. **量化效益**：「135 效益：1 整合平台、3 投資組合、5 分鐘規劃」
4. **完整商業模式九宮格**
5. **B2B2C 商模設計**

→ 我們也要做這 5 點。

### 2.3 我們的得名機會與風險

#### ✅ 強項（高度有機會得獎）

1. **整合創新評分項拉滿**
   - 雙面介面（人資 vs 勞工）+ 共用知識庫
   - 主辦方範例與去年得獎都沒有這種設計
   - 評分項佔比約 10-30%，這裡能拿滿分

2. **痛點具體可量化**
   - 違規罰鍰最高 100 萬（勞基法§79）
   - 死亡補償 45 個月薪資 = 數百萬
   - 律師諮詢費一次 3-5 萬
   - 月訂閱制 1,000-5,000 元 → ROI 清楚

3. **政策時機點對**
   - 2022 年災保法上路後，企業合規負擔加重
   - 中小企業苦於沒有專責法務 → 真實市場需求

4. **資料公開且權威**
   - 全國法規資料庫官方 PDF
   - 勞保局官方給付指南
   - 函釋與案例都有公開出處

5. **技術深度可展現**
   - VectorRAG 處理白話事故描述（情緒化、口語）
   - GraphRAG 處理多重法規 + 義務 + 期限的推理
   - 兩者**缺一不可**才能完整回答 → 證明 Hybrid RAG 的必要性

#### ⚠️ 風險（要注意的弱項）

1. **資料量比去年得獎少**
   - 去年第一名：400 條金融法規 + 200 條退休法規 + 4000 筆基金資料
   - 我們：10 部法 + 12 個 CSV + 30 多個案例
   - **緩解**：強調「主題聚焦」而非「資料堆量」；質感大於數量

2. **法律專業度**
   - 評審若有法律背景，會看到 12 個函釋摘要不夠細
   - **緩解**：明確標註資料來源，並準備 1-2 個亮點 case 講透

3. **介面設計**
   - 主辦方在範例中強調「介面設計初步構想」也佔分
   - **緩解**：用 Vibe Coding 至少做出 2 頁靜態 demo（身分選擇 + 對話畫面）放截圖

4. **B2B 商模驗證**
   - 評審可能問「中小企業真的會付錢嗎？」
   - **緩解**：引用 1-2 個實際勞檢罰款案例（職安署違規裁罰公布專區有公開資料），證明痛點真實

### 2.4 得名機率評估

> 個人判斷，僅供參考。

| 名次 | 機率 | 條件 |
| --- | --- | --- |
| **入圍決賽** | **70%** | 只要把資料上傳、跑出 5 個案例、PPT 結構完整就會有 |
| **佳作** | 50% | 提案結構完整 + 雙面介面 demo 順暢 |
| **第三名** | 30% | 雙面介面 + 強記憶點命名 + 真實商模舉證 |
| **第二名** | 15% | 上述 + Demo 衝擊力（8 小時倒數、罰則金額視覺化）+ 法律深度 |
| **第一名** | 5-10% | 上述 + 強烈差異化（主辦方範例沒有的角度）+ 完美執行 |

### 2.5 進入前 3 名的關鍵動作

**Day 1-3（5/4-5/6）：把資料跑出來**
- 完成 EAP 平台所有上傳與設定
- 跑通 5 個案例的 QA
- 截圖 6-8 張關鍵畫面

**Day 4（5/7）：強化記憶點**
- 想一個有 punch 的題目命名（例：**JobShield 職盾**、**JADE 職災一站通** 等）
- 列出 3 個量化痛點數字（罰金、補償金額、時效失權人數）
- 設計「135 效益」式的 slogan

**Day 5（5/8）：介面 prototype**
- 用 Figma 或 Vibe Coding 產 2 頁靜態 mockup
- 至少要有「身分選擇頁」與「對話 + 推理路徑」頁

**Day 6（5/9）：寫 PPT**
- 套用 [2026 初賽提案簡報範例.pdf](2026%20初賽提案簡報範例.pdf) 結構
- 15 頁分配：1 頁封面、2 頁痛點、3 頁價值、5 頁技術、3 頁 Demo、1 頁團隊

**Day 7（5/10）：檢查與提交**
- 檔名格式：`隊伍序號_隊伍名稱_提案標題.pptx`
- 仔細檢查每張 EAP 截圖清晰度

### 2.6 PPT 15 頁結構建議

| 頁 | 內容 | 對應評分 |
| --- | --- | --- |
| 1 | 封面（隊名 + slogan + logo） | — |
| 2 | 痛點：3 個量化數字 + 雙受眾困境 | 25% 痛點 |
| 3 | 解決方案：雙面介面架構圖 | 25% 痛點 |
| 4 | 為何 Hybrid RAG 缺一不可 | 30% 技術 |
| 5 | 資料來源（公開、權威，13 PDF + 12 CSV） | 30% 技術 |
| 6 | 知識圖譜建模（節點/關係/Unique Key） | 30% 技術 |
| 7 | 技術架構圖（情境 → API → 語意網 → 資料來源） | 30% 技術 |
| 8 | Context Engineering（Robot Setting 全文） | 30% 技術 |
| 9 | Prompt Design（3 類問題分類 + 範例） | 30% 技術 |
| 10 | Demo 截圖 1：通勤事故 人資端 | 20% 實作 |
| 11 | Demo 截圖 2：通勤事故 勞工端（同事故對比） | 20% 實作 |
| 12 | Demo 截圖 3：工地墜落 8 小時倒數 | 20% 實作 |
| 13 | 介面初步構想（Figma mockup 截圖） | 10% 介面 |
| 14 | 商業價值與目標客戶（中小企業 + 工會 + 律所） | 10% 商業 |
| 15 | 團隊 + 後續開發路徑 | — |

---

## 三、若得名後的決賽強化方向（6/26）

| 強化項目 | 建議 |
| --- | --- |
| 資料量 | 補完 22 縣市勞工局調解程序、加入 100+ 真實 函釋 |
| 介面實作 | Vibe Coding 完成可互動 Web App，串 API |
| 商業驗證 | 找 1-2 家中小企業人資訪談，加入「使用者證言」頁 |
| 技術亮點 | 加入「期限倒數定時通知」（API + 推播） |
| AI Agent | 讓 AI 主動詢問追問問題（多輪對話） |
| 商模驗證 | 列出 3-5 家潛在客戶名單與訪談紀錄 |

---

## 四、最後提醒

去年第一名的 slogan「**用 RAGTIRE，讓你退休不 TIRED**」用了 5 次在簡報中（每頁頁腳）。這種**重複曝光記憶點**的技巧值得學習。

我們可以類似做：
- **「JobShield 職盾，讓職災風險看得見、罰則躲得開、權益拿得回」**
- 或更簡短：**「一個事故，兩種視角，秒懂法律」**

每張投影片頁腳放這句話，評審看完 15 頁就記住你了。
