# Harness Agent 系统

基于 Anthropic 三 Agent 架构的 Harness（驾驭工程）框架实现。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /workspace/practice/level3_advanced/harness_system
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# 设置 API Key（必须）
export OPENAI_API_KEY=your_api_key

# 可选：设置 API Base URL（使用其他模型时）
export OPENAI_BASE_URL=https://api.deepseek.com
```

### 3. 运行系统

#### 方式一：直接运行任务（推荐）

```bash
python run_harness.py "帮我创建一个待办事项 Web 应用"
```

#### 方式二：交互模式

```bash
python run_harness.py --interactive
```

#### 方式三：运行演示

```bash
python demo.py
```

## 📖 使用方法

### 基本用法

```bash
# 标准用法
python run_harness.py "你的任务描述"

# 指定项目名称
python run_harness.py --project my_project "构建用户管理系统"

# 交互模式
python run_harness.py --interactive
```

### 性能优化选项

```bash
# 自定义资源限制
python run_harness.py --max-memory 85.0 --max-cpu 90.0 "任务"

# 禁用资源监控（减少开销
python run_harness.py --no-resource-monitor "任务"

# 修改超时时间
python run_harness.py --timeout 600 "任务"
```

详见 [PERFORMANCE.md](./PERFORMANCE.md) 完整优化指南。

### Python API

```python
import openai
from harness_system import HarnessController

# 创建客户端
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 创建控制器（带性能配置）
controller = HarnessController(
    project_path="./my_project",
    project_name="我的项目",
    llm_client=client,
    
    # 性能配置
    enable_resource_monitoring=True,  # 启用资源监控
    max_memory_percent=90.0,         # 内存使用上限 90%
    max_cpu_percent=95.0,            # CPU使用上限 95%
    feature_timeout_seconds=300        # 功能超时时间 5分钟
)

# 运行任务
result = controller.run("帮我构建一个用户管理系统")

# 查看结果
print(f"完成率: {result['final_status']['completion_rate']:.1%}")

# 获取性能报告
perf_report = controller.get_performance_report()
```

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Harness Controller                        │
│                      （驾驭控制器）                           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
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

## 📁 项目结构

```
harness_system/
├── __init__.py              # 主入口
├── run_harness.py           # 命令行入口
├── demo.py                  # 演示脚本
├── harness_base.py          # 基础类
├── memory_system.py         # 外部记忆系统
├── context_manager.py       # 上下文管理器
├── harness_controller.py    # 驾驭控制器
├── agents/
│   ├── __init__.py
│   ├── initializer.py       # 初始化器 Agent
│   ├── generator.py         # 生成器 Agent
│   └── evaluator.py         # 评估器 Agent
├── examples/
│   └── example_usage.py     # 使用示例
├── README.md                # 本文档
└── requirements.txt         # 依赖
```

## 🔧 配置选项

### LLM 模型配置

```python
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    # 支持: deepseek-chat, gpt-4, gpt-3.5-turbo 等
)
```

### 上下文管理器配置

```python
from harness_system import ContextManager, ContextWindow

config = ContextWindow(
    max_tokens=120000,        # 最大 token 数
    warning_threshold=0.8,    # 警告阈值
    critical_threshold=0.95,   # 严重阈值
    compression_ratio=0.5      # 压缩比
)

ctx = ContextManager(config)
```

## 📊 工作流程

```
用户请求
    │
    ▼
┌─────────────────┐
│  Initializer    │ ◄── 分解任务、协商契约
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generator      │ ◄── 执行任务、自测、提交
└────────┬────────┘
         │ 提交
         ▼
┌─────────────────┐
│  Evaluator      │ ◄── 验证、要求修复
└────────┬────────┘
         │ 通过？
    ┌────┴────┐
    │         │
   是        否
    │         │
    ▼         ▼
┌───────┐ ┌─────────────┐
│ 完成  │ │ 返回修复    │
└───┬───┘ └──────┬──────┘
    │            │
    │      ◄────┘
    │
    ▼ (下一个功能)
```

## 📝 示例任务

### 1. 简单计算任务

```bash
python run_harness.py "计算 1 到 100 的所有质数之和"
```

### 2. 数据处理任务

```bash
python run_harness.py "分析 sales.csv，生成月度销售报告"
```

### 3. Web 应用开发

```bash
python run_harness.py "创建一个待办事项 Web 应用，支持增删改查"
```

### 4. 复杂项目

```bash
python run_harness.py --project blog_system "构建博客系统：用户注册、文章发布、评论、标签分类"
```

## 🔍 查看项目状态

```bash
# 交互模式中输入 status
python run_harness.py --interactive
>>> status

# 或者直接在 Python 中
from harness_system import ExternalMemory
memory = ExternalMemory("./my_project")
print(memory.get_full_context())
```

## 📦 外部记忆文件

运行后会在项目目录创建 `.harness/` 文件夹：

```
projects/my_project/.harness/
├── feature_list.json      # 功能清单
├── progress_log.json      # 操作日志
├── state.json            # 当前状态
├── contracts/            # 契约存储
│   └── {contract_id}.json
└── context_archive/       # 上下文归档
    └── {feature_id}_*.txt
```

## ❓ 常见问题

### Q: 需要 API Key 吗？

**A**: 是的，需要设置 `OPENAI_API_KEY` 环境变量。支持 DeepSeek、OpenAI 等兼容 API。

### Q: 支持哪些模型？

**A**: 支持所有 OpenAI 兼容的模型，只需修改 base_url。

### Q: 如何调试？

**A**: 查看项目目录下的 `.harness/progress_log.json` 获取详细日志。

### Q: 任务失败怎么办？

**A**: Harness 支持最多 3 次自动修复，如果仍然失败会暂停等待人工介入。

## 📚 参考资料

- [Anthropic: Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [Building Effective AI Coding Agents for the Terminal](https://arxiv.org/abs/OPENDEV)
