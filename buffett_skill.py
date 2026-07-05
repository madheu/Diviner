# -*- coding: utf-8 -*-
"""
巴菲特视角Skill
基于 https://everythingskill.net/zh/skills/buffett-perspective

核心能力：
- 6大心智模型评估
- 8条决策启发式
- 安全边际计算
- 能力圈判断
"""

from datetime import datetime


class BuffettSkill:
    """
    巴菲特视角 —— 投资逻辑层

    不是替代数学/术数预测，而是从"企业质量"和"安全边际"
    角度提供独立判断，作为宏观逻辑层的补充。
    """

    # 6大心智模型
    MENTAL_MODELS = {
        "经济护城河": {
            "question": "这个东西的竞争优势能持续多久？",
            "red_flags": ["门槛低", "同质化", "价格战", "无品牌"],
            "green_flags": ["垄断", "专利", "品牌", "网络效应", "转换成本高"],
        },
        "能力圈": {
            "question": "你真正理解这个东西吗？",
            "red_flags": ["听不懂", "太复杂", "新技术", "不熟悉"],
            "green_flags": ["简单", "熟悉", "可预测", "经验丰富"],
        },
        "市场先生": {
            "question": "当前价格是恐慌还是贪婪？",
            "red_flags": ["追涨", "FOMO", "恐慌抛售"],
            "green_flags": ["低估", "无人问津", "冷静评估"],
        },
        "复利雪球": {
            "question": "这个决策长期来看能滚雪球吗？",
            "red_flags": ["短期", "一次性", "不可持续"],
            "green_flags": ["长期", "可积累", "复利效应"],
        },
        "制度惯性": {
            "question": "有没有组织惯性在推动盲目决策？",
            "red_flags": ["跟风", "羊群效应", "被迫"],
            "green_flags": ["独立思考", "逆向", "主动"],
        },
        "所有者心态": {
            "question": "如果这是你自己的全部身家？",
            "red_flags": ["投机", "杠杆", "all-in"],
            "green_flags": ["谨慎", "研究", "安全边际"],
        },
    }

    # 8条决策启发式
    HEURISTICS = {
        "安全边际": "买入价格要远低于内在价值，留足犯错空间",
        "管理层诚信": "和管理层吃顿饭，你愿意把女儿嫁给他吗？",
        "打孔卡规则": "假设你一生只能做20次决策，这次值得打一个孔吗？",
        "甜蜜点规则": "这件事在你的能力圈内，且你比大多数人更懂？",
        "蟑螂规则": "看到一个蟑螂，说明厨房里不止一个——坏消息往往成群出现",
        "五分钟规则": "五分钟内讲不清楚的商业模式，不投",
        "报纸测试": "如果明天报纸头条报道你的决策，你会骄傲还是羞愧？",
        "太难堆": "如果搞不懂，就放进'太难'堆，不碰",
    }

    def analyze(self, question, real_data, news_analysis):
        """
        巴菲特视角分析

        返回：
        - 心智模型评估
        - 决策启发式匹配
        - 安全边际判断
        - 综合投资建议
        """
        question_lower = question.lower()

        # 1. 运行6大心智模型
        model_results = {}
        red_count = 0
        green_count = 0

        for model_name, model in self.MENTAL_MODELS.items():
            reds = sum(1 for flag in model["red_flags"] if flag in question_lower)
            greens = sum(1 for flag in model["green_flags"] if flag in question_lower)
            red_count += reds
            green_count += greens

            if reds > greens:
                verdict = "⚠ 红灯"
            elif greens > reds:
                verdict = "✓ 绿灯"
            else:
                verdict = "○ 中性"

            model_results[model_name] = {
                "question": model["question"],
                "verdict": verdict,
                "red_flags_hit": reds,
                "green_flags_hit": greens,
            }

        # 2. 匹配决策启发式
        relevant_heuristics = []
        if any(w in question_lower for w in ["买", "入", "加仓", "建仓"]):
            relevant_heuristics.append(("安全边际", self.HEURISTICS["安全边际"]))
            relevant_heuristics.append(("打孔卡规则", self.HEURISTICS["打孔卡规则"]))
        if any(w in question_lower for w in ["卖", "减仓", "清仓", "止损"]):
            relevant_heuristics.append(("蟑螂规则", self.HEURISTICS["蟑螂规则"]))
            relevant_heuristics.append(("报纸测试", self.HEURISTICS["报纸测试"]))
        if any(w in question_lower for w in ["复杂", "不懂", "新技术"]):
            relevant_heuristics.append(("太难堆", self.HEURISTICS["太难堆"]))
            relevant_heuristics.append(("五分钟规则", self.HEURISTICS["五分钟规则"]))
        if any(w in question_lower for w in ["杠杆", "借钱", "all", "全部"]):
            relevant_heuristics.append(("所有者心态", self.HEURISTICS["所有者心态"]))

        # 3. 安全边际计算（基于市场数据）
        margin_of_safety = self._calc_margin_of_safety(real_data, news_analysis)

        # 4. 综合判断
        total_score = green_count - red_count
        if total_score >= 3:
            buffett_verdict = "巴菲特会说：这在他的能力圈内，可以认真考虑"
            buffett_score = 0.75
        elif total_score >= 1:
            buffett_verdict = "巴菲特会说：再研究研究，不急着下注"
            buffett_score = 0.55
        elif total_score >= -1:
            buffett_verdict = "巴菲特会说：放进'太难'堆，别碰"
            buffett_score = 0.40
        else:
            buffett_verdict = "巴菲特会说：远离，这不是你的游戏"
            buffett_score = 0.25

        return {
            "mental_models": model_results,
            "relevant_heuristics": relevant_heuristics,
            "margin_of_safety": margin_of_safety,
            "verdict": buffett_verdict,
            "score": buffett_score,
            "red_flags_total": red_count,
            "green_flags_total": green_count,
            "timestamp": datetime.now().isoformat(),
        }

    def _calc_margin_of_safety(self, real_data, news_analysis):
        """计算安全边际（简化版）"""
        index = real_data.get("index") or {}
        sentiment = real_data.get("sentiment") or {}
        margin = real_data.get("margin") or {}

        safety = 0.5  # 中性

        # 波动率越高，安全边际越低
        vol = index.get("volatility_20d", 0.15)
        if vol > 0.20:
            safety -= 0.15
        elif vol < 0.10:
            safety += 0.10

        # 情绪极端时安全边际低
        fear_greed = sentiment.get("fear_greed", "中性")
        if fear_greed == "恐惧":
            safety += 0.10  # 恐惧时反而可能有机会
        elif fear_greed == "贪婪":
            safety -= 0.15

        # 融资趋势
        if margin.get("margin_trend", 0) < 0:
            safety -= 0.05

        safety = max(0.1, min(0.9, safety))

        if safety > 0.65:
            level = "较高"
        elif safety > 0.45:
            level = "中等"
        else:
            level = "较低"

        return {"score": round(safety, 4), "level": level}

    def format_for_decision(self, analysis_result):
        """将分析结果格式化为决策系统可用的文本"""
        lines = []
        lines.append("【巴菲特视角评估】")

        # 心智模型
        models = analysis_result.get("mental_models", {})
        for name, result in models.items():
            lines.append(f"  {result['verdict']} {name}：{result['question']}")

        # 启发式
        heuristics = analysis_result.get("relevant_heuristics", [])
        if heuristics:
            lines.append(f"  匹配的决策启发式：")
            for name, desc in heuristics:
                lines.append(f"    · {name}：{desc}")

        # 安全边际
        margin = analysis_result.get("margin_of_safety", {})
        lines.append(f"  安全边际：{margin.get('level', 'N/A')}（{margin.get('score', 0):.2%}）")

        # 结论
        lines.append(f"  巴菲特结论：{analysis_result.get('verdict', '')}")

        return "\n".join(lines)

    def get_score(self, analysis_result):
        """获取0-1之间的评分"""
        return analysis_result.get("score", 0.5)