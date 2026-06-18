# VibeLearn

> AI 应用开发学习平台

## 🎯 项目简介

本仓库是一个系统化的 **VibeLearn（智能编程能力成长平台）**，旨在帮助开发者系统性地掌握大语言模型（LLM）在编程领域的应用。通过从基础到高级的学习路径，你将从 API 调用入门，逐步构建 Agent 系统，最终成长为 AI 应用开发专家。

## 📚 学习框架

### 学习路径概览

| 阶段 | 名称 | 难度 | 预计时长 | 核心能力 |
|:---:|:---:|:---:|:---:|:---|
| **Level 1** | 入门探索 | ⭐⭐☆ | 2-3 周 | LLM API 调用、Prompt 工程基础 |
| **Level 2** | 进阶实践 | ⭐⭐⭐ | 3-4 周 | Agent 架构设计、代码生成 |
| **Level 3** | 高级应用 | ⭐⭐⭐⭐ | 4-6 周 | RAG 系统、复杂工作流编排 |

### 技术演进时间线（2023-2025）

| 阶段 | 时间 | 特点 | 代表技术 |
|:---:|:---:|:---|:---|
| **Phase 1** | 2023 | 过度迷信模型微调，崇尚行业垂直大模型 | 垂直领域微调 |
| **Phase 2** | 2024 | 明确了 RAG、Agent 的核心地位 | RAG、Agent、GPT |
| **Phase 3** | 2025 | Qwen、DeepSeek 胜任 AI 应用，技术路线形成成熟方法论 | 多模型兼容、商业化落地 |

## 📁 目录结构

```
.
├── theory/                           # 理论学习
│   ├── llm_fundamentals/            # LLM 基础原理
│   ├── agent_principles/            # Agent 架构原理
│   ├── rag_techniques/              # RAG 技术体系
│   └── theory_guide.md              # 理论指南汇总
├── practice/                         # 实践项目
│   ├── level1_basic/                # 入门级项目
│   │   └── README.md
│   ├── level2_intermediate/         # 进阶级项目
│   │   ├── financial_news/          # 📰 金融新闻智能简报系统
│   │   │   ├── financial_news.py           # 基础版
│   │   │   └── financial_news_advanced.py  # 增强版（规则引擎 + 去重 + LLM 摘要）
│   │   └── fund_analyzer/           # 📊 基金分析与策略回测系统
│   │       ├── fund_analyzer.py            # 基础版
│   │       └── fund_analyzer_advanced.py   # 增强版（技术指标 + 多策略回测 + 资产配置）
│   └── level3_advanced/            # 高级项目
│       ├── harness_system/          # 🎯 Harness 驾驭系统（三 Agent 协作）
│       │   ├── harness_controller.py       # 基础版
│       │   └── harness_advanced.py         # 增强版（Skill 路由 + 记忆沉淀 + 上下文压缩）
│       ├── multimodal_rag.py        # 🧠 多模态 RAG 知识库问答系统（新增）
│       └── minicode_agent.py        # 🤖 MiniCode AI 编码 Agent（参考 Claude Code 架构）
├── resources/                        # 学习资源
│   ├── AIConcepts_BusinessAnalysis.md
│   ├── agent_task_decomposition.md
│   └── career_guide.md
├── learning_paths/                   # 学习路径规划
│   ├── learning_path.md             # 阶段规划
│   └── skill_matrix.md              # 技能矩阵
└── README.md
```

## 🎓 学习路径

### Level 1: 入门探索（2-3 周）

**目标**：掌握 LLM API 调用和基础 Prompt 工程

**核心能力**：
- LLM 基础概念与原理
- OpenAI API 使用方法
- Prompt 工程基础技巧

**实践项目**：聊天机器人、文本分类器、代码补全工具

---

### Level 2: 进阶实践（3-4 周）

**目标**：掌握 Agent 架构设计和 AI 代码生成

**核心能力**：
- Agent 核心组件（Prompt、LLM、工作流、代码执行）
- 任务拆解与规划
- AI 代码生成技术
- 规则引擎与关键词评分
- 数据清洗与去重策略
- 增量缓存机制设计

