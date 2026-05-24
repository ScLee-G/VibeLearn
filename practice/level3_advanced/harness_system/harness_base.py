"""
Harness Agent 系统 - 基础模块
基于 Anthropic 三 Agent 架构的 Harness 驾驭工程框架

核心组件:
1. 外部记忆系统 - 文件系统持久化状态
2. 上下文管理器 - 压缩与重组
3. 状态机 - 任务生命周期管理
4. 三 Agent 协作 - Initializer/Generator/Evaluator
"""

import os
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentRole(Enum):
    """Agent 角色枚举"""
    INITIALIZER = "initializer"
    GENERATOR = "generator"
    EVALUATOR = "evaluator"


@dataclass
class Message:
    """Agent 间通信消息"""
    sender: AgentRole
    receiver: AgentRole
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "sender": self.sender.value,
            "receiver": self.receiver.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }


@dataclass
class Feature:
    """功能单元定义"""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    dependencies: list = field(default_factory=list)
    acceptance_criteria: list = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "acceptance_criteria": self.acceptance_criteria,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Feature":
        data["status"] = TaskStatus(data["status"])
        return cls(**data)


@dataclass
class Sprint:
    """Sprint 迭代定义"""
    id: str
    features: list
    status: TaskStatus = TaskStatus.PENDING
    goal: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status.value,
            "features": [f.id for f in self.features],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "notes": self.notes
        }


@dataclass
class Contract:
    """Initializer 与 Evaluator 之间的契约"""
    id: str
    sprint_id: str
    feature_id: str
    generator_commitment: str
    evaluator_criteria: list
    negotiated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    signed: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sprint_id": self.sprint_id,
            "feature_id": self.feature_id,
            "generator_commitment": self.generator_commitment,
            "evaluator_criteria": self.evaluator_criteria,
            "negotiated_at": self.negotiated_at,
            "signed": self.signed
        }


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, role: AgentRole, llm_client: Any, name: str = ""):
        self.role = role
        self.llm_client = llm_client
        self.name = name or role.value
        self.conversation_history: list[Message] = []

    @abstractmethod
    def think(self, context: dict) -> dict:
        """Agent 核心思考逻辑"""
        pass

    def send_message(self, receiver: AgentRole, content: str) -> Message:
        """发送消息"""
        msg = Message(
            sender=self.role,
            receiver=receiver,
            content=content
        )
        self.conversation_history.append(msg)
        return msg

    def receive_message(self, message: Message) -> None:
        """接收消息"""
        self.conversation_history.append(message)

    def get_system_prompt(self) -> str:
        """获取 Agent 系统提示词"""
        return f"""你是 {self.name}，角色是 {self.role.value}。

你的职责是：
{self.get_role_description()}

始终保持专业、严谨的工作态度，确保输出质量。
"""

    @abstractmethod
    def get_role_description(self) -> str:
        """获取角色描述"""
        pass

    def call_llm(self, prompt: str, **kwargs) -> str:
        """调用 LLM"""
        response = self.llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            **kwargs
        )
        return response.choices[0].message.content.strip()
