# -*- coding: utf-8 -*-
"""
真实数据采集模块
数据源：akshare（免费开源A股数据接口）
每次调用从网络拉取最新数据，不依赖本地缓存
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")


class RealDataCollector:
    """采集真实市场数据"""

    def __init__(self):
        self.cache = {}
        self.cache_time = {}

    def _is_cache_valid(self, key, seconds=300):
        """缓存5分钟内有效，避免频繁请求被限流"""
        if key in self.cache and key in self.cache_time:
            elapsed = (datetime.now() - self.cache_time[key]).total_seconds()
            return elapsed < seconds
        return False

    def collect_all(self):
        """采集全部数据，返回一个字典"""
        result = {}
        errors = []

        # 并行采集各类数据（串行调用，但逐个容错）
        for name, func in [
            ("index", self.get_index_data),
            ("margin", self.get_margin_data),
            ("north_flow", self.get_north_flow),
            ("sector", self.get_sector_data),
            ("sentiment", self.get_sentiment),
        ]:
            try:
                result[name] = func()
            except Exception as e:
                errors.append(f"{name}: {str(e)[:80]}")
                result[name] = None

        result["errors"] = errors
        result["timestamp"] = datetime.now().isoformat()
        return result

    def get_index_data(self):
        """获取上证指数最新行情"""
        key = "index_data"
        if self._is_cache_valid(key, 120):
            return self.cache[key]

        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df.empty:
            raise ValueError("获取指数数据为空")

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # 计算涨跌幅
        change_pct = (latest["close"] - prev["close"]) / prev["close"]

        # 计算最近20日波动率
        if len(df) >= 20:
            returns = df["close"].pct_change().dropna().tail(20)
            volatility = returns.std()
        else:
            volatility = 0.15

        result = {
            "date": str(latest["date"]),
            "close": float(latest["close"]),
            "volume": float(latest["volume"]),
            "change_pct": round(float(change_pct), 4),
            "volatility_20d": round(float(volatility), 4),
        }
        self.cache[key] = result
        self.cache_time[key] = datetime.now()
        return result

    def get_margin_data(self):
        """获取沪市融资融券余额"""
        key = "margin_data"
        if self._is_cache_valid(key, 120):
            return self.cache[key]

        df = ak.macro_china_market_margin_sh()
        if df.empty:
            raise ValueError("获取融资数据为空")

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # 融资余额趋势（+为增加，-为减少）
        margin_change = latest["融资余额"] - prev["融资余额"]
        margin_trend = 1 if margin_change > 0 else (-1 if margin_change < 0 else 0)

        result = {
            "date": str(latest["日期"]),
            "margin_balance": float(latest["融资余额"]),
            "margin_buy": float(latest["融资买入额"]),
            "short_balance": float(latest["融券余额"]),
            "total_balance": float(latest["融资融券余额"]),
            "margin_change": float(margin_change),
            "margin_trend": margin_trend,
        }
        self.cache[key] = result
        self.cache_time[key] = datetime.now()
        return result

    def get_north_flow(self):
        """获取北向资金流向"""
        key = "north_flow"
        if self._is_cache_valid(key, 120):
            return self.cache[key]

        try:
            df = ak.stock_hsgt_hist_em(symbol="北向资金")
            if df.empty:
                raise ValueError("北向资金数据为空")

            latest = df.iloc[-1]
            net_flow = latest.get("当日成交净买额", 0)
            if pd.isna(net_flow):
                net_flow = 0

            result = {
                "date": str(latest["日期"]),
                "net_flow": float(net_flow),
                "holding_value": float(latest.get("持股市值", 0)),
            }
        except Exception:
            # 北向数据有时不可用，返回默认值
            result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "net_flow": 0,
                "holding_value": 0,
                "note": "数据暂不可用",
            }

        self.cache[key] = result
        self.cache_time[key] = datetime.now()
        return result

    def get_sector_data(self):
        """获取板块轮动数据（从东方财富概念板块）"""
        key = "sector_data"
        if self._is_cache_valid(key, 120):
            return self.cache[key]

        result = {"top_sectors": [], "bottom_sectors": [], "leading_sector": "未知", "lagging_sector": "未知"}

        try:
            # 尝试概念板块（接口更稳定）
            df = ak.stock_board_concept_name_em()
            if not df.empty:
                df_sorted = df.sort_values("涨跌幅", ascending=False)
                top3 = df_sorted.head(3)[["板块名称", "涨跌幅"]].to_dict("records")
                bottom3 = df_sorted.tail(3)[["板块名称", "涨跌幅"]].to_dict("records")
                result = {
                    "top_sectors": top3,
                    "bottom_sectors": bottom3,
                    "leading_sector": top3[0]["板块名称"] if top3 else "未知",
                    "lagging_sector": bottom3[0]["板块名称"] if bottom3 else "未知",
                }
        except Exception:
            pass

        # 如果概念板块也失败，尝试行业板块
        if result["leading_sector"] == "未知":
            try:
                df = ak.stock_board_industry_name_em()
                if not df.empty:
                    df_sorted = df.sort_values("涨跌幅", ascending=False)
                    top3 = df_sorted.head(3)[["板块名称", "涨跌幅"]].to_dict("records")
                    bottom3 = df_sorted.tail(3)[["板块名称", "涨跌幅"]].to_dict("records")
                    result = {
                        "top_sectors": top3,
                        "bottom_sectors": bottom3,
                        "leading_sector": top3[0]["板块名称"] if top3 else "未知",
                        "lagging_sector": bottom3[0]["板块名称"] if bottom3 else "未知",
                    }
            except Exception:
                pass

        self.cache[key] = result
        self.cache_time[key] = datetime.now()
        return result

    def get_sentiment(self):
        """
        计算市场情绪指标
        基于：涨跌比、成交量变化、融资趋势
        """
        index_data = self.get_index_data()
        margin_data = self.get_margin_data()

        sentiment_score = 0.5  # 中性起步

        # 涨跌影响
        if index_data["change_pct"] > 0.01:
            sentiment_score += 0.15
        elif index_data["change_pct"] < -0.01:
            sentiment_score -= 0.15

        # 融资趋势影响
        sentiment_score += margin_data["margin_trend"] * 0.1

        # 波动率影响（高波动=恐慌=负面）
        if index_data["volatility_20d"] > 0.25:
            sentiment_score -= 0.1
        elif index_data["volatility_20d"] < 0.10:
            sentiment_score += 0.05

        sentiment_score = max(0.0, min(1.0, sentiment_score))

        return {
            "score": round(sentiment_score, 4),
            "level": "乐观" if sentiment_score > 0.6 else ("悲观" if sentiment_score < 0.4 else "中性"),
            "fear_greed": "贪婪" if sentiment_score > 0.7 else ("恐惧" if sentiment_score < 0.3 else "中性"),
        }


# 运行测试
if __name__ == "__main__":
    collector = RealDataCollector()
    data = collector.collect_all()
    import json
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))