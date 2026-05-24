"""
上下文管理器 - Harness 核心基础设施

处理上下文的:
1. 压缩与精简
2. 渐进式披露
3. 对话历史管理
4. Token 预算控制
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class ContextWindow:
    """上下文窗口配置"""
    max_tokens: int = 120000
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
    compression_ratio: float = 0.5


@dataclass
class TokenEstimate:
    """Token 估算"""
    current_tokens: int
    max_tokens: int
    usage_ratio: float
    status: str


class ContextManager:
    """上下文管理器"""

    def __init__(self, config: Optional[ContextWindow] = None):
        self.config = config or ContextWindow()

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数量（粗略估算：中文约 2 字符/token，英文约 4 字符/token）"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        other_chars = len(text) - chinese_chars - english_chars
        return int(chinese_chars / 2 + english_chars / 4 + other_chars / 4)

    def check_usage(self, text: str) -> TokenEstimate:
        """检查 token 使用情况"""
        current = self.estimate_tokens(text)
        ratio = current / self.config.max_tokens
        status = "normal"
        if ratio >= self.config.critical_threshold:
            status = "critical"
        elif ratio >= self.config.warning_threshold:
            status = "warning"
        return TokenEstimate(
            current_tokens=current,
            max_tokens=self.config.max_tokens,
            usage_ratio=ratio,
            status=status
        )

    def compress_conversation(self, messages: list[dict], preserve_last_n: int = 5) -> list[dict]:
        """压缩对话历史，保留最近的 N 条消息和重要的系统消息"""
        if not messages:
            return []

        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]

        recent_messages = other_messages[-preserve_last_n:] if len(other_messages) > preserve_last_n else other_messages

        if len(other_messages) > preserve_last_n:
            summary = self._summarize_older_messages(other_messages[:-preserve_last_n])
            summarized_message = {
                "role": "system",
                "content": f"[早期对话摘要] {summary}"
            }
            return system_messages + [summarized_message] + recent_messages

        return system_messages + recent_messages

    def _summarize_older_messages(self, older_messages: list[dict]) -> str:
        """总结早期对话"""
        if not older_messages:
            return "无早期对话"

        action_summary = []
        for msg in older_messages[-10:]:
            content = msg.get("content", "")[:100]
            role = msg.get("role", "unknown")
            action_summary.append(f"{role}: {content}...")

        return f"共 {len(older_messages)} 条消息，主要操作: " + "; ".join(action_summary[:3])

    def progressive_disclosure(self, metadata: dict, full_content: str, max_metadata_tokens: int = 2000) -> str:
        """渐进式披露：先返回元数据，必要时返回完整内容"""
        metadata_text = self._format_metadata(metadata)
        metadata_tokens = self.estimate_tokens(metadata_text)

        if metadata_tokens <= max_metadata_tokens:
            return metadata_text + "\n\n[详细内容已加载]"

        summary = self._summarize_content(full_content)
        return metadata_text + f"\n\n[内容摘要] {summary}"

    def _format_metadata(self, metadata: dict) -> str:
        """格式化元数据"""
        lines = ["[元数据]"]
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                lines.append(f"  {key}: {len(value)} 项")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    def _summarize_content(self, content: str, max_length: int = 500) -> str:
        """总结内容"""
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    def build_task_context(
        self,
        task_description: str,
        project_state: str,
        feature: dict,
        recent_work: str = "",
        max_tokens: Optional[int] = None
    ) -> str:
        """构建任务上下文"""
        max_tokens = max_tokens or self.config.max_tokens

        context_parts = []
        context_parts.append("=" * 60)
        context_parts.append("当前任务")
        context_parts.append("=" * 60)
        context_parts.append(task_description)

        context_parts.append("\n" + "=" * 60)
        context_parts.append("项目状态")
        context_parts.append("=" * 60)
        context_parts.append(project_state)

        context_parts.append("\n" + "=" * 60)
        context_parts.append(f"当前功能: {feature.get('name', 'unknown')}")
        context_parts.append("=" * 60)
        context_parts.append(f"描述: {feature.get('description', 'N/A')}")
        context_parts.append(f"验收标准: {', '.join(feature.get('acceptance_criteria', []))}")

        if recent_work:
            context_parts.append("\n最近工作:")
            context_parts.append(recent_work)

        full_context = "\n".join(context_parts)

        usage = self.check_usage(full_context)
        if usage.status == "critical":
            return self._compact_context(full_context)
        elif usage.status == "warning":
            full_context += "\n\n[警告: 上下文接近上限，建议精简]"

        return full_context

    def _compact_context(self, context: str) -> str:
        """精简上下文"""
        lines = context.split("\n")
        important_keywords = ["任务", "功能", "状态", "验收", "标准", "描述"]

        important_lines = []
        for line in lines:
            if any(kw in line for kw in important_keywords):
                important_lines.append(line)
            elif len(line) < 80:
                important_lines.append(line)

        compacted = "\n".join(important_lines[:50])
        return compacted + "\n\n[上下文已精简，仅保留关键信息]"

    def extract_key_points(self, text: str) -> list[str]:
        """从文本中提取关键点"""
        sentences = re.split(r'[。！？\n]', text)
        key_points = []
        for s in sentences:
            if len(s) > 10 and any(kw in s for kw in ["关键", "重要", "必须", "应该", "需要"]):
                key_points.append(s.strip())
        return key_points[:10]

    def format_for_llm(self, context: str, instruction: str = "") -> list[dict]:
        """格式化为 LLM 消息格式"""
        messages = []

        if instruction:
            messages.append({
                "role": "system",
                "content": instruction
            })

        messages.append({
            "role": "user",
            "content": context
        })

        return messages


class ThinkingTool:
    """思维工具 - 模拟 Claude 的 thinking tool"""

    def __init__(self, max_thinking_tokens: int = 8000):
        self.max_thinking_tokens = max_thinking_tokens
        self.thoughts: list[dict] = []

    def think(
        self,
        problem: str,
        constraints: list[str] = None,
        plan_ahead: int = 3
    ) -> str:
        """执行逐步思考"""
        constraints = constraints or []
        thought_steps = []

        thought_steps.append(f"问题: {problem}")
        thought_steps.append(f"约束条件: {', '.join(constraints) if constraints else '无'}")

        thought_steps.append("\n分析:")
        thought_steps.append(f"1. 理解问题: {self._analyze_problem(problem)}")

        thought_steps.append("\n计划:")
        for i in range(1, plan_ahead + 1):
            thought_steps.append(f"{i}. [待规划]")

        thought_steps.append("\n风险识别:")
        thought_steps.append("- [待识别]")

        thought_steps.append("\n最终决策:")
        thought_steps.append("[基于以上分析，做出决策]")

        self.thoughts.append({
            "problem": problem,
            "steps": thought_steps,
            "timestamp": str(datetime.now())
        })

        return "\n".join(thought_steps)

    def _analyze_problem(self, problem: str) -> str:
        """分析问题"""
        keywords = {
            "代码生成": "需要生成完整可运行的代码",
            "调试": "需要定位和修复问题",
            "重构": "需要改进现有代码结构",
            "测试": "需要编写和运行测试",
            "部署": "需要配置部署流程"
        }

        for kw, desc in keywords.items():
            if kw in problem:
                return desc
        return "需要进一步分析"

    def get_thought_history(self) -> list[dict]:
        """获取思考历史"""
        return self.thoughts


from datetime import datetime
