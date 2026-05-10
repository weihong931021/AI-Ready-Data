const BLUE = "#0B63F6";
const INK = "#111827";
const MUTED = "#5B6472";
const PALE = "#EEF4FF";
const PALE2 = "#F7FAFF";
const LINE = "#D8E0EF";
const REDPALE = "#FFE7E2";
const GREEN = "#2F7D46";

const ASSET = "/Users/weihong/Documents/AI-Ready-Data/簡報要用圖片";
const PDF_PREVIEW = "/private/tmp/ai-ready-pdf-pages";

function bg(slide, ctx) {
  ctx.addShape(slide, { x: 0, y: 0, w: 1280, h: 720, fill: "#FFFFFF" });
  ctx.addShape(slide, { x: 0, y: 0, w: 1280, h: 6, fill: BLUE });
}

function title(slide, ctx, text, sub = "") {
  ctx.addText(slide, { x: 70, y: 54, w: 900, h: 56, text, fontSize: 37, bold: true, color: INK, typeface: ctx.fonts.title });
  if (sub) ctx.addText(slide, { x: 72, y: 112, w: 1060, h: 32, text: sub, fontSize: 17, color: BLUE, bold: true });
}

function foot(slide, ctx, n) {
  ctx.addText(slide, { x: 1130, y: 674, w: 80, h: 22, text: String(n).padStart(2, "0"), fontSize: 13, color: "#A6B1C2", align: "right" });
}

function card(slide, ctx, x, y, w, h, opts = {}) {
  ctx.addShape(slide, {
    x, y, w, h,
    fill: opts.fill || PALE2,
    line: { style: "solid", fill: opts.line || LINE, width: opts.lineWidth ?? 1 },
  });
}

function metric(slide, ctx, x, y, value, label, color = BLUE) {
  ctx.addText(slide, { x, y, w: 150, h: 38, text: value, fontSize: 29, bold: true, color, align: "center" });
  ctx.addText(slide, { x, y: y + 36, w: 150, h: 34, text: label, fontSize: 12, color: MUTED, align: "center" });
}

function bullets(slide, ctx, x, y, w, items, opts = {}) {
  const fs = opts.fontSize || 17;
  const lh = opts.lineHeight || 32;
  items.forEach((item, i) => {
    const yy = y + i * lh;
    ctx.addText(slide, { x, y: yy, w: 18, h: 24, text: "•", fontSize: fs, color: opts.bulletColor || BLUE, bold: true });
    ctx.addText(slide, { x: x + 24, y: yy, w: w - 24, h: lh + 8, text: item, fontSize: fs, color: opts.color || INK });
  });
}

function smallTable(slide, ctx, x, y, widths, rowH, rows, opts = {}) {
  const headerFill = opts.headerFill || "#E8F0FF";
  const border = opts.border || LINE;
  rows.forEach((row, r) => {
    let cx = x;
    widths.forEach((w, c) => {
      card(slide, ctx, cx, y + r * rowH, w, rowH, { fill: r === 0 ? headerFill : "#FFFFFF", line: border });
      ctx.addText(slide, {
        x: cx + 8,
        y: y + r * rowH + 8,
        w: w - 16,
        h: rowH - 12,
        text: row[c] || "",
        fontSize: r === 0 ? (opts.headerSize || 14) : (opts.bodySize || 13),
        bold: r === 0 || (row[c] || "").includes("合計"),
        color: r === 0 ? INK : (opts.bodyColor || INK),
      });
      cx += w;
    });
  });
}

function threeScenarioCard(slide, ctx, x, y, titleText, lines, iconLabel) {
  card(slide, ctx, x, y, 345, 315, { fill: PALE });
  ctx.addShape(slide, { x: x + 28, y: y + 26, w: 42, h: 42, fill: BLUE });
  ctx.addText(slide, { x: x + 29, y: y + 35, w: 40, h: 25, text: iconLabel, fontSize: 16, color: "#FFFFFF", bold: true, align: "center" });
  ctx.addText(slide, { x: x + 86, y: y + 27, w: 235, h: 38, text: titleText, fontSize: 24, bold: true, color: INK });
  bullets(slide, ctx, x + 32, y + 88, 285, lines, { fontSize: 17, lineHeight: 42, bulletColor: GREEN });
}

