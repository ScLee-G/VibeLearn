# 基金分析系统（增强版）

> VibeLearn Level 2 实践项目 - 每日市场基金涨跌分析 + 多策略回测 + 资产配置建议

---

## ✨ 核心能力

| 模块 | 说明 | 技术要点 |
|-----|-----|---------|
| **技术指标** | 多因子信号生成 | MA5/10/20/60、RSI(14)、MACD、波动率、最大回撤、夏普比 |
| **策略回测** | 4 种经典策略对比 | 双均线穿越 / RSI 均值回归 / 动量 / 定投 |
| **持仓诊断** | 基于用户成本价 | 浮盈/浮亏分析、结合信号给出加仓/减仓建议 |
| **资产配置** | 5 档风险水平 | 保守/稳健/平衡/进取/激进 - 自动推荐组合 |
| **历史数据** | GBM 几何布朗运动 | 按基金类型设置不同漂移/波动参数，保证离线可运行 |
| **性能指标** | 完整评估体系 | 总收益/年化/胜率/最大回撤/夏普比/超额收益 |
| **输出** | 可视化 + 结构化 | ASCII Sparkline、Markdown 表格、JSON 导出 |

---

## 🚀 快速开始

### 1. 直接运行完整分析

```bash
cd practice/level2_intermediate/fund_analyzer
python fund_analyzer_advanced.py
```

输出将包含：
- 📊 所有基金的技术指标摘要表
- 🔬 对第一只基金执行 4 种策略回测对比
- ⭐ 综合评分后的 TOP5 推荐基金
- 🧾 个性化持仓诊断（如在 `fund_config.py` 中填写了 `MY_HOLDINGS`）
- 🎯 资产配置建议（默认"平衡"风险水平）
- 📁 详细数据 JSON 导出

### 2. 运行完整示例集

```bash
python examples/example_advanced.py
```

包含 5 个独立示例：
1. 单只基金的完整技术指标分析
2. 多策略回测对比（4 种策略）
3. 动量策略窗口期敏感性分析
4. 完整分析系统调用
5. 5 档风险水平的资产配置对比

### 3. Python API 用法

```python
from fund_analyzer_advanced import (
    AdvancedFundAnalyzer,
    TechnicalAnalyzer,
    BacktestEngine,
    MovingAverageCrossoverStrategy,
)

# 方式 A：一键完整分析
analyzer = AdvancedFundAnalyzer(
    user_holdings={
        "161725": {"name": "招商中证白酒", "position": 15.0, "cost": 1.25},
    }
)
analyzer.load_and_analyze()

# 输出各类报告
print(analyzer.format_tech_table())
print(analyzer.format_top_picks(top_n=5))
print(analyzer.format_holding_diagnosis())
print(analyzer.format_portfolio_advice(risk_level="平衡"))

# 方式 B：自定义策略回测
profile = TechnicalAnalyzer.analyze_profile(
    AdvancedFundAnalyzer().data_source.generator.generate(
        "005827", "易方达蓝筹精选", "混合型", days=180
    )
)
engine = BacktestEngine()
result = engine.run(profile, MovingAverageCrossoverStrategy())
print(f"均线穿越策略总收益: {result.total_return:+.2f}%")
print(f"净值曲线: {result.equity_curve}")
```

---

## 📐 技术指标详解

### 均线系统 (Moving Average)

| 周期 | 作用 | 信号解读 |
|-----|------|---------|
| MA5 | 短期趋势 | 价格 > MA5 表示短期强势 |
| MA20 | 中期趋势 | 20 日均线作为多空分界 |
| MA60 | 长期趋势 | 价格 > MA60 表示长周期仍处于上升通道 |

### RSI (相对强弱指数)

| RSI 值区间 | 解读 | 建议操作 |
|-----------|------|---------|
| < 30 | 超卖 | 买入信号 |
| 30 - 70 | 正常区间 | 持有观察 |
| > 70 | 超买 | 考虑减仓 |

### MACD (指数平滑异同移动平均)

- **MACD 线 > 信号线**：多头排列，潜在买入
- **MACD 线 < 信号线**：空头排列，潜在卖出
- **MACD 线 > 0 且上穿信号**：强势金叉

### 夏普比率 (Sharpe Ratio)

衡量风险调整后收益：
> Sharpe = (年化收益率 - 无风险利率) / 年化波动率

| 夏普比 | 评价 |
|-------|-----|
| < 0 | 亏损 |
| 0 - 1 | 一般 |
| 1 - 2 | 良好 |
| > 2 | 优秀 |

---

## 🎮 策略说明

### 1. 均线穿越策略 (MA5 vs MA20)
- **原理**：短期均线上穿长期均线为金叉，代表动量反转
- **买入**：MA5 从下方上穿 MA20
- **卖出**：MA5 从上方下穿 MA20
- **适用**：震荡市中表现较好

### 2. 均值回归策略 (RSI 30/70)
- **原理**：价格偏离均值过远时将向均值回归
- **买入**：RSI < 30
- **卖出**：RSI > 70
- **适用**：横盘震荡型基金

