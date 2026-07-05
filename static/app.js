// ========================================
// 术数决策系统 · 前端逻辑
// 设计：暗黑 + 毛玻璃 + 胶囊 + 环形图
// ========================================

let currentMethod = "梅花易数";

// 方法切换
document.querySelectorAll(".method-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".method-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const map = {"meihua":"梅花易数","qimen":"奇门遁甲"};
    currentMethod = map[btn.dataset.method] || "梅花易数";
    document.getElementById("methodBadge").textContent = currentMethod;
  });
});

// 折叠面板
function toggleAccordion(header) {
  header.parentElement.classList.toggle("open");
}

// 回车触发
document.getElementById("questionInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    analyze();
  }
});

// 环形图
function drawRing(containerId, percent, color) {
  const container = document.getElementById(containerId);
  const size = 90;
  const stroke = 5;
  const radius = (size / 2) - stroke;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percent);

  container.innerHTML = `
    <div class="ring-container">
      <svg class="ring-svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle class="ring-bg" cx="${size/2}" cy="${size/2}" r="${radius}" stroke-width="${stroke}"/>
        <circle class="ring-fill" cx="${size/2}" cy="${size/2}" r="${radius}" stroke-width="${stroke}"
          stroke="${color}" stroke-dasharray="${circumference}" stroke-dashoffset="${circumference}"
          style="stroke-dashoffset: ${offset}px;"/>
      </svg>
      <div class="ring-center">
        ${(percent*100).toFixed(0)}<small>%</small>
      </div>
    </div>
  `;
}

async function analyze() {
  const question = document.getElementById("questionInput").value.trim();
  if (!question) {
    showToast("请输入你的决策问题");
    return;
  }

  const btn = document.getElementById("analyzeBtn");
  const btnText = document.getElementById("btnText");
  const btnSpinner = document.getElementById("btnSpinner");

  btn.disabled = true;
  btnText.textContent = "分析中...";
  btnSpinner.classList.remove("hidden");

  // 显示结果区 + 骨架屏
  const resultSection = document.getElementById("resultSection");
  resultSection.style.display = "flex";
  document.getElementById("verdictCard").innerHTML = `
    <div class="skeleton skeleton-line" style="height:90px"></div>
  `;
  document.querySelectorAll(".accordion-body").forEach(b => {
    b.innerHTML = `
      <div class="skeleton skeleton-line"></div>
      <div class="skeleton skeleton-line short"></div>
      <div class="skeleton skeleton-line" style="width:40%"></div>
    `;
  });
  document.getElementById("reflexivityContent").innerHTML = `
    <div class="skeleton skeleton-line short"></div>
  `;

  resultSection.scrollIntoView({ behavior: "smooth" });

  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, method: currentMethod }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || "分析失败");
    }

    const data = await resp.json();
    renderResult(data);

  } catch (err) {
    showToast(err.message || "网络错误，请重试");
  } finally {
    btn.disabled = false;
    btnText.textContent = "开始分析";
    btnSpinner.classList.add("hidden");
  }
}