async function cover(slide, ctx) {
  await ctx.addImage(slide, { path: `${PDF_PREVIEW}/page-01.png`, x: 0, y: 0, w: 1280, h: 720, fit: "cover", alt: "Canva-style cover reference" });
  ctx.addShape(slide, { x: 0, y: 0, w: 1280, h: 720, fill: "#00000014" });
  ctx.addShape(slide, { x: 86, y: 436, w: 4, h: 40, fill: "#FF4D3D" });
  ctx.addText(slide, { x: 108, y: 438, w: 710, h: 34, text: "Hybrid RAG 驅動的職災與法遵風險作戰室", fontSize: 21, color: "#FFFFFF" });
}

function slidePain(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "痛點與量化佐證", "風險已經發生在 HR、PM、管理層日常裡");
  const xs = [70, 465, 860];
  const heads = ["HR 人資", "PM 專案主管", "公司管理層"];
  const pains = ["職災發生不知道 8 小時內要做什麼，資遣程序不確定是否合規", "客戶端事故責任不清，專案趕工加班紀錄不足", "不知道同業被罰什麼，勞檢來了措手不及"];
  const facts = [["3–30 萬", "漏報重大職災罰鍰"], ["1,883 件", "違反加班費給付裁罰"], ["1,114 家次", "北市單年度開罰"]];
  xs.forEach((x, i) => {
    ctx.addText(slide, { x, y: 165, w: 325, h: 36, text: heads[i], fontSize: 24, bold: true, color: INK });
    ctx.addShape(slide, { x, y: 210, w: 325, h: 2, fill: "#111827" });
    card(slide, ctx, x, 236, 325, 96, { fill: "#FFFFFF" });
    ctx.addText(slide, { x: x + 22, y: 257, w: 280, h: 58, text: `痛點：\n${pains[i]}`, fontSize: 15, color: INK });
    card(slide, ctx, x, 360, 325, 212, { fill: REDPALE, line: "#FFE7E2" });
    metric(slide, ctx, x + 88, 392, facts[i][0], facts[i][1], "#C74432");
  });
  bullets(slide, ctx, 95, 606, 1070, ["HR：每年 6,000+ 件資遣費勞資爭議", "PM：加班費裁罰總額 6,200 萬，出勤紀錄最高罰 100 萬", "管理層：北市單年度總罰鍰 7,545 萬"], { fontSize: 14, lineHeight: 24 });
  ctx.addText(slide, { x: 72, y: 666, w: 850, h: 24, text: "AI 是公司的「合規煙霧偵測器」", fontSize: 18, color: BLUE, bold: true });
  foot(slide, ctx, n);
}

function slideSolution(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "解決方案：一個知識庫，兩種決策視角", "同一事故，依身份輸出企業義務或勞工權益");
  card(slide, ctx, 74, 165, 330, 390, { fill: "#F7FAFF" });
  card(slide, ctx, 476, 165, 330, 390, { fill: "#EEF4FF", line: "#9BB8FF" });
  card(slide, ctx, 878, 165, 330, 390, { fill: "#F7FAFF" });
  ctx.addText(slide, { x: 108, y: 192, w: 260, h: 34, text: "企業端", fontSize: 28, bold: true, color: INK, align: "center" });
  ctx.addText(slide, { x: 510, y: 202, w: 260, h: 64, text: "Hybrid RAG\n共用知識庫", fontSize: 29, bold: true, color: BLUE, align: "center" });
  ctx.addText(slide, { x: 912, y: 192, w: 260, h: 34, text: "勞工端", fontSize: 28, bold: true, color: INK, align: "center" });
  bullets(slide, ctx, 110, 260, 250, ["公司現在該做什麼", "誰負責、少做會怎樣", "需要哪些文件", "刑責 / 罰鍰 / 民事賠償"], { fontSize: 18, lineHeight: 46 });
  bullets(slide, ctx, 512, 305, 260, ["VectorRAG 查法規原文", "GraphRAG 展開推理鏈", "裁罰層支撐同業對標"], { fontSize: 18, lineHeight: 48, bulletColor: GREEN });
  bullets(slide, ctx, 914, 260, 250, ["我能申請什麼", "要準備什麼文件", "申請期限與受理單位", "申訴或調解路徑"], { fontSize: 18, lineHeight: 46 });
  ctx.addText(slide, { x: 165, y: 600, w: 950, h: 40, text: "法律顧問是救火隊，小勞鼠是合規煙霧偵測器", fontSize: 27, bold: true, color: BLUE, align: "center" });
  foot(slide, ctx, n);
}

