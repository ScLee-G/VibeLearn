# Level 2: 进阶实践

## 学习目标

- 掌握 Agent 架构设计
- 理解 AI 代码生成技术
- 能够构建中等复杂度的 AI 应用

## 预计学习时长

3-4 周

## 难度评估

| 指标 | 评分 |
|:---|:---:|
| 概念理解 | ⭐⭐⭐ |
| 代码复杂度 | ⭐⭐☆ |
| 调试难度 | ⭐⭐☆ |
| 创新性 | ⭐⭐☆ |

## 理论学习

在开始实践项目前，建议先学习相关理论：
- [Agent 架构原理](../../theory/agent_principles/README.md)
- [理论学习指南](../../theory/theory_guide.md)

## 实践项目

### 项目 1: 数据处理 Agent

**目标**：实现一个自动化数据处理 Agent，通过 AI 生成代码并执行

**技术要点**：
- 地址转经纬度（通过 LLM
- Excel 数据处理
- 距离计算（Haversine 公式）
- 代码生成与执行

**文件**：
- [agent_workflow.py](agent_workflow.py) - 核心工作流
- [create_sample_excel.py](create_sample_excel.py) - 创建示例数据
- sites_geocoded.xlsx - 示例数据（运行 create_sample_excel.py 生成

**使用方法**：
1. 先运行 `python create_sample_excel.py` 生成示例数据
2. 然后运行 `python agent_workflow.py <地址> <城市>` 来执行数据处理

---

## 学习资源

1. [LangChain 官方文档](https://python.langchain.com/)
2. [Agent 架构原理](../../theory/agent_principles/README.md)
3. [理论学习指南](../../theory/theory_guide.md)

## 下一步

完成 Level 2 后，继续到 [Level 3: 高级应用](../level3_advanced/README.md) 学习 RAG 和多 Agent 系统。