function renderResult(data) {
  const d = data.decision;
  const m = data.math;
  const i = data.iching;
  const mk = data.market;
  const nw = data.news;
  const sp = data.spatio;
  const bf = data.buffett;

  // 解析综合评分
  const scoreNum = parseFloat(d.score) / 100;
  const ringColor = scoreNum > 0.55 ? "#34d399" : (scoreNum > 0.45 ? "#fbbf24" : "#f87171");

  // 环形图
  drawRing("verdictRing", scoreNum, ringColor);

  // 裁决文字
  document.getElementById("verdictAction").textContent = d.action;
  document.getElementById("verdictDetail").innerHTML = `
    仓位：${d.position}<br>止损：${d.stop_loss}
  `;

  // 标签
  let tagsHTML = "";
  if (d.chaos) tagsHTML += '<span class="tag tag-yellow">混沌模式</span>';
  if (d.conflict && d.conflict !== "无冲突") tagsHTML += '<span class="tag tag-purple">冲突裁决</span>';
  tagsHTML += `<span class="tag tag-accent">${d.weights}</span>`;
  document.getElementById("verdictTags").innerHTML = tagsHTML;

  // 更新 Hero 统计
  updateHeroStats(data);

  // 第一维：概率
  const probClass = m.direction === "上涨" ? "up" : "down";
  document.getElementById("panelMath").innerHTML = `
    <div class="data-row">
      <span class="data-label">预测方向</span>
      <span class="data-value ${probClass}">${m.direction}（${(m.probability*100).toFixed(1)}%）</span>
    </div>
    <div class="data-row">
      <span class="data-label">95%置信区间</span>
      <span class="data-value dim">${m.confidence_interval}</span>
    </div>
    <div class="data-row">
      <span class="data-label">波动率</span>
      <span class="data-value dim">${m.volatility}</span>
    </div>
    <div class="data-row">
      <span class="data-label">熵值</span>
      <span class="data-value ${parseFloat(m.entropy) > 0.9 ? 'down' : 'dim'}">${m.entropy}</span>
    </div>
    <div class="data-row">
      <span class="data-label">数据源</span>
      <span class="data-value accent">真实行情（akshare）</span>
    </div>
  `;

  // 第二维：术数
  document.getElementById("panelIching").innerHTML = `
    <div class="data-row">
      <span class="data-label">方法</span>
      <span class="data-value accent">${i.method}</span>
    </div>
    <div class="data-row">
      <span class="data-label">本卦</span>
      <span class="data-value">${i.ben_gua}</span>
    </div>
    <div class="data-judgment">${i.ben_judgment}</div>
    <div class="data-row">
      <span class="data-label">变卦</span>
      <span class="data-value">${i.bian_gua}</span>
    </div>
    <div class="data-row">
      <span class="data-label">体用生克</span>
      <span class="data-value dim">${i.shengke}</span>
    </div>
    <div class="data-row">
      <span class="data-label">趋势</span>
      <span class="data-value dim">${i.trend}</span>
    </div>
    <div class="data-row">
      <span class="data-label">建议</span>
      <span class="data-value accent">${i.advice}</span>
    </div>
    ${i.warning ? `<div style="color:var(--yellow);font-size:12px;margin-top:6px;font-weight:300">⚠ ${i.warning}</div>` : ""}
  `;

  // 第三维：市场
  document.getElementById("panelMarket").innerHTML = `
    <div class="data-row">
      <span class="data-label">上证指数</span>
      <span class="data-value">${mk.index} <span class="${mk.change.startsWith('+') ? 'up' : 'down'}">${mk.change}</span></span>
    </div>
    <div class="data-row">
      <span class="data-label">波动率</span>
      <span class="data-value dim">${mk.volatility}</span>
    </div>
    <div class="data-row">
      <span class="data-label">融资余额</span>
      <span class="data-value dim">${mk.margin_balance}（${mk.margin_trend}）</span>
    </div>
    <div class="data-row">
      <span class="data-label">北向资金</span>
      <span class="data-value dim">${mk.north_flow}</span>
    </div>
    <div class="data-row">
      <span class="data-label">市场情绪</span>
      <span class="data-value dim">${mk.sentiment}（${mk.fear_greed}）</span>
    </div>
    <div class="data-row">
      <span class="data-label">领涨板块</span>
      <span class="data-value dim">${mk.leading}</span>
    </div>
    <div class="data-divider"></div>
    <div class="data-row">
      <span class="data-label">新闻</span>
      <span class="data-value dim">${nw.count}条</span>
    </div>
    <div class="data-row">
      <span class="data-label">政策阶段</span>
      <span class="data-value dim">${nw.phase}</span>
    </div>
    <div class="data-row">
      <span class="data-label">新闻情绪</span>
      <span class="data-value dim">${nw.sentiment}（正${nw.pos}/负${nw.neg}）</span>
    </div>
    <div class="data-divider"></div>
    <div class="data-row">
      <span class="data-label">节气</span>
      <span class="data-value dim">${sp['当前节气']} · ${sp['季节']}季</span>
    </div>
    <div class="data-row">
      <span class="data-label">黄历宜</span>
      <span class="data-value dim">${sp['黄历宜忌']['宜'].join('、')}</span>
    </div>
    <div class="data-row">
      <span class="data-label">黄历忌</span>
      <span class="data-value dim">${sp['黄历宜忌']['忌'].join('、')}</span>
    </div>
  `;

  // 巴菲特
  if (bf) {
    let dotsHTML = "";
    const models = bf.mental_models || {};
    for (const [name, result] of Object.entries(models)) {
      let cls = "neutral";
      if (result.verdict.includes("绿灯")) cls = "green";
      else if (result.verdict.includes("红灯")) cls = "red";
      dotsHTML += `
        <div class="bm-dot ${cls}">
          <span class="bm-dot-icon ${cls}"></span>
          ${name}
        </div>`;
    }

    let heuristicsHTML = "";
    const heuristics = bf.relevant_heuristics || [];
    heuristics.slice(0, 3).forEach(([name, desc]) => {
      heuristicsHTML += `<div class="heuristic-item"><b>${name}</b>：${desc}</div>`;
    });

    document.getElementById("panelBuffett").innerHTML = `
      <div class="data-row">
        <span class="data-label">巴菲特评分</span>
        <span class="data-value dim">${(bf.score*100).toFixed(0)}%</span>
      </div>
      <div class="data-row">
        <span class="data-label">安全边际</span>
        <span class="data-value dim">${bf.margin_of_safety.level}（${(bf.margin_of_safety.score*100).toFixed(0)}%）</span>
      </div>
      <div class="buffett-grid">${dotsHTML}</div>
      ${heuristicsHTML ? `<div style="margin-top:6px">${heuristicsHTML}</div>` : ""}
      <div style="margin-top:6px;font-size:12px;color:var(--text-dim);font-weight:300">${bf.verdict}</div>
    `;
  }

  // 反身性
  document.getElementById("reflexivityContent").textContent = d.reflexivity;

  // LLM 深度分析
  renderLLM(data.llm);
}