**实践项目**：

| 项目 | 核心模块 | 文件 |
|------|---------|-----|
| 📰 金融新闻智能简报系统 | 多源聚合、规则引擎、去重器、LLM 摘要、Markdown 输出 | `practice/level2_intermediate/financial_news/financial_news_advanced.py` |
| 📊 基金分析与策略回测系统 | 技术指标、4 策略回测引擎、资产配置、JSON 导出 | `practice/level2_intermediate/fund_analyzer/fund_analyzer_advanced.py` |
| 🤖 智能代码生成器 | Python 代码模板、规则审查 | `practice/level2_intermediate/fund_analyzer/fund_analyzer.py` |
| ⚙️ 自动化工作流 | 定时任务、增量更新 | `practice/level2_intermediate/fund_analyzer/scheduled_task.py` |

---

### Level 3: 高级应用（4-6 周）

**目标**：掌握 RAG 和复杂 Agent 系统架构

**核心能力**：
- RAG 检索增强生成（文档解析、切分、混合检索、Rerank）
- 向量数据库与稀疏检索融合
- Skill 分层路由与任务分解
- Agent 自进化记忆（程序化经验 + 情景记忆）
- 分层上下文压缩（外部化 + 占位符 + 摘要）
- 中心化多 Agent 协作（权限控制、工具约束）
- AI 风险分类与安全审查
- RAGAS 风格的检索与生成质量评估

**实践项目**：

| 项目 | 架构思想 | 核心模块 | 文件 |
|------|---------|---------|-----|
| 🎯 Harness 驾驭系统 | 三 Agent 协作、契约式编程 | Initializer/Generator/Evaluator、Sprint 机制 | `practice/level3_advanced/harness_system/harness_advanced.py` |
| 🤖 MiniCode Agent | 参考 Claude Code 架构 | Skill 路由、自进化记忆、上下文压缩、多 Agent 权限 | `practice/level3_advanced/minicode_agent.py` |
| 🧠 多模态 RAG 知识库问答 | 检索增强生成 | 多格式解析、语义切分、BM25+向量混合检索、RAGAS 评估 | `practice/level3_advanced/multimodal_rag.py` |
| 📚 知识库问答系统 | 企业文档问答 | 增量索引、多路召回、上下文拼装 | `practice/level3_advanced/harness_system/harness_controller.py` |

---

## 📚 核心概念速览

| 概念 | 说明 |
|:---|:---|
| **RAG** | 检索增强生成，让 LLM 基于知识库回答 |
| **Function Call** | LLM 调用外部工具/函数的能力 |
| **MCP** | 模型上下文协议，标准化工具交互 |
| **Skill** | 面向任务的技能组合，解决复杂问题 |

📚 **详细解释**：[理论指南](theory/theory_guide.md)

---

## 💼 职业发展

### 2025年 AI 人才趋势
- AI 产品经理岗位需求爆发
- 产品经理岗位占比位居第二
- AI 高薪岗位：50-80K

### 职业转型路径
```
产品经理 ──→ AI 产品经理    测试 ──→ AI 产品测试
销售     ──→ AI 产品销售    运营   ──→ AI 产品运营
```

📚 **详细内容**：[职业发展与转型指南](resources/career_guide.md)

---

## 🛠️ 技术栈

| 类型 | 技术 |
|:---|:---|
| **语言模型** | GPT-4、DeepSeek-V3、Qwen |
| **框架** | LangChain、OpenAI SDK |
| **向量数据库** | Pinecone、Chroma、Milvus |
| **代码执行** | Python exec、Jupyter |
| **数据处理** | Pandas、NumPy |

---

## 📊 难度评估体系

| 维度 | 权重 | 说明 |
|:---|:---:|:---|
| **概念理解** | 30% | 对核心概念的理解难度 |
| **代码复杂度** | 30% | 实现代码的复杂程度 |
| **调试难度** | 25% | 排查问题的难度 |
| **创新性** | 15% | 需要创新思维的程度 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
