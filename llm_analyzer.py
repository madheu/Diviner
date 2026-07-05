#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 深度分析引擎
将多维决策数据送入大模型，生成综合解读与策略建议

支持 OpenAI 兼容 API（OpenAI / DeepSeek / Qwen / 智谱 等）
"""

import os
import json
import hashlib
from datetime import datetime
from crypto_utils import get_llm_config


# ── 默认配置（会被加密文件或环境变量覆盖） ──────────────────
_LLM_DEFAULTS = {
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
}
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "1200"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "30"))


class LLMAnalyzer:
    """
    LLM 深度分析器
    - 将数学预测、术数占卜、市场数据、新闻政策、巴菲特视角 融合为自然语言解读
    - 无 API Key 时自动降级为规则引擎
    """

    def __init__(self):
        self._client = None
        self._config = None
        self._available = None  # None = 未检测

    def _load_config(self):
        """加载配置（加密文件或环境变量）"""
        if self._config is None:
            self._config = get_llm_config()
        return self._config

    @property
    def available(self) -> bool:
        if self._available is None:
            cfg = self._load_config()
            self._available = bool(cfg.get("api_key"))
        return self._available

    def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is not None:
            return self._client

        cfg = self._load_config()
        api_key = cfg.get("api_key")
        if not api_key:
            return None

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=api_key,
                base_url=cfg.get("base_url", _LLM_DEFAULTS["base_url"]),
                timeout=LLM_TIMEOUT,
            )
            return self._client
        except ImportError:
            return None
        except Exception:
            return None

    def analyze(self, question: str, math_result: dict, iching_result: dict,
                market_data: dict, news_analysis: dict, spatio: dict,
                decision: dict, buffett_analysis: dict = None) -> dict:
        """
        主入口：综合所有数据，调用 LLM 生成深度分析

        返回 dict:
            - source: "llm" | "fallback"
            - analysis: 自然语言解读
            - risk_level: 风险等级
            - key_factors: 关键因素
            - contrarian: 反向思考
            - timestamp: 时间戳
        """
        if not self.available:
            return self._fallback_analysis(question, math_result, decision)

        prompt = self._build_prompt(question, math_result, iching_result,
                                     market_data, news_analysis, spatio,
                                     decision, buffett_analysis)

        try:
            client = self._get_client()
            if not client:
                return self._fallback_analysis(question, math_result, decision)

            cfg = self._load_config()
            response = client.chat.completions.create(
                model=cfg.get("model", _LLM_DEFAULTS["model"]),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )

            raw = response.choices[0].message.content.strip()
            return self._parse_llm_response(raw)

        except Exception as e:
            # LLM 调用失败，降级为规则引擎
            fallback = self._fallback_analysis(question, math_result, decision)
            fallback["llm_error"] = str(e)
            return fallback

    def _build_prompt(self, question, math_result, iching_result,
                      market_data, news_analysis, spatio, decision,
                      buffett_analysis):
        """构建发送给 LLM 的 Prompt"""
        # 简化术数数据
        iching_simple = {
            "本卦": iching_result.get("本卦", {}).get("name", ""),
            "变卦": iching_result.get("变卦", {}).get("name", ""),
            "体用关系": iching_result.get("体用生克", {}).get("关系", ""),
            "趋势": iching_result.get("解读", {}).get("趋势定性", ""),
        }

        # 简化市场数据
        idx = market_data.get("index") or {}
        mrg = market_data.get("margin") or {}
        nf = market_data.get("north_flow") or {}
        sent = market_data.get("sentiment") or {}

        market_simple = {
            "指数": idx.get("close", "N/A"),
            "涨跌": f"{idx.get('change_pct', 0):+.2%}",
            "波动率": f"{idx.get('volatility_20d', 0):.2%}",
            "融资趋势": "增加" if mrg.get("margin_trend", 0) > 0 else "减少",
            "北向资金": f"{nf.get('net_flow', 0):+.1f}亿",
            "市场情绪": sent.get("level", "N/A"),
            "贪婪恐惧": sent.get("fear_greed", "N/A"),
        }

        policy = news_analysis.get("policy", {})
        nws = news_analysis.get("sentiment", {})

        news_simple = {
            "新闻数量": news_analysis.get("news_count", 0),
            "政策阶段": policy.get("phase", "N/A"),
            "新闻情绪": nws.get("sentiment", "N/A"),
        }

        buffett_simple = None
        if buffett_analysis:
            buffett_simple = {
                "评分": f"{buffett_analysis.get('score', 0):.0%}",
                "安全边际": buffett_analysis.get("margin_of_safety", {}).get("level", "N/A"),
                "红灯": buffett_analysis.get("red_flags_total", 0),
                "绿灯": buffett_analysis.get("green_flags_total", 0),
                "结论": buffett_analysis.get("verdict", "N/A"),
            }

        prompt = f"""请对以下投资决策问题进行综合分析。