function updateHeroStats(data) {
  const w = data.decision.weights || "";
  const mathMatch = w.match(/数学(\d+)%/);
  const ichingMatch = w.match(/术数(\d+)%/);
  const macroMatch = w.match(/宏观(\d+)%/);

  if (mathMatch) document.getElementById("statMath").textContent = mathMatch[1] + "%";
  if (ichingMatch) document.getElementById("statIching").textContent = ichingMatch[1] + "%";
  if (macroMatch) document.getElementById("statMacro").textContent = macroMatch[1] + "%";
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

// LLM 分析渲染
function renderLLM(llm) {
  const card = document.getElementById("llmCard");
  if (!llm) {
    card.style.display = "none";
    return;
  }
  card.style.display = "block";

  // 来源标签
  const badge = document.getElementById("llmBadge");
  const model = document.getElementById("llmModel");
  if (llm.source === "llm") {
    badge.textContent = "AI 深度分析";
    badge.style.background = "linear-gradient(135deg, #a78bfa, #7c3aed)";
    model.textContent = llm.model || "";
  } else {
    badge.textContent = "规则引擎";
    badge.style.background = "linear-gradient(135deg, #6b7280, #4b5563)";
    model.textContent = llm.llm_error ? "LLM 调用失败，已降级" : "未配置 API Key";
  }

  // 分析文本
  document.getElementById("llmAnalysis").textContent = llm.analysis || "";

  // 风险等级
  const riskMap = {"低": "low", "中": "medium", "高": "high", "极高": "critical"};
  const riskEl = document.getElementById("llmRisk");
  const riskLevel = llm.risk_level || "中";
  riskEl.className = "llm-risk " + (riskMap[riskLevel] || "medium");
  riskEl.innerHTML = `⚠ 风险等级：${riskLevel}`;

  // 关键因素
  const factors = llm.key_factors || [];
  document.getElementById("llmFactors").innerHTML = factors
    .map(f => `<span class="llm-factor">${f}</span>`)
    .join("");

  // 反向思考
  document.getElementById("llmContrarian").textContent = llm.contrarian
    ? "反向思考：" + llm.contrarian
    : "";
}

// Service Worker
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}