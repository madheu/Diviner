#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融合数学预测与术数易学的战略决策系统 v3.0
真实数据版 + 多Skill集成

Skill来源：
  - 梅花易数（内置）
  - 奇门遁甲（Numerologist_skills 适配）
  - 巴菲特视角（投资逻辑层）

用法：python decision_system.py
     python decision_system.py --method qimen   # 使用奇门遁甲
     python decision_system.py --method meihua  # 使用梅花易数（默认）
"""

import math
import json
import os
import sys
from datetime import datetime, timedelta

# 真实数据模块
from real_data_collector import RealDataCollector
from news_monitor import NewsMonitor
from skill_manager import get_skill_manager
from buffett_skill import BuffettSkill


# ============================================================
# 第一部分：数学预测引擎（基于真实数据）
# ============================================================

class MathEngine:
    """基于真实市场数据的量化预测"""

    def __init__(self):
        self.last_prediction = None

    def predict(self, real_data):
        """
        输入：真实市场数据（来自RealDataCollector）
        输出：上涨概率、置信区间、波动率、熵值
        """
        index = real_data.get("index") or {}
        margin = real_data.get("margin") or {}
        sentiment = real_data.get("sentiment") or {}

        # 基础概率 = 50% + 近期趋势修正
        base_prob = 0.50

        # 指数涨跌影响
        change_pct = index.get("change_pct", 0)
        base_prob += change_pct * 1.5  # 涨1%增加1.5%概率

        # 融资趋势影响
        margin_trend = margin.get("margin_trend", 0)
        base_prob += margin_trend * 0.03

        # 情绪影响
        sentiment_score = sentiment.get("score", 0.5)
        base_prob += (sentiment_score - 0.5) * 0.2

        # 限制在10%-90%
        base_prob = max(0.10, min(0.90, base_prob))

        # 波动率（使用真实20日波动率，年化处理）
        raw_vol = index.get("volatility_20d", 0.15)
        volatility = max(raw_vol, 0.02)  # 不低于2%

        # 置信区间（95%）
        z_score = 1.96
        margin_of_error = z_score * volatility / math.sqrt(20)
        ci_lower = max(0.01, base_prob - margin_of_error)
        ci_upper = min(0.99, base_prob + margin_of_error)

        # 熵值
        p = base_prob
        if p > 0 and p < 1:
            entropy = -p * math.log2(p) - (1 - p) * math.log2(1 - p)
        else:
            entropy = 0

        # 方差
        variance = volatility ** 2

        result = {
            "probability": round(base_prob, 4),
            "confidence_interval": (round(ci_lower, 4), round(ci_upper, 4)),
            "volatility": round(volatility, 4),
            "variance": round(variance, 4),
            "entropy": round(entropy, 4),
            "sample_size": 20,
            "direction": "上涨" if base_prob > 0.5 else "下跌",
            "confidence_level": 0.95,
            "data_source": "真实行情（akshare）",
        }
        self.last_prediction = result
        return result


# ============================================================
# 第二部分：时空与校准模块
# ============================================================

class SpatioTemporal:
    """时空校准：节气、黄历、预期差监控"""

    SOLAR_TERMS = [
        ("立春", (2, 4)), ("雨水", (2, 19)), ("惊蛰", (3, 6)), ("春分", (3, 21)),
        ("清明", (4, 5)), ("谷雨", (4, 20)), ("立夏", (5, 6)), ("小满", (5, 21)),
        ("芒种", (6, 6)), ("夏至", (6, 21)), ("小暑", (7, 7)), ("大暑", (7, 23)),
        ("立秋", (8, 7)), ("处暑", (8, 23)), ("白露", (9, 8)), ("秋分", (9, 23)),
        ("寒露", (10, 8)), ("霜降", (10, 23)), ("立冬", (11, 7)), ("小雪", (11, 22)),
        ("大雪", (12, 7)), ("冬至", (12, 22)), ("小寒", (1, 6)), ("大寒", (1, 20)),
    ]

    HUANGLI = {
        "立春": {"宜": ["谋划", "布局", "学习", "签约"], "忌": ["冒进", "大举投资"]},
        "春分": {"宜": ["平衡配置", "调整仓位", "合作"], "忌": ["极端操作", "孤注一掷"]},
        "立夏": {"宜": ["积极进取", "扩大投入", "创新"], "忌": ["保守退缩", "观望"]},
        "夏至": {"宜": ["稳健持有", "获利了结", "复盘"], "忌": ["追高", "加杠杆"]},
        "立秋": {"宜": ["收割利润", "调整策略", "收缩"], "忌": ["扩张", "新项目"]},
        "秋分": {"宜": ["均衡配置", "对冲风险", "研究"], "忌": ["单边重仓", "冲动"]},
        "立冬": {"宜": ["储备", "防守", "学习研究"], "忌": ["激进", "大额支出"]},
        "冬至": {"宜": ["布局来年", "长线建仓", "内省"], "忌": ["短线博弈", "频繁交易"]},
    }

    def __init__(self):
        self.deviation_history = []
        self.last_prediction = None

    def analyze(self, dt=None):
        if dt is None:
            dt = datetime.now()
        current_term = self._get_solar_term(dt)
        huangli_info = self._get_huangli(current_term)
        lunar_month = (dt.month + 1) % 12 or 12
        season = self._get_season(dt.month)

        return {
            "当前节气": current_term,
            "季节": season,
            "农历月": f"农历{lunar_month}月",
            "黄历宜忌": huangli_info,
            "日期": dt.strftime("%Y-%m-%d"),
            "时辰": self._get_shichen(dt.hour),
        }

    def _get_solar_term(self, dt):
        doy = dt.timetuple().tm_yday
        best_term, best_doy = "春分", 0
        for term, (m, d) in self.SOLAR_TERMS:
            term_doy = datetime(dt.year, m, d).timetuple().tm_yday
            if term_doy <= doy and term_doy >= best_doy:
                best_doy, best_term = term_doy, term
        return best_term

    def _get_huangli(self, term):
        for key in self.HUANGLI:
            if key in term or term in key:
                return self.HUANGLI[key]
        return {"宜": ["正常操作"], "忌": ["极端操作"]}

    def _get_season(self, month):
        if month in [3, 4, 5]: return "春"
        elif month in [6, 7, 8]: return "夏"
        elif month in [9, 10, 11]: return "秋"
        return "冬"

    def _get_shichen(self, hour):
        shichen_map = [
            (23, "子时"), (1, "丑时"), (3, "寅时"), (5, "卯时"),
            (7, "辰时"), (9, "巳时"), (11, "午时"), (13, "未时"),
            (15, "申时"), (17, "酉时"), (19, "戌时"), (21, "亥时"),
        ]
        for start, name in shichen_map:
            if hour >= start:
                return name
        return "子时"

    def check_deviation(self, predicted_prob, actual_change):
        """
        预期差监控：对比预测概率与真实涨跌
        actual_change: 指数实际涨跌幅（正=涨，负=跌）
        """
        # 将实际涨跌转为0/1
        actual_outcome = 1.0 if actual_change > 0 else 0.0
        deviation = abs(predicted_prob - actual_outcome)
        threshold = 2 * 0.15  # 2个标准差

        alert = deviation > threshold
        self.deviation_history.append({
            "time": datetime.now().isoformat(),
            "predicted": predicted_prob,
            "actual_change": actual_change,
            "actual_outcome": actual_outcome,
            "deviation": round(deviation, 4),
            "alert": alert,
        })

        if alert:
            return {
                "alert": True,
                "message": f"预期差警报！预测偏差{deviation:.2%}超过2σ阈值{threshold:.2%}，建议重新校准模型",
                "deviation": round(deviation, 4),
            }
        return {
            "alert": False,
            "message": "预期差在正常范围内",
            "deviation": round(deviation, 4),
        }


# ============================================================
# 第三部分：决策引擎
# ============================================================

class DecisionEngine:
    """综合决策引擎"""

    def __init__(self):
        self.math_weight = 0.60
        self.iching_weight = 0.25
        self.macro_weight = 0.15
        self.decision_log = []

    def _assess_macro(self, real_data, news_analysis, spatio_info):
        """评估宏观逻辑（真实数据驱动）"""
        score = 0.5  # 中性

        # 政策影响
        policy = news_analysis.get("policy", {})
        impact = news_analysis.get("policy_impact_score", 0)
        score += impact

        # 新闻情绪
        sentiment = news_analysis.get("sentiment", {})
        score += (sentiment.get("score", 0.5) - 0.5) * 0.3

        # 黄历宜忌
        huangli = spatio_info.get("黄历宜忌", {})
        yi = str(huangli.get("宜", []))
        if "积极" in yi or "进取" in yi:
            score += 0.02
        if "防守" in yi or "收缩" in yi:
            score -= 0.02

        # 融资趋势
        margin = real_data.get("margin") or {}
        if margin.get("margin_trend", 0) > 0:
            score += 0.03
        elif margin.get("margin_trend", 0) < 0:
            score -= 0.03

        return max(0.10, min(0.90, score))

    def decide(self, math_result, iching_result, real_data, news_analysis, spatio_info,
                buffett_analysis=None):
        """综合决策"""
        math_prob = math_result["probability"]
        math_entropy = math_result["entropy"]

        # 混沌触发器
        if math_entropy > 0.90:
            self.math_weight = 0.45
            self.iching_weight = 0.40
            self.macro_weight = 0.15
            chaos_triggered = True
        else:
            self.math_weight = 0.60
            self.iching_weight = 0.25
            self.macro_weight = 0.15
            chaos_triggered = False

        # 术数信号量化
        iching_score = (iching_result["解读"]["综合评分"] + 3) / 6
        iching_score = max(0.05, min(0.95, iching_score))

        # 宏观信号
        macro_score = self._assess_macro(real_data, news_analysis, spatio_info)

        # 加权综合
        composite = (
            math_prob * self.math_weight
            + iching_score * self.iching_weight
            + macro_score * self.macro_weight
        )

        # 巴菲特视角作为额外调整层（±10%范围）
        buffett_score = None
        if buffett_analysis:
            buffett_score = buffett_analysis.get("score", 0.5)
            # 巴菲特视角偏保守，只做向下修正不做向上放大
            if buffett_score < 0.5:
                adjustment = (buffett_score - 0.5) * 0.2  # 最多向下拉10%
                composite += adjustment
            # 绿灯时微调向上
            elif buffett_score > 0.6:
                composite += 0.03

        # 冲突仲裁
        math_dir = "看多" if math_prob > 0.5 else "看空"
        iching_dir = "看多" if iching_score > 0.5 else "看空"
        conflict = (math_dir != iching_dir)
        arbitration = ""

        if conflict:
            sentiment = news_analysis.get("sentiment", {})
            fear_greed = sentiment.get("fear_greed", "中性")
            policy = news_analysis.get("policy", {})

            if policy.get("phase", "") in ["吹风期", "征求意见", "即将落地"]:
                arbitration = "政策密集期，以数学信号为准"
                composite = composite * 0.7 + math_prob * 0.3
            elif fear_greed == "恐惧":
                arbitration = "情绪极端期（恐惧），以术数警示为准"
                composite = composite * 0.5 + iching_score * 0.5
            else:
                arbitration = "信号模糊，建议不做决策"
                composite = 0.5

        # 仓位建议
        if composite > 0.65:
            position = f"{round((composite - 0.5) * 200)}%"
            action = "积极做多"
            stop_loss = f"-{round((1 - composite) * 10 + 2, 1)}%"
        elif composite > 0.55:
            position = f"{round((composite - 0.5) * 200)}%"
            action = "轻仓试探"
            stop_loss = f"-{round((1 - composite) * 7 + 1, 1)}%"
        elif composite > 0.45:
            position = "0%"
            action = "观望等待"
            stop_loss = "N/A"
        elif composite > 0.35:
            position = "减至10%以下"
            action = "防御减仓"
            stop_loss = f"-{round(composite * 5, 1)}%"
        else:
            position = "清仓"
            action = "立即离场"
            stop_loss = "N/A"

        reflexivity = self._generate_reflexivity(composite, action)

        decision = {
            "综合评分": round(composite, 4),
            "方向": "看多" if composite > 0.5 else "看空",
            "行动指令": action,
            "仓位建议": position,
            "止损建议": stop_loss,
            "混沌触发": chaos_triggered,
            "冲突裁决": arbitration if conflict else "无冲突",
            "权重分配": {"数学": self.math_weight, "术数": self.iching_weight, "宏观": self.macro_weight},
            "反身性提醒": reflexivity,
        }

        self.decision_log.append(decision)
        return decision

    def _generate_reflexivity(self, composite, action):
        if composite > 0.65:
            return "如果大量用户按此信号做多，可能推高价格形成自我实现的预言。建议分批入场。"
        elif composite > 0.55:
            return "轻仓操作对市场影响有限，反身性风险较低。"
        elif composite > 0.45:
            return "观望信号本身不产生市场影响，但若多数人同时观望，流动性可能下降。"
        elif composite > 0.35:
            return "减仓信号若被广泛传播，可能引发恐慌性抛售。建议私下执行。"
        else:
            return "大规模清仓信号可能导致踩踏。建议分多日执行，降低冲击成本。"


# ============================================================
# 第四部分：输出格式化
# ============================================================

class OutputFormatter:
    """三维决策矩阵输出"""

    def format(self, question, math_result, iching_result, real_data,
               news_analysis, spatio_info, decision, deviation_check,
               buffett_analysis=None):
        lines = []
        lines.append("=" * 70)
        lines.append("                    三 维 决 策 矩 阵")
        lines.append("=" * 70)
        lines.append(f"")
        lines.append(f"  决策问题：{question}")
        lines.append(f"  分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        method = iching_result.get("method", "梅花易数")
        lines.append(f"  术数方法：{method}")
        lines.append(f"")

        # 第一维：概率层
        lines.append("─" * 70)
        lines.append("  【第一维】概率层信号（数学预测引擎 · 真实数据）")
        lines.append("─" * 70)
        lines.append(f"  预测方向：{math_result['direction']}（概率 {math_result['probability']:.2%}）")
        lines.append(f"  95%置信区间：[{math_result['confidence_interval'][0]:.2%}, {math_result['confidence_interval'][1]:.2%}]")
        lines.append(f"  波动率(20日)：{math_result['volatility']:.2%}　|　方差：{math_result['variance']:.4f}")
        lines.append(f"  熵值：{math_result['entropy']:.2%}")
        lines.append(f"  数据来源：{math_result['data_source']}")
        if math_result['entropy'] > 0.90:
            lines.append(f"  ⚠ 熵值过高，触发混沌机制！")
        lines.append(f"")

        # 第二维：象征层
        lines.append("─" * 70)
        lines.append("  【第二维】象征层信号（术数易学参谋）")
        lines.append("─" * 70)
        ben = iching_result["本卦"]
        bian = iching_result["变卦"]
        hu = iching_result["互卦"]
        ti = iching_result["体卦"]
        yong = iching_result["用卦"]
        sk = iching_result["体用生克"]
        jd = iching_result["解读"]

        lines.append(f"  起卦时间：{iching_result['起卦时间']}（{iching_result['时辰']}时）")
        lines.append(f"  本卦：{ben['name']}（{ben['upper']}上{ben['lower']}下）")
        lines.append(f"    　　{ben['judgment']}")
        lines.append(f"  互卦：{hu['name']}（{hu['upper']}上{hu['lower']}下）")
        lines.append(f"  变卦：{bian['name']}（{bian['upper']}上{bian['lower']}下）")
        lines.append(f"    　　{bian['judgment']}")
        lines.append(f"  动爻：第{iching_result['动爻']}爻")
        lines.append(f"  体卦：{ti['name']}（{ti['element']}，{ti['nature']}）")
        lines.append(f"  用卦：{yong['name']}（{yong['element']}，{yong['nature']}）")
        lines.append(f"  体用关系：{sk['关系']} → {sk['含义']}")
        lines.append(f"  趋势定性：{jd['趋势定性']}")
        lines.append(f"  术数建议：{jd['行动建议']}")
        lines.append(f"  综合评分：{jd['综合评分']}")
        lines.append(f"")

        # 第三维：事实层
        lines.append("─" * 70)
        lines.append("  【第三维】事实层信号（真实市场数据）")
        lines.append("─" * 70)
        idx = real_data.get("index") or {}
        mrg = real_data.get("margin") or {}
        nf = real_data.get("north_flow") or {}
        sec = real_data.get("sector") or {}
        sent = real_data.get("sentiment") or {}

        lines.append(f"  上证指数：{idx.get('close', 'N/A')}　|　涨跌：{idx.get('change_pct', 0):+.2%}")
        lines.append(f"  20日波动率：{idx.get('volatility_20d', 0):.2%}")
        lines.append(f"  融资余额：{mrg.get('margin_balance', 0)/1e8:.0f}亿　|　趋势：{'增加' if mrg.get('margin_trend',0)>0 else '减少'}")
        lines.append(f"  融券余额：{mrg.get('short_balance', 0)/1e8:.0f}亿")
        lines.append(f"  北向资金：{nf.get('net_flow', 0):+.1f}亿")
        lines.append(f"  市场情绪：{sent.get('level', 'N/A')}（{sent.get('fear_greed', 'N/A')}）")
        lines.append(f"  领涨板块：{sec.get('leading_sector', 'N/A')}")
        lines.append(f"  领跌板块：{sec.get('lagging_sector', 'N/A')}")
        lines.append(f"")

        # 新闻政策
        pol = news_analysis.get("policy", {})
        nws = news_analysis.get("sentiment", {})
        lines.append(f"  新闻数量：{news_analysis.get('news_count', 0)}条")
        lines.append(f"  政策阶段：{pol.get('phase', 'N/A')}　|　紧急程度：{pol.get('urgency', 'N/A')}")
        lines.append(f"  政策信号：{', '.join(pol.get('active_categories', [])) or '无明显信号'}")
        lines.append(f"  新闻情绪：{nws.get('sentiment', 'N/A')}（正面{nws.get('positive_count',0)}/负面{nws.get('negative_count',0)}）")
        lines.append(f"")

        # 时空校准
        lines.append(f"  时空校准：{spatio_info['日期']}　{spatio_info['季节']}季　{spatio_info['当前节气']}")
        lines.append(f"  黄历宜：{'、'.join(spatio_info['黄历宜忌'].get('宜', []))}")
        lines.append(f"  黄历忌：{'、'.join(spatio_info['黄历宜忌'].get('忌', []))}")
        if deviation_check["alert"]:
            lines.append(f"  ⚠ 预期差警报：{deviation_check['message']}")
        lines.append(f"")

        # 综合裁决
        lines.append("─" * 70)
        lines.append("  【综合裁决】")
        lines.append("─" * 70)
        lines.append(f"  综合评分：{decision['综合评分']:.2%}（{decision['方向']}）")
        lines.append(f"  行动指令：{decision['行动指令']}")
        lines.append(f"  仓位建议：{decision['仓位建议']}")
        lines.append(f"  止损建议：{decision['止损建议']}")
        lines.append(f"  权重分配：数学{decision['权重分配']['数学']:.0%} | 术数{decision['权重分配']['术数']:.0%} | 宏观{decision['权重分配']['宏观']:.0%}")
        if decision["混沌触发"]:
            lines.append(f"  ⚠ 混沌模式已激活")
        if decision["冲突裁决"] != "无冲突":
            lines.append(f"  ⚡ 冲突裁决：{decision['冲突裁决']}")
        lines.append(f"")

        # 反身性提醒
        lines.append("─" * 70)
        lines.append("  【反身性提醒】")
        lines.append("─" * 70)
        lines.append(f"  {decision['反身性提醒']}")
        lines.append(f"")

        # 巴菲特视角
        if buffett_analysis:
            lines.append("─" * 70)
            lines.append("  【巴菲特视角】")
            lines.append("─" * 70)
            bf = buffett_analysis
            lines.append(f"  巴菲特评分：{bf['score']:.2%}")
            lines.append(f"  安全边际：{bf['margin_of_safety']['level']}（{bf['margin_of_safety']['score']:.2%}）")
            lines.append(f"  红灯信号：{bf['red_flags_total']}个　|　绿灯信号：{bf['green_flags_total']}个")
            lines.append(f"  结论：{bf['verdict']}")
            if bf.get("relevant_heuristics"):
                lines.append(f"  匹配启发式：")
                for name, desc in bf["relevant_heuristics"][:3]:
                    lines.append(f"    · {name}：{desc}")
            lines.append(f"")

        # 数据采集异常
        errors = real_data.get("errors", [])
        if errors:
            lines.append(f"  ⚠ 数据采集异常：{'; '.join(errors)}")
            lines.append(f"")

        lines.append("=" * 70)
        lines.append("  免责声明：本系统仅供研究参考，不构成投资建议。")
        lines.append("=" * 70)

        return "\n".join(lines)


# ============================================================
# 第五部分：反馈数据库
# ============================================================

class FeedbackDB:
    def __init__(self, db_path="feedback_db.json"):
        self.db_path = db_path
        self.records = []
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.records = []

    def _save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def record(self, question, decision, actual_outcome=None):
        record = {
            "time": datetime.now().isoformat(),
            "question": question,
            "decision": {
                "score": decision["综合评分"],
                "direction": decision["方向"],
                "action": decision["行动指令"],
                "position": decision["仓位建议"],
            },
            "actual_outcome": actual_outcome,
            "is_correct": None,
        }
        if actual_outcome is not None:
            pred_dir = decision["方向"]
            correct = (pred_dir == "看多" and actual_outcome == "涨") or \
                      (pred_dir == "看空" and actual_outcome == "跌")
            record["is_correct"] = correct

        self.records.append(record)
        self._save()
        return record

    def get_stats(self):
        if not self.records:
            return {"total": 0, "accuracy": None, "message": "暂无记录"}
        judged = [r for r in self.records if r["is_correct"] is not None]
        if not judged:
            return {"total": len(self.records), "accuracy": None, "message": "暂无已判定结果"}
        correct = sum(1 for r in judged if r["is_correct"])
        accuracy = correct / len(judged)
        return {
            "total": len(self.records),
            "judged": len(judged),
            "correct": correct,
            "accuracy": round(accuracy, 4),
            "message": f"准确率 {accuracy:.2%}（{correct}/{len(judged)}）",
        }


# ============================================================
# 第六部分：主程序
# ============================================================

def main():
    # 解析命令行参数
    method = "梅花易数"
    if "--method" in sys.argv:
        idx = sys.argv.index("--method")
        if idx + 1 < len(sys.argv):
            arg = sys.argv[idx + 1]
            method_map = {"qimen": "奇门遁甲", "meihua": "梅花易数", "ziwei": "紫微斗数"}
            method = method_map.get(arg, "梅花易数")

    print("=" * 70)
    print(f"    融合数学预测与术数易学的战略决策系统 v3.0")
    print(f"    数据源：akshare 实时行情 + 东方财富新闻")
    print(f"    术数方法：{method}")
    print("=" * 70)
    print("")
    print("已加载Skill：")
    print("  术数层：梅花易数、奇门遁甲（Numerologist_skills）")
    print("  投资层：巴菲特视角（6大心智模型 + 8条启发式）")
    print("")
    print("提示：输入 'quit' 退出，'stats' 查看准确率")
    print("      'method qimen' 切换奇门遁甲，'method meihua' 切换梅花易数")
    print("")

    # 初始化
    real_data = RealDataCollector()
    news_monitor = NewsMonitor()
    skill_mgr = get_skill_manager()
    skill_mgr.set_active_method(method)
    buffett = BuffettSkill()
    math_engine = MathEngine()
    spatio_temporal = SpatioTemporal()
    decision_engine = DecisionEngine()
    output_formatter = OutputFormatter()
    feedback_db = FeedbackDB()

    print("正在初始化数据连接...")

    # 预采集数据（测试连通性）
    try:
        test_data = real_data.collect_all()
        test_errors = test_data.get("errors", [])
        if test_errors:
            print(f"⚠ 部分数据源异常：{'; '.join(test_errors)}")
        else:
            print("✓ 行情数据连接正常")
    except Exception as e:
        print(f"⚠ 数据采集初始化异常：{e}")

    try:
        test_news = news_monitor.full_analysis()
        print(f"✓ 新闻监听正常（获取{test_news['news_count']}条新闻）")
    except Exception as e:
        print(f"⚠ 新闻监听初始化异常：{e}")

    print("")

    while True:
        try:
            question = input("\n请输入你的决策问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() == "quit":
            print("再见！")
            break
        if question.lower() == "stats":
            stats = feedback_db.get_stats()
            print(f"\n历史统计：{stats['message']}")
            continue

        if question.lower().startswith("method "):
            new_method = question[7:].strip()
            method_map = {"qimen": "奇门遁甲", "meihua": "梅花易数", "ziwei": "紫微斗数"}
            new_method = method_map.get(new_method, new_method)
            if skill_mgr.set_active_method(new_method):
                method = new_method
                print(f"已切换术数方法为：{method}")
            else:
                print(f"不支持的方法：{new_method}，可用：梅花易数/奇门遁甲/紫微斗数")
            continue

        print("\n正在采集数据 & 分析中...\n")

        # 1. 采集真实数据
        try:
            market_data = real_data.collect_all()
        except Exception as e:
            print(f"数据采集失败：{e}，使用上一次缓存数据")
            market_data = {"index": None, "margin": None, "north_flow": None,
                          "sector": None, "sentiment": None, "errors": [str(e)]}

        # 2. 新闻政策分析
        try:
            news_analysis = news_monitor.full_analysis()
        except Exception as e:
            print(f"新闻分析失败：{e}")
            news_analysis = {"news_count": 0, "policy": {}, "sentiment": {},
                            "policy_impact_score": 0}

        # 3. 时空校准
        spatio_info = spatio_temporal.analyze()

        # 4. 数学预测（基于真实数据）
        math_result = math_engine.predict(market_data)

        # 5. 术数预测（使用Skill管理器）
        iching_result = skill_mgr.divine(question, method=method)

        # 6. 巴菲特视角分析
        buffett_analysis = skill_mgr.analyze_investment(question, market_data, news_analysis)

        # 7. 综合决策（融入巴菲特视角）
        decision = decision_engine.decide(
            math_result, iching_result, market_data, news_analysis, spatio_info,
            buffett_analysis=buffett_analysis
        )

        # 7. 预期差检查（对比真实涨跌）
        actual_change = (market_data.get("index") or {}).get("change_pct", 0)
        deviation_check = spatio_temporal.check_deviation(
            math_result["probability"], actual_change
        )

        # 8. 输出
        output = output_formatter.format(
            question, math_result, iching_result,
            market_data, news_analysis, spatio_info, decision, deviation_check,
            buffett_analysis=buffett_analysis
        )
        print(output)

        # 9. 记录
        feedback_db.record(question, decision)

        # 10. 询问实际结果
        print("\n" + "-" * 50)
        try:
            actual = input("请输入实际结果（涨/跌/跳过）：").strip()
            if actual in ["涨", "跌"]:
                feedback_db.record(question, decision, actual)
                stats = feedback_db.get_stats()
                print(f"已记录。当前统计：{stats['message']}")
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    main()