【用户问题】
{question}

【第一维 · 数学预测】
- 上涨概率：{math_result.get('probability', 0):.2%}
- 预测方向：{math_result.get('direction', '')}
- 置信区间：{math_result.get('confidence_interval', '')}
- 波动率：{math_result.get('volatility', '')}
- 熵值：{math_result.get('entropy', '')}

【第二维 · 术数占卜】
- 方法：{iching_result.get('method', '')}
- 本卦：{iching_simple.get('本卦', '')}
- 变卦：{iching_simple.get('变卦', '')}
- 体用关系：{iching_simple.get('体用关系', '')}
- 趋势定性：{iching_simple.get('趋势', '')}

【第三维 · 市场数据】
- 上证指数：{market_simple.get('指数', '')}
- 涨跌：{market_simple.get('涨跌', '')}
- 20日波动率：{market_simple.get('波动率', '')}
- 融资趋势：{market_simple.get('融资趋势', '')}
- 北向资金：{market_simple.get('北向资金', '')}
- 市场情绪：{market_simple.get('市场情绪', '')}
- 贪婪恐惧指数：{market_simple.get('贪婪恐惧', '')}

【新闻政策】
- 新闻数量：{news_simple.get('新闻数量', 0)}条
- 政策阶段：{news_simple.get('政策阶段', '')}
- 新闻情绪：{news_simple.get('新闻情绪', '')}

【时空校准】
- 节气：{spatio.get('当前节气', '')}
- 季节：{spatio.get('季节', '')}
- 黄历宜：{'、'.join(spatio.get('黄历宜忌', {}).get('宜', []))}
- 黄历忌：{'、'.join(spatio.get('黄历宜忌', {}).get('忌', []))}"""

        if buffett_simple:
            prompt += f"""

【巴菲特视角】
- 评分：{buffett_simple.get('评分', '')}
- 安全边际：{buffett_simple.get('安全边际', '')}
- 红灯信号：{buffett_simple.get('红灯', 0)}个
- 绿灯信号：{buffett_simple.get('绿灯', 0)}个
- 结论：{buffett_simple.get('结论', '')}"""

        prompt += f"""

【综合决策】
- 评分：{decision.get('score', '')}
- 方向：{decision.get('direction', '')}
- 行动指令：{decision.get('action', '')}
- 仓位建议：{decision.get('position', '')}
- 止损建议：{decision.get('stop_loss', '')}
- 混沌触发：{'是' if decision.get('chaos') else '否'}
- 冲突裁决：{decision.get('conflict', '')}

