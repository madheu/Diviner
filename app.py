#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策系统 Web 服务
启动后手机浏览器访问 http://你的IP:5000 即可使用
"""

import json
import sys
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# 导入现有模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from real_data_collector import RealDataCollector
from news_monitor import NewsMonitor
from skill_manager import get_skill_manager
from llm_analyzer import LLMAnalyzer

app = Flask(__name__)
CORS(app)

# 全局实例（延迟初始化，避免启动阻塞）
real_data = None
news_monitor = None
skill_mgr = None
llm_analyzer = None


def init_modules():
    global real_data, news_monitor, skill_mgr, llm_analyzer
    if real_data is None:
        real_data = RealDataCollector()
        news_monitor = NewsMonitor()
        skill_mgr = get_skill_manager()
        llm_analyzer = LLMAnalyzer()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js")


@app.route("/api/debug")
def debug():
    """调试接口：查看 LLM 配置状态"""
    import os
    from crypto_utils import get_llm_config
    cfg = get_llm_config()
    return jsonify({
        "env_key_set": bool(os.environ.get("LLM_API_KEY")),
        "env_url_set": bool(os.environ.get("LLM_BASE_URL")),
        "env_model_set": bool(os.environ.get("LLM_MODEL")),
        "config_loaded": bool(cfg),
        "config_provider": cfg.get("base_url", "N/A") if cfg else "N/A",
        "config_model": cfg.get("model", "N/A") if cfg else "N/A",
        "has_api_key": bool(cfg.get("api_key")) if cfg else False,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """核心分析接口"""
    init_modules()

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    method = data.get("method", "梅花易数")

    if not question:
        return jsonify({"error": "请输入问题"}), 400

    # 设置术数方法
    skill_mgr.set_active_method(method)

    try:
        # 1. 采集真实数据
        market_data = real_data.collect_all()
    except Exception as e:
        market_data = {"index": None, "margin": None, "error": str(e)}

    try:
        # 2. 新闻分析
        news_analysis = news_monitor.full_analysis()
    except Exception as e:
        news_analysis = {"news_count": 0, "error": str(e)}

    # 3. 数学预测
    math_result = _math_predict(market_data)

    # 4. 术数预测
    iching_result = skill_mgr.divine(question, method=method)

    # 5. 巴菲特视角
    buffett_analysis = skill_mgr.analyze_investment(question, market_data, news_analysis)

    # 6. 时空校准
    spatio = _spatio_analyze()

    # 7. 综合决策
    decision = _decide(math_result, iching_result, market_data, news_analysis,
                       spatio, buffett_analysis)

    # 8. LLM 深度分析（如果有 API Key）
    llm_result = llm_analyzer.analyze(
        question, math_result, iching_result, market_data,
        news_analysis, spatio, decision, buffett_analysis
    )

    return jsonify({
        "success": True,
        "question": question,
        "method": method,
        "timestamp": datetime.now().isoformat(),
        "math": math_result,
        "iching": _simplify_iching(iching_result),
        "buffett": buffett_analysis,
        "market": _simplify_market(market_data),
        "news": _simplify_news(news_analysis),
        "spatio": spatio,
        "decision": decision,
        "llm": llm_result,
    })


def _math_predict(market_data):
    """内联数学预测"""
    import math
    index = market_data.get("index") or {}
    margin = market_data.get("margin") or {}
    sentiment = market_data.get("sentiment") or {}

    base_prob = 0.50
    base_prob += index.get("change_pct", 0) * 1.5
    base_prob += margin.get("margin_trend", 0) * 0.03
    base_prob += (sentiment.get("score", 0.5) - 0.5) * 0.2
    base_prob = max(0.10, min(0.90, base_prob))

    raw_vol = index.get("volatility_20d", 0.15)
    volatility = max(raw_vol, 0.02)

    z = 1.96
    moe = z * volatility / math.sqrt(20)
    ci_low = max(0.01, base_prob - moe)
    ci_high = min(0.99, base_prob + moe)

    p = base_prob
    entropy = -p * math.log2(p) - (1 - p) * math.log2(1 - p) if 0 < p < 1 else 0

    return {
        "probability": round(base_prob, 4),
        "direction": "上涨" if base_prob > 0.5 else "下跌",
        "confidence_interval": f"{ci_low:.1%} ~ {ci_high:.1%}",
        "volatility": f"{volatility:.2%}",
        "entropy": f"{entropy:.2%}",
        "entropy_raw": round(entropy, 4),
    }


def _spatio_analyze():
    """内联时空分析"""
    from decision_system import SpatioTemporal
    st = SpatioTemporal()
    return st.analyze()


def _decide(math_result, iching_result, market_data, news_analysis, spatio, buffett):
    """内联决策"""
    from decision_system import DecisionEngine
    de = DecisionEngine()

    # 转换格式
    math_fmt = {
        "probability": math_result["probability"],
        "entropy": math_result["entropy_raw"],
        "direction": math_result["direction"],
        "volatility": float(math_result["volatility"].rstrip("%")) / 100,
        "variance": (float(math_result["volatility"].rstrip("%")) / 100) ** 2,
        "confidence_interval": (0.4, 0.6),
        "sample_size": 20,
        "confidence_level": 0.95,
        "data_source": "真实行情",
    }

    d = de.decide(math_fmt, iching_result, market_data, news_analysis, spatio,
                  buffett_analysis=buffett)

    return {
        "score": f"{d['综合评分']:.1%}",
        "direction": d["方向"],
        "action": d["行动指令"],
        "position": d["仓位建议"],
        "stop_loss": d["止损建议"],
        "weights": f"数学{d['权重分配']['数学']:.0%} | 术数{d['权重分配']['术数']:.0%} | 宏观{d['权重分配']['宏观']:.0%}",
        "chaos": d["混沌触发"],
        "conflict": d["冲突裁决"],
        "reflexivity": d["反身性提醒"],
    }


def _simplify_iching(result):
    ben = result["本卦"]
    bian = result["变卦"]
    sk = result["体用生克"]
    jd = result["解读"]
    return {
        "method": result.get("method", "梅花易数"),
        "ben_gua": f"{ben['name']}（{ben['upper']}上{ben['lower']}下）",
        "ben_judgment": ben["judgment"],
        "bian_gua": f"{bian['name']}（{bian['upper']}上{bian['lower']}下）",
        "dong_yao": result["动爻"],
        "ti_gua": f"{result['体卦']['name']}（{result['体卦']['element']}）",
        "yong_gua": f"{result['用卦']['name']}（{result['用卦']['element']}）",
        "shengke": f"{sk['关系']} → {sk['含义']}",
        "trend": jd["趋势定性"],
        "advice": jd["行动建议"],
        "score": jd["综合评分"],
        "time": result["起卦时间"],
        "warning": result.get("warning", ""),
    }


def _simplify_market(data):
    idx = data.get("index") or {}
    mrg = data.get("margin") or {}
    nf = data.get("north_flow") or {}
    sec = data.get("sector") or {}
    sent = data.get("sentiment") or {}
    return {
        "index": f"{idx.get('close', 'N/A')}",
        "change": f"{idx.get('change_pct', 0):+.2%}",
        "volatility": f"{idx.get('volatility_20d', 0):.2%}",
        "margin_balance": f"{mrg.get('margin_balance', 0)/1e8:.0f}亿",
        "margin_trend": "增加" if mrg.get('margin_trend', 0) > 0 else "减少",
        "north_flow": f"{nf.get('net_flow', 0):+.1f}亿",
        "sentiment": sent.get("level", "N/A"),
        "fear_greed": sent.get("fear_greed", "N/A"),
        "leading": sec.get("leading_sector", "N/A"),
    }


def _simplify_news(data):
    pol = data.get("policy", {})
    nws = data.get("sentiment", {})
    return {
        "count": data.get("news_count", 0),
        "phase": pol.get("phase", "N/A"),
        "urgency": pol.get("urgency", "N/A"),
        "signals": ", ".join(pol.get("active_categories", [])) or "无",
        "sentiment": nws.get("sentiment", "N/A"),
        "pos": nws.get("positive_count", 0),
        "neg": nws.get("negative_count", 0),
    }


if __name__ == "__main__":
    print("=" * 50)
    print("  决策系统 Web 服务启动中...")
    print("  手机浏览器访问: http://你的IP:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)