# Harness Agent 系统

基于 Anthropic 三 Agent 架构的 Harness（驾驭工程）框架实现。

## 核心概念

**Harness（驾驭工程）** 是一种 AI Agent 工程方法论，旨在为 AI 智能体构建一套完整的运行环境、治理机制和安全保障体系。

### 三 Agent 协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Harness Controller                        │
│                      （驾驭控制器）                           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Initializer │    │   Generator   │    │   Evaluator   │
│   （初始化器）  │    │   （生成器）    │    │   （评估器）   │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ 理解任务       │    │ 执行任务       │    │ 定义验收标准   │
│ 分解功能       │    │ 自测          │    │ 验证提交      │
│ 协商契约       │    │ 提交          │    │ 要求修复      │
│ 规划 Sprint    │    │ 修复          │    │ 确认完成      │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 核心机制

| 机制 | 说明 |
|:---|:---|
| **外部记忆** | 使用文件系统持久化状态，替代上下文窗口记忆 |
| **任务分解** | 将大任务分解为可验证的功能单元 |
| **契约协商** | Generator 和 Evaluator 事先达成一致 |
| **上下文压缩** | 定期总结和精简上下文 |
| **反馈循环** | Evaluator 发现问题，Generator 修复 |

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
import os
import openai
from harness_system import HarnessController

# 配置 LLM 客户端
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 创建 Harness 控制器
controller = HarnessController(
    project_path="./my_project",
    project_name="我的项目",
    llm_client=client
)

# 运行任务
result = controller.run("帮我构建一个用户管理系统")
```

## 项目结构

```
harness_system/
├── __init__.py              # 主入口
├── harness_base.py          # 基础类和接口
├── memory_system.py         # 外部记忆系统
├── context_manager.py       # 上下文管理器
├── harness_controller.py    # 驾驭控制器
├── agents/
│   ├── __init__.py
│   ├── initializer.py       # 初始化器 Agent
│   ├── generator.py         # 生成器 Agent
│   └── evaluator.py         # 评估器 Agent
└── examples/
    └── example_usage.py     # 使用示例
```

## 核心组件

### 1. ExternalMemory（外部记忆系统）

```python
from harness_system import ExternalMemory

memory = ExternalMemory("./project")
memory.initialize_project("项目名", "项目描述")

# 添加功能
feature = Feature(
    id="f001",
    name="用户注册",
    description="实现用户注册功能"
)
memory.add_feature(feature)

# 获取完整上下文
context = memory.get_full_context()
```

### 2. ContextManager（上下文管理器）

```python
from harness_system import ContextManager

ctx = ContextManager()

# 构建任务上下文
context = ctx.build_task_context(
    task_description="任务描述",
    project_state="项目状态",
    feature={"name": "功能名"}
)

# 检查 token 使用
usage = ctx.check_usage(context)
if usage.status == "critical":
    context = ctx._compact_context(context)
```

### 3. 三 Agent 协作

```python
# 初始化器分解任务
init_result = initializer.initialize_project("项目名", "用户需求")

# 生成器执行功能
gen_result = generator.execute_feature(feature, contract)

# 评估器验证
eval_result = evaluator.evaluate_submission(feature, submission, contract)

if not eval_result["approved"]:
    # 处理修订
    fix_result = generator.handle_evaluator_feedback(eval_result)
```

## 工作流程

1. **初始化阶段**
   - Initializer 分析用户需求
   - 将任务分解为功能单元
   - 定义验收标准

2. **契约协商**
   - Generator 说明承诺
   - Evaluator 定义要求
   - 双方达成契约

3. **执行阶段**
   - Generator 一次执行一个功能
   - 每个功能进行自测
   - 提交给 Evaluator

4. **评估阶段**
   - Evaluator 严格验证
   - 通过则放行
   - 失败则要求修复（最多 3 次）

5. **完成阶段**
   - 功能标记为完成
   - 进入下一个功能
   - 循环直到所有功能完成

## 外部记忆文件

`.harness/` 目录结构:

```
.harness/
├── feature_list.json      # 功能清单
├── progress_log.json      # 操作日志
├── state.json             # 当前状态
├── contracts/             # 契约存储
│   ├── {contract_id}.json
│   └── ...
└── context_archive/        # 上下文归档
    ├── {feature_id}_20260101_120000.txt
    └── ...
```

## 配置

### ContextManager 配置

```python
from harness_system import ContextManager, ContextWindow

config = ContextWindow(
    max_tokens=120000,        # 最大 token 数
    warning_threshold=0.8,    # 警告阈值
    critical_threshold=0.95,  # 严重阈值
    compression_ratio=0.5     # 压缩比
)

ctx = ContextManager(config)
```

## 参考资料

- [Anthropic: Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [Building Effective AI Coding Agents for the Terminal](https://arxiv.org/abs/OPENDEV)