请输出 JSON 格式（不要 markdown 包裹）：
{{"analysis": "200字以内的综合解读，融合数学、术数、市场的核心逻辑",
 "risk_level": "低/中/高/极高",
 "key_factors": ["因素1", "因素2", "因素3"],
 "contrarian": "反向思考：如果判断错了，最可能的原因是什么（30字）"}}"""

        return prompt

    def _parse_llm_response(self, raw: str) -> dict:
        """解析 LLM 返回的 JSON"""
        # 清理可能的 markdown 包裹
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # 解析失败，返回原始文本
            parsed = {
                "analysis": raw[:500],
                "risk_level": "中",
                "key_factors": ["LLM 返回格式异常"],
                "contrarian": "无法解析反向思考",
            }

        return {
            "source": "llm",
            "model": self._load_config().get("model", _LLM_DEFAULTS["model"]),
            "analysis": parsed.get("analysis", ""),
            "risk_level": parsed.get("risk_level", "中"),
            "key_factors": parsed.get("key_factors", []),
            "contrarian": parsed.get("contrarian", ""),
            "timestamp": datetime.now().isoformat(),
        }

    def _fallback_analysis(self, question: str, math_result: dict,
                            decision: dict) -> dict:
        """无 LLM 时的规则引擎降级分析"""
        prob = math_result.get("probability", 0.5)
        score_raw = decision.get("score", "50%")
        try:
            score = float(score_raw.rstrip("%")) / 100
        except (ValueError, AttributeError):
            score = 0.5

        if prob > 0.65:
            analysis = f"数学模型显示上涨概率 {prob:.1%}，综合评分 {score:.1%}。当前市场动能偏强，技术面支持{decision.get('direction', '')}判断。建议结合术数卦象与宏观政策交叉验证。"
            risk = "中"
            factors = ["数学概率偏强", f"综合评分 {score:.1%}", "关注波动率变化"]
            contrarian = "若宏观政策突变或北向资金大幅流出，上涨逻辑可能失效"
        elif prob > 0.55:
            analysis = f"上涨概率 {prob:.1%}，方向偏多但信号不够强。综合评分 {score:.1%}，建议轻仓试探，等待更明确信号。"
            risk = "中"
            factors = ["信号偏弱", "需等待确认", "控制仓位"]
            contrarian = "若成交量萎缩或情绪转冷，可能是假突破"
        elif prob > 0.45:
            analysis = f"概率 {prob:.1%} 处于中性区间，综合评分 {score:.1%}。市场方向不明，建议观望为主，减少操作频率。"
            risk = "中"
            factors = ["方向不明", "中性区间", "观望为宜"]
            contrarian = "盘整后可能选择方向，需密切关注突破信号"
        elif prob > 0.35:
            analysis = f"下跌概率偏大（{1-prob:.1%}），综合评分 {score:.1%}。建议防御减仓，控制风险敞口。"
            risk = "高"
            factors = ["下跌概率偏高", "防御为主", "控制仓位"]
            contrarian = "若出现重大利好政策，可能扭转跌势"
        else:
            analysis = f"下跌概率 {1-prob:.1%}，信号强烈偏空，综合评分 {score:.1%}。建议清仓离场，等待风险释放。"
            risk = "极高"
            factors = ["强烈偏空信号", "清仓离场", "等待风险释放"]
            contrarian = "极端恐慌时往往是逆向布局的时机，但需极大勇气"

        return {
            "source": "fallback",
            "model": "rule_engine",
            "analysis": analysis,
            "risk_level": risk,
            "key_factors": factors,
            "contrarian": contrarian,
            "timestamp": datetime.now().isoformat(),
        }


# ── System Prompt ─────────────────────────────────────────
SYSTEM_PROMPT = """你是一位融合量化金融、中国传统术数易学与宏观经济学的战略分析师。
你的任务是将多维度的决策数据（数学概率、易经卦象、市场行情、政策新闻、巴菲特价值投资视角）综合为一个清晰、有洞察力的解读。

规则：
1. 用中文输出，简洁有力，避免废话
2. 解读要同时体现"理性的数学逻辑"和"易经卦象的象征含义"，将两者融会贯通
3. 风险等级要综合考虑：概率、熵值、卦象吉凶、市场情绪
4. 关键因素要抓住最核心的 3 个要点
5. 反向思考（contrarian）要诚实指出判断可能出错的最关键原因
6. 严格输出 JSON 格式，不要额外文字

示例输出：
{"analysis": "数学概率65%偏多，泽火革卦象显示变革之机，市场情绪贪婪但北向资金流入，建议积极但分批建仓",
 "risk_level": "中",
 "key_factors": ["数学概率偏强", "革卦变革信号", "北向资金支撑"],
 "contrarian": "若政策突转或外部冲击，变革可能夭折"}"""