### 3. 动量策略 (20日动量)
- **原理**：强者恒强，追涨杀跌
- **买入**：过去 20 日涨幅 > 3%
- **卖出**：过去 20 日跌幅 > 5%
- **适用**：趋势强、动量稳定的基金

### 4. 定投策略 (每 20 天)
- **原理**：定期定额，摊薄成本
- **买入**：固定周期买入
- **卖出**：一般不主动卖出
- **适用**：长期投资、非专业投资者

---

## 🧪 回测引擎参数

| 参数 | 默认值 | 说明 |
|-----|-------|-----|
| 初始资金 | 10,000 元 | 标准单位 |
| 交易滑点 | 0.1% | 模拟真实买卖价差 |
| 手续费 | 0.05% | 模拟基金申购赎回费 |
| 仓位规则 | 每次动用 90% 可用资金 | 简化满仓交易 |
| 回测期 | 180 个交易日 | 约 7 个月 |

---

## 🎯 综合信号机制

信号得分 = 均线位置 + 均线排列 + RSI 区间 + MACD 方向 + 回撤修正

| 得分区间 | 信号 | 操作建议 |
|---------|------|---------|
| ≥ 4 | 强买 | 可积极建仓 |
| 1.5 ~ 4 | 买入 | 分批建仓 |
| -0.5 ~ 1.5 | 观望 | 持有观察 |
| -2.5 ~ -0.5 | 减仓 | 分批卖出 |
| < -2.5 | 强卖 | 考虑离场 |

---

## 📊 资产配置模板

| 风险等级 | 债券型 | 指数型 | 混合型 | 股票型 | 适合人群 |
|--------|-------|-------|-------|-------|--------|
| 保守 | 60% | 20% | 20% | 0% | 退休人员、低风险偏好 |
| 稳健 | 40% | 30% | 25% | 5% | 中老年投资者 |
| 平衡 | 25% | 35% | 25% | 15% | 大多数投资者 |
| 进取 | 10% | 35% | 30% | 25% | 中青年、有投资经验 |
| 激进 | 0% | 30% | 30% | 40% | 高风险偏好、长期投资 |

---

## 🏗️ 项目结构

```
fund_analyzer/
├── README.md                      # 本文档
├── requirements.txt               # 依赖
├── fund_analyzer.py               # 基础版（保留兼容）
├── fund_analyzer_advanced.py      # ✨ 增强版主程序
├── fund_config.py                 # 用户配置（基金池 + 持仓）
├── scheduled_task.py              # 定时任务（可接入增强版）
├── examples/
│   ├── example_usage.py           # 基础版示例
│   └── example_advanced.py        # ✨ 增强版示例集合
└── outputs/
    └── fund_advanced_report.json  # 运行后自动导出 JSON
```

---

## 🔧 定时任务接入增强版

修改 `scheduled_task.py` 中的 `send_report` 方法：

```python
from fund_analyzer_advanced import run_full_analysis

def send_report(self):
    report = run_full_analysis(
        codes=MY_FUND_LIST,
        user_holdings=MY_HOLDINGS,
        risk_level="平衡",
        top_n=5,
    )
    # ... 邮件/微信推送逻辑
```

启动定时任务：
```bash
python scheduled_task.py --hour 14 --minute 40
```

---

## ⚠️ 注意事项

1. **模拟数据**：当前版本使用几何布朗运动（GBM）模拟价格数据，保证离线可运行。真实市场结果将不同
2. **回测过拟合**：历史表现不代表未来，请多策略对比，避免过度拟合历史
3. **风险提示**：所有信号和建议仅供参考，投资有风险，请根据自身风险承受能力决策
4. **真实数据接入**：真实基金数据源可通过天天基金网 / 东方财富接口替换 `MockHistoryGenerator`

---

## 💡 学习要点（Level 2）

本项目完整覆盖以下工程化实践：

- **时间序列分析**：金融数据处理、技术指标公式实现
- **策略模式 (Strategy Pattern)**：可插拔的策略设计，便于扩展
- **回测引擎设计**：滑点、手续费、仓位管理的正确建模
- **投资组合理论**：简化版资产配置的工程实现
- **可复现性**：随机种子管理、离线运行能力
- **数据结构设计**：清晰分离数据层 / 分析层 / 策略层 / 输出层

---

## 📚 推荐拓展阅读

- 《主动投资组合管理》- Richard C. Grinold
- 《量化投资策略》- Ernie Chan
- Python 金融分析库：`pandas`, `numpy`, `backtrader`, `zipline`

---

## 🎯 下一步可扩展

- [ ] 接入真实基金数据 API（天天基金、东方财富）
- [ ] 增加更多技术指标（布林带、KDJ、OBV）
- [ ] 增加机器学习策略（LSTM 价格预测、强化学习）
- [ ] 支持多资产组合回测（多基金同时交易）
- [ ] 增加邮件 / 微信 / 钉钉推送
- [ ] 网页版可视化图表（Matplotlib / Plotly）
