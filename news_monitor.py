# -*- coding: utf-8 -*-
"""
新闻与政策监听模块
数据源：东方财富新闻、百度经济新闻（通过akshare）
"""

import akshare as ak
from datetime import datetime, timedelta
import re
import warnings
warnings.filterwarnings("ignore")


class NewsMonitor:
    """实时新闻监听与政策信号提取"""

    # 政策关键词库
    POLICY_KEYWORDS = {
        "货币政策": ["降准", "降息", "LPR", "MLF", "逆回购", "准备金", "利率", "央行", "流动性"],
        "财政政策": ["减税", "赤字", "专项债", "基建", "财政", "补贴"],
        "产业政策": ["新能源", "芯片", "半导体", "人工智能", "AI", "数字经济", "碳中和", "光伏", "电动车"],
        "监管政策": ["监管", "处罚", "立案", "调查", "反垄断", "合规"],
        "资本市场": ["IPO", "注册制", "退市", "减持", "分红", "回购", "T+0"],
    }

    # 政策阶段判断
    PHASE_PATTERNS = {
        "吹风期": ["研究", "探讨", "可能", "拟", "或将", "有望", "考虑"],
        "征求意见": ["征求意见", "草案", "征求意见稿"],
        "即将落地": ["即将", "近期", "加快", "推进", "落地", "实施"],
        "已落地": ["发布", "出台", "实施", "正式", "印发", "通知"],
    }

    def __init__(self):
        self.news_cache = []
        self.policy_signals = {}
        self.cache_time = None

    def fetch_news(self, keyword=""):
        """获取最新新闻"""
        # 缓存5分钟
        if self.cache_time and (datetime.now() - self.cache_time).total_seconds() < 300:
            return self.news_cache

        try:
            df = ak.stock_news_em()
            news_list = []
            for _, row in df.head(30).iterrows():
                news_list.append({
                    "title": str(row["新闻标题"]),
                    "content": str(row.get("新闻内容", ""))[:200],
                    "time": str(row["发布时间"]),
                    "source": str(row.get("文章来源", "")),
                })
            self.news_cache = news_list
            self.cache_time = datetime.now()
            return news_list
        except Exception as e:
            print(f"[新闻获取异常] {e}")
            return self.news_cache if self.news_cache else []

    def analyze_policy(self, news_list=None):
        """分析新闻中的政策信号"""
        if news_list is None:
            news_list = self.fetch_news()

        if not news_list:
            return {"phase": "未知", "signals": {}, "summary": "暂无新闻数据"}

        signals = {}
        all_text = " ".join([n["title"] + " " + n["content"] for n in news_list])

        # 检测政策类别
        for category, keywords in self.POLICY_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in all_text)
            if count > 0:
                signals[category] = {"mention_count": count, "signal": "活跃" if count >= 3 else "出现"}

        # 检测政策阶段
        phase_scores = {}
        for phase, patterns in self.PHASE_PATTERNS.items():
            score = sum(1 for p in patterns if p in all_text)
            if score > 0:
                phase_scores[phase] = score

        if phase_scores:
            dominant_phase = max(phase_scores, key=phase_scores.get)
        else:
            dominant_phase = "平稳期"

        # 检测紧急程度
        urgency = "低"
        urgency_keywords = ["紧急", "突发", "重大", "黑天鹅", "危机"]
        if any(kw in all_text for kw in urgency_keywords):
            urgency = "高"

        result = {
            "phase": dominant_phase,
            "urgency": urgency,
            "signals": signals,
            "summary": f"当前政策阶段：{dominant_phase}，紧急程度：{urgency}",
            "active_categories": list(signals.keys()),
        }

        self.policy_signals = result
        return result

    def get_policy_impact_score(self):
        """
        将政策信号量化为影响分数
        +1 = 利好，-1 = 利空，0 = 中性
        """
        signals = self.policy_signals
        if not signals or not signals.get("signals"):
            return 0.0

        score = 0.0
        # 宽松政策利好
        positive_cats = ["货币政策", "财政政策"]
        # 监管政策偏利空
        negative_cats = ["监管政策"]

        for cat in signals["signals"]:
            if cat in positive_cats:
                score += 0.15
            elif cat in negative_cats:
                score -= 0.15
            else:
                score += 0.05  # 产业政策中性偏正

        # 政策阶段影响
        phase = signals.get("phase", "")
        if phase == "即将落地":
            score += 0.1
        elif phase == "已落地":
            score -= 0.05  # 利好出尽

        return max(-0.5, min(0.5, score))

    def get_news_sentiment(self, news_list=None):
        """
        新闻情绪分析（基于关键词匹配，非NLP模型）
        简单但实用，不需要GPU
        """
        if news_list is None:
            news_list = self.fetch_news()

        if not news_list:
            return {"sentiment": "中性", "score": 0.5}

        positive_words = ["涨", "利好", "增长", "突破", "创新高", "盈利", "回购", "分红", "增持"]
        negative_words = ["跌", "利空", "下滑", "亏损", "暴雷", "减持", "处罚", "退市", "风险"]

        pos_count = 0
        neg_count = 0

        for news in news_list:
            text = news["title"] + news["content"]
            pos_count += sum(1 for w in positive_words if w in text)
            neg_count += sum(1 for w in negative_words if w in text)

        total = pos_count + neg_count
        if total == 0:
            return {"sentiment": "中性", "score": 0.5}

        score = pos_count / total
        score = 0.1 + score * 0.8  # 缩放到0.1-0.9

        if score > 0.6:
            sentiment = "乐观"
        elif score < 0.4:
            sentiment = "悲观"
        else:
            sentiment = "中性"

        return {
            "sentiment": sentiment,
            "score": round(score, 4),
            "positive_count": pos_count,
            "negative_count": neg_count,
        }

    def full_analysis(self):
        """完整分析：新闻+政策+情绪"""
        news = self.fetch_news()
        policy = self.analyze_policy(news)
        sentiment = self.get_news_sentiment(news)
        impact = self.get_policy_impact_score()

        return {
            "news_count": len(news),
            "policy": policy,
            "sentiment": sentiment,
            "policy_impact_score": round(impact, 4),
            "timestamp": datetime.now().isoformat(),
        }


# 运行测试
if __name__ == "__main__":
    monitor = NewsMonitor()
    result = monitor.full_analysis()
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))