"""
Harness Agent 系统 - Anthropic 三 Agent 架构实现

基于论文《Harness Design for Long-Running Application Development》

核心组件:
- ExternalMemory: 外部记忆系统
- ContextManager: 上下文管理器
- InitializerAgent: 初始化器（理解任务、分解功能、协商契约）
- GeneratorAgent: 生成器（执行任务、自测、提交）
- EvaluatorAgent: 评估器（验证提交、要求修复、确认完成）
- HarnessController: 驾驭控制器（协调三 Agent 协作）

使用方法:
```python
from harness_system import HarnessController

controller = HarnessController(
    project_path="./my_project",
    project_name="我的项目",
    llm_client=openai_client
)

result = controller.run("帮我构建一个用户管理系统")
```
"""

from .harness_base import (
    BaseAgent,
    AgentRole,
    TaskStatus,
    Message,
    Feature,
    Contract,
    Sprint
)
from .memory_system import ExternalMemory
from .context_manager import ContextManager, ThinkingTool
from .agents import InitializerAgent, GeneratorAgent, EvaluatorAgent
from .harness_controller import HarnessController

__version__ = "1.0.0"
__all__ = [
    "HarnessController",
    "ExternalMemory",
    "ContextManager",
    "ThinkingTool",
    "InitializerAgent",
    "GeneratorAgent",
    "EvaluatorAgent",
    "BaseAgent",
    "AgentRole",
    "TaskStatus",
    "Message",
    "Feature",
    "Contract",
    "Sprint"
]