function slideScenarios(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "應用與使用情境", "三個高頻決策入口，對應 IT 公司真實工作場景");
  threeScenarioCard(slide, ctx, 70, 168, "應急導航", ["職災、客戶現場、IDC、通勤公出、不法侵害", "使用者：HR / PM / EHS", "輸出：事故判定、SOP、文件、罰則、刑責"], "A");
  threeScenarioCard(slide, ctx, 468, 168, "精準止損", ["資遣 / 解僱前", "使用者：HR / Legal", "輸出：程序、期限、舉證、調解風險"], "B");
  threeScenarioCard(slide, ctx, 866, 168, "法規風險雷達", ["勞檢前 / 年度內控", "使用者：管理層 / HR", "輸出：同業裁罰、法條熱點、改善建議"], "C");
  ctx.addShape(slide, { x: 170, y: 562, w: 940, h: 86, fill: "#DDF2FF", line: { style: "solid", fill: "#DDF2FF", width: 0 } });
  ctx.addText(slide, { x: 210, y: 582, w: 860, h: 52, text: "事故發生時，每小時都是罰款計時器；資遣不合規，調解輸了是天價；同業被罰什麼，就是你的下一個風險。", fontSize: 20, bold: true, color: GREEN, align: "center" });
  foot(slide, ctx, n);
}

function slideLLM(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "傳統 LLM vs 小勞鼠", "回應評審會問的問題：現在 LLM 這麼強，你們好在哪？");
  const rows = [
    ["比較項目", "一般 LLM", "小勞鼠 Hybrid RAG"],
    ["資料來源", "可能憑模型記憶", "官方 PDF + 裁罰 CSV + GraphRAG"],
    ["推理方式", "文字回答為主", "事故 → 法規 → 義務 → 文件 → 罰則"],
    ["可追溯性", "難確認依據", "可回到節點、法條、裁罰案例"],
    ["產業性", "泛用", "專注資訊服務業"],
    ["輸出", "一般建議", "可執行 SOP / 風險清單"],
  ];
  smallTable(slide, ctx, 110, 176, [190, 360, 500], 70, rows, { bodySize: 18, headerSize: 18 });
  ctx.addText(slide, { x: 150, y: 625, w: 980, h: 34, text: "核心差異：不是只答得出來，而是能把法條、義務、文件、罰則、刑責串成決策鏈。", fontSize: 20, bold: true, color: BLUE, align: "center" });
  foot(slide, ctx, n);
}

async function slideArchitecture(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "技術架構", "直接使用專案既有架構圖，不重新生成流程圖");
  await ctx.addImage(slide, { path: `${ASSET}/ai-ready-data-archetecture.png`, x: 125, y: 122, w: 1030, h: 475, fit: "contain", alt: "AI Ready Data architecture" });
  [
    ["VectorRAG", "PDF 法規 / 指引 / 案例原文"],
    ["GraphRAG", "義務 / 權益 / 文件 / 罰則 / 刑責"],
    ["Robot Setting", "控制三情境回答格式"],
    ["Risk Layer", "裁罰資料支撐同業對標"],
  ].forEach((d, i) => {
    const x = 115 + i * 282;
    card(slide, ctx, x, 620, 245, 54, { fill: "#F7FAFF" });
    ctx.addText(slide, { x: x + 16, y: 628, w: 210, h: 18, text: d[0], fontSize: 15, bold: true, color: BLUE, align: "center" });
    ctx.addText(slide, { x: x + 14, y: 649, w: 214, h: 16, text: d[1], fontSize: 10.5, color: MUTED, align: "center" });
  });
  foot(slide, ctx, n);
}

