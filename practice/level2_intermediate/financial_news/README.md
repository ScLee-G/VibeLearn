# 金融新闻智能助手（增强版）

> 每天自动获取并分析最新金融新闻，重点关注可能影响市场的内容。
> **V2 增强版：多源聚合 + 规则引擎 + 可选 LLM 摘要 + 增量缓存**

---

## ✨ 核心特性

| 模块 | 说明 | 技术要点 |
|-----|-----|---------|
| **数据源** | 多源聚合 | 新浪财经 RSS（可选）+ 模拟数据 + 自定义 JSON |
| **规则引擎** | 智能评分 | 关键词权重、来源加权、情绪分析、分类判断 |
| **去重器** | 内容去重 | 文本指纹 + Jaccard 相似度阈值 |
| **LLM 摘要** | AI 综述 | OpenAI/DeepSeek 兼容接口（可选） |
| **缓存机制** | 增量更新 | 按日期 JSON 缓存，减少重复拉取 |
| **输出格式** | 多格式输出 | Markdown、纯文本 |

---

## 🚀 快速开始

### 方式一：直接运行（推荐，无需配置）

```bash
cd practice/level2_intermediate/financial_news
python financial_news_advanced.py
```

### 方式二：运行示例集合

```bash
python examples/example_advanced.py
```

### 方式三：命令行自定义参数

```bash
# 尝试拉取真实数据源（无网络自动回退）
python financial_news_advanced.py --real

# 启用 LLM 摘要（需配置 LLM_API_KEY）
python financial_news_advanced.py --llm

# 纯文本输出 + 只保留 5 条核心
python financial_news_advanced.py --text --items 5

# 组合使用
python financial_news_advanced.py --real --llm --items 8
```

### 方式四：Python API

```python
from financial_news_advanced import get_morning_brief_advanced, save_brief_to_file

# 获取 Markdown 简报
brief = get_morning_brief_advanced(
    use_real_data=False,   # 尝试真实数据源
    use_llm=False,         # 使用 LLM 摘要
    max_items=10,          # 保留条数
    output_format="markdown",
)
print(brief)

# 保存到文件
save_brief_to_file(brief, "./outputs")
```

---

## 🧠 规则引擎详解

### 评分逻辑

```
重要性等级 = f(关键词命中 × 权重 × 来源加权 × 标题长度修正)

关键词权重：
  - 重大关键词（央行/降息/政治局/万亿 ...）× 3.0
  - 重要关键词（A股/财报/新能源/北向资金 ...）× 1.0

来源加权：
  - 央行/国务院/证监会：1.5
  - 新华社/人民日报：1.4
  - 财新/第一财经/华尔街见闻：1.3
  - 新浪/东财/同花顺：1.2
  - 其他：1.0
```

### 重要性分级

| 等级 | 星标 | 评分区间 | 典型场景 |
|-----|-----|---------|---------|
| 重大 | ⭐⭐⭐ | ≥ 6 | 央行政策、国务院会议、重大监管新规 |
| 重要 | ⭐⭐ | 2 ~ 6 | A股走势、行业重大新闻、公司财报 |
| 一般 | ⭐ | < 2 | 普通市场报道、券商观点 |

### 分类体系

- **宏观政策**：央行、国务院、发改委、财政部
- **证券市场**：A股、港股、IPO、证监会
- **行业动态**：新能源、AI、半导体、医药、房地产
- **公司新闻**：财报、业绩、重组、并购
- **国际市场**：美联储、欧央行、汇率、原油、黄金
- **大宗商品**：原油、黄金、铜、铁矿石

---

## 🤖 可选 LLM 摘要

### 配置方式

```bash
export LLM_API_KEY="你的API Key"
export LLM_BASE_URL="https://api.deepseek.com/v1/"   # 可选
export LLM_MODEL="deepseek-chat"                      # 可选，默认 gpt-4o-mini
```

### 使用

```bash
python financial_news_advanced.py --llm
```

### 工作原理

系统将精选新闻整理为结构化列表，发送给 LLM：
1. 概述今日最重要的 2-3 个主题
2. 指出市场影响方向（偏多/偏空/中性）
3. 语言简洁专业（200-300 字）

---

## 📊 输出示例（Markdown）

```markdown
# 📊 金融晨报 | 2026-06-18

**市场脉搏**：整体偏积极，利好消息占优

**今日关键词**：央行、A股、新能源、美联储、财报

## 📋 今日概览
- 原始新闻数：14 条
- 精选简报数：10 条
- 分类分布：
  - 宏观政策：3 条
  - 证券市场：2 条
  - 行业动态：2 条
  - 国际市场：2 条
  - 大宗商品：2 条

## 🔥 重点新闻

### 1. ⭐⭐⭐ 央行公布最新LPR报价... 🟢
> 来源：央行官网 | 时间：2026-06-18 09:15 | 分类：宏观政策
> 关键词：央行、LPR
> 评分：12.50 | 情绪：+0.25

中国人民银行授权全国银行间同业拆借中心公布贷款市场报价利率（LPR）...
```

---

## 🏗️ 项目结构

```
financial_news/
├── README.md                       # 本文档
├── requirements.txt                # 依赖（仅 requests 为可选依赖）
├── financial_news.py               # 旧版主程序（保留兼容）
├── financial_news_advanced.py      # ✨ 增强版主程序（推荐使用）
├── examples/
│   ├── example_usage.py            # 旧版示例
│   └── example_advanced.py         # ✨ 增强版示例集合
└── .news_cache/                    # 自动生成：每日缓存
    ├── news_20260618.json
    └── ...
```

---

## 💡 学习要点（Level 2）

本项目完整覆盖以下 Agent 开发技能：

| 技能点 | 实现位置 |
|-------|---------|
| **数据获取** | `NewsDataProvider` 类，多源聚合与回退策略 |
| **数据清洗** | `DuplicateFilter` 去重器，文本指纹 + Jaccard |
| **规则引擎** | `RuleEngine` 类，关键词/权重/情绪评分 |
| **可选 LLM** | `LLMSummarizer` 类，OpenAI/DeepSeek 兼容 |
| **缓存机制** | `NewsCache` 类，按日增量缓存 |
| **格式化输出** | `BriefBuilder` 类，多策略多格式 |
| **命令行接口** | `__main__` 段，argparse 风格参数 |
| **向后兼容** | 保留 `get_morning_brief()` 旧接口 |

---

## ⚠️ 注意事项

1. **数据源**：真实 RSS 源可能因网络、反爬等原因不可用，系统设计了自动回退机制
2. **LLM 摘要**：为可选功能，未配置 API Key 时自动跳过，不影响核心流程
3. **模拟数据**：默认使用模拟数据保证可运行，便于学习与调试
4. **投资参考**：所有内容仅供信息参考，不构成任何投资建议

---

## 🎯 可扩展方向

- [ ] 添加 Webhook/邮件/企业微信推送
- [ ] 集成更多财经数据源（Wind、Bloomberg 等）
- [ ] 添加用户自定义关键词订阅
- [ ] 将规则引擎替换为轻量级 ML 模型（如 TextBlob / 自研小模型）
- [ ] 添加新闻热度时序图
- [ ] 对接实际定时任务（crontab / APScheduler）
