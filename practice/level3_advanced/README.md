# Level 3: 高级应用

## 学习目标

- 掌握多 Agent 协作架构
- 理解复杂 AI 系统设计
- 能够构建企业级 AI 应用

## 预计学习时长

4-6 周

## 难度评估

| 指标 | 评分 |
|:---|:---:|
| 概念理解 | ⭐⭐⭐⭐ |
| 代码复杂度 | ⭐⭐⭐ |
| 调试难度 | ⭐⭐⭐⭐ |
| 创新性 | ⭐⭐⭐ |

## 理论学习

在开始实践项目前，建议先学习相关理论：
- [RAG 技术体系](../../theory/rag_techniques/README.md)
- [Agent 架构原理](../../theory/agent_principles/README.md)
- [理论学习指南](../../theory/theory_guide.md)

## 实践项目

### 项目 1: Harness Agent 系统（多 Agent 协作）

**目标**：基于 Anthropic 三 Agent 架构，构建一个完整的多 Agent 协作系统，实现任务的智能分解、执行和验证

**技术要点**：
- 三 Agent 协作架构（Initializer / Generator / Evaluator）
- 任务拆解与 Sprint 规划
- 代码生成与执行验证
- 外部记忆系统
- 资源监控与性能优化

**文件**：
- [harness_system/README.md](harness_system/README.md) - 项目主文档
- [harness_system/SETUP.md](harness_system/SETUP.md) - 前置准备指南
- [harness_system/PERFORMANCE.md](harness_system/PERFORMANCE.md) - 性能优化指南
- [harness_system/run_harness.py](harness_system/run_harness.py) - 主程序入口
- [harness_system/harness_controller.py](harness_system/harness_controller.py) - 控制器
- [harness_system/agents/](harness_system/agents/) - Agent 实现

**快速开始**：
```bash
cd harness_system
pip install -r requirements.txt
python run_harness.py --precheck  # 检查环境
python run_harness.py "帮我创建一个待办事项 Web 应用"  # 运行任务
```

---

### 项目 2: 多 Agent 代码审查系统

**目标**：构建一个基于多 Agent 协作的自动化代码审查系统，包含逻辑审查、安全审查和风格审查

**技术要点**：
- 多 Agent 并行协作模式
- 代码逻辑审查
- 安全漏洞检测
- PEP 8 代码风格检查
- 审查报告汇总

**文件**：
- [code_review_system/README.md](code_review_system/README.md) - 项目文档
- [code_review_system/main.py](code_review_system/main.py) - 主程序入口
- [code_review_system/review_controller.py](code_review_system/review_controller.py) - 审查控制器
- [code_review_system/code_review_agent.py](code_review_system/code_review_agent.py) - 逻辑审查 Agent
- [code_review_system/security_agent.py](code_review_system/security_agent.py) - 安全审查 Agent
- [code_review_system/style_agent.py](code_review_system/style_agent.py) - 风格审查 Agent
- [code_review_system/summarizer_agent.py](code_review_system/summarizer_agent.py) - 报告汇总 Agent

**快速开始**：
```bash
cd code_review_system
pip install openai
python main.py -f your_code.py  # 审查代码文件
python main.py -p -f your_code.py  # 并行审查模式
```

---

### 项目 3: 多 Agent 任务分工系统

**目标**：构建一个智能任务分配和执行系统，实现任务拆解、执行和监控的全流程管理

**技术要点**：
- 任务拆解与依赖分析
- 智能任务分配
- 并行任务执行
- 任务进度监控
- 风险识别与优化建议

**文件**：
- [task_assignment_system/README.md](task_assignment_system/README.md) - 项目文档
- [task_assignment_system/main.py](task_assignment_system/main.py) - 主程序入口
- [task_assignment_system/task_coordinator.py](task_assignment_system/task_coordinator.py) - 任务协调器
- [task_assignment_system/task_decomposer.py](task_assignment_system/task_decomposer.py) - 任务拆解 Agent
- [task_assignment_system/task_executor.py](task_assignment_system/task_executor.py) - 任务执行 Agent
- [task_assignment_system/task_monitor.py](task_assignment_system/task_monitor.py) - 任务监控 Agent

**快速开始**：
```bash
cd task_assignment_system
pip install openai
python main.py "帮我创建一个博客网站"  # 执行任务
python main.py -p "复杂任务描述"  # 并行执行模式
```

## 学习资源

1. [RAG 技术体系](../../theory/rag_techniques/README.md)
2. [Agent 架构原理](../../theory/agent_principles/README.md)
3. [理论学习指南](../../theory/theory_guide.md)
4. [Harness Agent 系统文档](harness_system/README.md)
5. [代码审查系统文档](code_review_system/README.md)
6. [任务分工系统文档](task_assignment_system/README.md)

## 下一步

完成 Level 3 后，你已掌握 AI 应用开发的核心技能！查看 [职业发展指南](../../resources/career_guide.md) 了解 AI 时代的职业机会。