function slideStructuredCollect(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "結構化資料一：資料收集與處理", "GraphRAG 把法規知識變成可遍歷的推理鏈");
  const rows = [
    ["資料來源", "取得方式", "筆數", "用途"],
    ["LBR 勞動部裁罰公告", "Python 爬蟲", "32,111", "工資、工時、資遣裁罰"],
    ["OSHA 職安署案例", "Python 爬蟲", "475", "職安案例"],
    ["勞退條例裁罰", "Open Data CSV", "9,427", "勞退義務"],
    ["災保法裁罰", "Open Data CSV", "16,483", "災保行政義務"],
    ["合併清理版", "自動化腳本", "58,496", "風險雷達與同業對標"],
  ];
  smallTable(slide, ctx, 70, 190, [230, 170, 120, 250], 60, rows, { bodySize: 14 });
  ctx.addText(slide, { x: 900, y: 190, w: 250, h: 36, text: "處理流程", fontSize: 24, bold: true, color: INK, align: "center" });
  ["多源採集", "格式標準化", "關鍵字分類", "精選 603 筆案例入圖", "匯入 GraphRAG"].forEach((t, i) => {
    card(slide, ctx, 895, 250 + i * 68, 270, 46, { fill: i % 2 ? "#FFFFFF" : PALE });
    ctx.addText(slide, { x: 915, y: 262 + i * 68, w: 230, h: 24, text: `${i + 1}. ${t}`, fontSize: 17, bold: true, color: i === 4 ? GREEN : INK });
  });
  foot(slide, ctx, n);
}

function slideStructuredGraph(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "結構化資料二：知識圖譜建模", "766 節點、2,410 邊、0 懸空邊");
  smallTable(slide, ctx, 90, 160, [210, 110], 58, [
    ["節點類型", "數量"], ["事故類型", "6"], ["法規條文", "39"], ["企業義務", "11"], ["勞工權益", "9"], ["裁罰案例", "603"], ["工作情境", "8"], ["其他 11 種", "90"], ["合計", "766"],
  ], { bodySize: 15 });
  smallTable(slide, ctx, 455, 160, [230, 140, 100, 250], 58, [
    ["關係群", "關係", "邊數", "功能"],
    ["核心義務 / 權益鏈", "R1–R5", "206", "事故→法規→義務/權益→文件"],
    ["裁罰案例鏈", "R6–R8", "1,914", "產業→違規→案例→法條"],
    ["刑事 / 民事責任鏈", "R9–R13", "52", "義務→刑責→負責人連帶"],
    ["IT 工作情境鏈", "R14–R20", "214", "情境→事故→證據→任務→角色"],
    ["風險雷達 / 罰則鏈", "R21–R24", "24", "違規→法條→罰則→受理單位"],
    ["合計", "24 種", "2,410", "0 懸空邊"],
  ], { bodySize: 13 });
  foot(slide, ctx, n);
}

function slidePDF(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "非結構化資料：VectorRAG PDF", "簡報展示 15 份核心 PDF；後台完整上傳 32 份");
  const rows = [
    ["類型", "核心文件", "來源"],
    ["法規", "勞基法、職安法、災保法、性平法、勞動事件法、大量解僱法、勞資爭議處理法、民法、刑法", "law.moj.gov.tw"],
    ["給付指南", "職災給付指南合輯", "bli.gov.tw"],
    ["職安指引", "不法侵害預防指引、異常工作負荷指引、腦心血管疾病認定參考", "osha.gov.tw"],
    ["案例", "重大職災統計、職災判決摘要、案例彙編", "osha.gov.tw / 司法判決"],
  ];
  smallTable(slide, ctx, 75, 175, [160, 760, 250], 86, rows, { bodySize: 15, headerSize: 16 });
  ctx.addText(slide, { x: 120, y: 620, w: 1040, h: 30, text: "VectorRAG 用於語意檢索，讓 AI 回答口語問題時能引用官方原文。", fontSize: 20, color: BLUE, bold: true, align: "center" });
  foot(slide, ctx, n);
}

async function slideModel(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "模型設計：事故如何變成決策鏈", "直接使用既有 Graph 節點截圖，不重新生成流程圖");
  await ctx.addImage(slide, { path: `${ASSET}/螢幕擷取畫面 2026-05-08 000936.png`, x: 20, y: 124, w: 1240, h: 402, fit: "contain", alt: "Graph path screenshot" });
  card(slide, ctx, 74, 565, 1132, 64, { fill: "#DDF2FF", line: "#DDF2FF" });
  ctx.addText(slide, { x: 106, y: 578, w: 1070, h: 38, text: "核心鏈：工作情境 S → 事故 A → 法規 L → 企業義務 D / 勞工權益 B → 文件 DOC → 罰則 P / 刑責 CR / 民事賠償 CV\n範例：S004 → A003 → L001/L002 → D002/D003 → DOC001/DOC003 → CR002", fontSize: 14.5, color: INK, bold: true });
  foot(slide, ctx, n);
}

