# Diviner

> Where math meets metaphysics — quantified decisions, ancient wisdom.

融合数学预测与术数易学的战略决策系统。量化概率 + 易经卦象 + 巴菲特视角，三维决策矩阵。

## 功能

- **数学预测引擎**：基于真实A股行情数据，输出概率、置信区间、波动率
- **术数易学参谋**：梅花易数 / 奇门遁甲起卦，体用生克分析
- **巴菲特视角**：6大心智模型 + 8条决策启发式
- **实时数据**：上证指数、融资融券、北向资金、新闻政策分析
- **时空校准**：农历节气、黄历宜忌、预期差监控
- **移动端适配**：PWA 支持，手机浏览器打开即用，可添加到桌面

## 项目结构

```
├── app.py                  # Flask Web 服务
├── templates/index.html    # 移动端页面
├── static/                 # 前端资源 (CSS/JS/PWA)
├── decision_system.py      # 命令行版
├── skill_manager.py        # Skill 调度中心
├── iching_skill.py         # 梅花易数
├── qimen_skill.py          # 奇门遁甲
├── buffett_skill.py        # 巴菲特视角
├── real_data_collector.py  # 真实行情采集
├── news_monitor.py         # 新闻政策监听
├── run.sh                  # 一键启动
└── share.sh                # ngrok 分享
```

## 免责声明

仅供研究参考，不构成投资建议。市场有风险，决策需谨慎。