function slidePrompt(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "Prompt Design 與 Context Engineering", "三類 Prompt 對應三種產品情境");
  const xs = [90, 475, 860];
  [["應急導航", "事故責任判定\n法定義務查詢\n雙面介面切換", "工程師到客戶機房搬伺服器扭傷，誰負責？"], ["精準止損", "資遣程序確認\n舉證缺口分析", "要資遣表現不佳的工程師，有哪些程序？"], ["風險雷達", "同業對標\n裁罰統計", "100 人 IT 公司常加班，主要違規風險是什麼？"]].forEach((col, i) => {
    card(slide, ctx, xs[i], 170, 330, 230, { fill: "#FFFFFF" });
    ctx.addText(slide, { x: xs[i] + 30, y: 198, w: 270, h: 34, text: col[0], fontSize: 25, bold: true, color: INK });
    ctx.addText(slide, { x: xs[i] + 30, y: 250, w: 260, h: 70, text: col[1], fontSize: 18, color: MUTED });
    card(slide, ctx, xs[i] + 28, 326, 274, 54, { fill: "#D6E5FF", line: "#D6E5FF" });
    ctx.addText(slide, { x: xs[i] + 40, y: 337, w: 248, h: 34, text: col[2], fontSize: 13, bold: true, color: INK });
  });
  card(slide, ctx, 90, 455, 1090, 145, { fill: PALE });
  ctx.addText(slide, { x: 120, y: 478, w: 1040, h: 86, text: "Robot Setting：繁體中文、台灣法規語境；先判斷使用場景；回答必須包含判定、義務、文件、罰則、風險；引用格式為法規名稱§條號；Cypher 使用 Neo4j v5，禁用 OVER()。", fontSize: 21, color: INK });
  foot(slide, ctx, n);
}

async function slideAPI(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "API 與介面雛形", "直接使用既有深色 UI 截圖，不重新生成介面圖");
  await ctx.addImage(slide, { path: `${ASSET}/螢幕擷取畫面 2026-05-08 140630.png`, x: 70, y: 142, w: 860, h: 395, fit: "contain", alt: "UI screenshot" });
  card(slide, ctx, 965, 150, 235, 390, { fill: "#F8FBFF" });
  ctx.addText(slide, { x: 992, y: 174, w: 180, h: 30, text: "核心 API", fontSize: 23, bold: true, color: INK });
  bullets(slide, ctx, 992, 226, 175, ["POST /chat/create", "POST /chat/{id}", "GET /chat/{id}/messages"], { fontSize: 14, lineHeight: 47 });
  ctx.addText(slide, { x: 992, y: 390, w: 180, h: 26, text: "介面功能", fontSize: 21, bold: true, color: INK });
  bullets(slide, ctx, 992, 435, 175, ["身份切換", "情境選擇", "結構化回答", "GraphRAG 路徑"], { fontSize: 14, lineHeight: 30, bulletColor: GREEN });
  foot(slide, ctx, n);
}

function demoSlide(slide, ctx, n, titleText, question, points, pathText) {
  bg(slide, ctx); title(slide, ctx, titleText);
  card(slide, ctx, 66, 152, 540, 380, { fill: "#0E1117", line: "#1F2937" });
  ctx.addText(slide, { x: 95, y: 184, w: 480, h: 28, text: "EAP QA 畫面", fontSize: 24, bold: true, color: "#FFFFFF", align: "center" });
  ctx.addShape(slide, { x: 98, y: 230, w: 445, h: 86, fill: "#6366D966" });
  ctx.addText(slide, { x: 118, y: 249, w: 405, h: 48, text: question, fontSize: 16, color: "#FFFFFF" });
  ctx.addShape(slide, { x: 98, y: 344, w: 445, h: 120, fill: "#151A22", line: { style: "solid", fill: "#2B3443", width: 1 } });
  ctx.addText(slide, { x: 120, y: 382, w: 400, h: 42, text: "此區可在 Canva 中替換為實際平台 QA 截圖", fontSize: 18, bold: true, color: "#9CA3AF", align: "center" });
  card(slide, ctx, 654, 152, 560, 380, { fill: PALE2 });
  ctx.addText(slide, { x: 690, y: 184, w: 480, h: 34, text: "AI 回答重點", fontSize: 27, bold: true, color: INK });
  bullets(slide, ctx, 690, 242, 470, points, { fontSize: 17, lineHeight: 39 });
  card(slide, ctx, 90, 575, 1090, 54, { fill: "#E6F7EA", line: "#E6F7EA" });
  ctx.addText(slide, { x: 120, y: 590, w: 1030, h: 26, text: pathText, fontSize: 18, bold: true, color: GREEN, align: "center" });
  foot(slide, ctx, n);
}

function slideDemo4(slide, ctx, n) {
  bg(slide, ctx); title(slide, ctx, "Demo 4：雙面介面，同一事故 HR 與勞工不同輸出");
  ctx.addText(slide, { x: 95, y: 145, w: 1090, h: 32, text: "同一事故：工程師去客戶端開會途中發生車禍，現在住院。", fontSize: 24, bold: true, color: BLUE, align: "center" });
  smallTable(slide, ctx, 110, 205, [520, 520], 66, [
    ["HR 端輸出", "勞工端輸出"],
    ["判斷通勤 / 公出 / 職災", "可申請傷病給付、醫療給付"],
    ["公司補償與通報義務", "失能或照護給付可能性"],
    ["應備證據與文件", "診斷證明、事故證明、薪資資料"],
    ["罰則與責任邊界", "受理單位：勞保局 / 勞工局"],
  ], { bodySize: 18, headerSize: 21 });
  ctx.addText(slide, { x: 170, y: 600, w: 940, h: 36, text: "核心展示：同一知識庫、同一事故，GraphRAG 依身份走不同決策路徑。", fontSize: 23, bold: true, color: GREEN, align: "center" });
  foot(slide, ctx, n);
}

export async function addByIndex(presentation, ctx, index) {
  const slide = presentation.slides.add();
  if (index === 1) await cover(slide, ctx);
  if (index === 2) slidePain(slide, ctx, 1);
  if (index === 3) slideSolution(slide, ctx, 2);
  if (index === 4) slideScenarios(slide, ctx, 3);
  if (index === 5) slideLLM(slide, ctx, 4);
  if (index === 6) await slideArchitecture(slide, ctx, 5);
  if (index === 7) slideStructuredCollect(slide, ctx, 6);
  if (index === 8) slideStructuredGraph(slide, ctx, 7);
  if (index === 9) slidePDF(slide, ctx, 8);
  if (index === 10) await slideModel(slide, ctx, 9);
  if (index === 11) slidePrompt(slide, ctx, 10);
  if (index === 12) await slideAPI(slide, ctx, 11);
  if (index === 13) demoSlide(slide, ctx, 12, "Demo 1：應急導航，駐點工程師機房搬運受傷", "我是 IT 公司人資。工程師到客戶機房支援維修，搬伺服器時扭傷腰送醫。客戶說現場由我們公司管，我們說是客戶指揮。這算職災嗎？誰要負責？", ["S004 → A003，職災成立初判", "勞基法§59 補償", "勞基法§63-1 連帶責任", "文件：派工單、門禁紀錄、合約、診斷證明", "風險：業務過失傷害、民事賠償"], "S004 → A003 → L001/L002 → D002/D003 → DOC001/DOC003 → CR002");
  if (index === 14) demoSlide(slide, ctx, 13, "Demo 2：精準止損，資遣程序合規確認", "我要資遣表現不佳的工程師，有哪些程序？期限是什麼？不照做會怎樣？", ["確認資遣理由、預告期、資遣費", "非自願離職證明", "工資 / 出勤 / 績效紀錄", "勞動事件法§37 工資推定", "大量解僱需 60 日前計畫"], "S008 → A006 → L023/L024/L025 → D009–D011");
  if (index === 15) demoSlide(slide, ctx, 14, "Demo 3：法規風險雷達，100 人 IT 公司同業對標", "我們是 100 人 IT 公司，常有加班，評估主要違規風險。", ["工資給付、加班費、工時紀錄", "災保法行政義務", "資訊服務業工資工時裁罰 2,363 件", "災保法裁罰 687 件", "建議：先補出勤紀錄、加班核准、on-call 工時規則"], "IND_08 → VP → L → D / DOC");
  if (index === 16) slideDemo4(slide, ctx, 15);
  return slide;
}
