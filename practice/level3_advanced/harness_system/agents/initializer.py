"""
Initializer Agent（初始化器）- Harness 三 Agent 架构之一

职责:
1. 理解用户任务
2. 将任务分解为功能单元（Features）
3. 与 Evaluator 协商契约（Contract）
4. 规划 Sprint 迭代

协作流程:
- 与 Evaluator 协商契约，双方确认后才开始执行
- 负责任务的初步规划和分解
"""

import uuid
from typing import Optional
from .harness_base import BaseAgent, AgentRole, Feature, Contract, TaskStatus, Message
from .memory_system import ExternalMemory
from .context_manager import ContextManager


class InitializerAgent(BaseAgent):
    """初始化器 Agent"""

    def __init__(
        self,
        llm_client,
        memory: ExternalMemory,
        context_manager: ContextManager
    ):
        super().__init__(AgentRole.INITIALIZER, llm_client, "任务初始化器")
        self.memory = memory
        self.context = context_manager

    def get_role_description(self) -> str:
        return """
你是任务初始化专家，负责:
1. 深入理解用户需求
2. 将复杂任务分解为可执行的最小功能单元
3. 为每个功能定义清晰的验收标准
4. 与评估器协商契约，确保双方对任务理解一致
5. 规划合理的执行顺序和依赖关系

工作原则:
- 分解要足够细，确保每个功能可以在 15-30 分钟内完成
- 验收标准要可测试、可验证
- 考虑功能间的依赖关系和执行顺序
- 确保契约是具体、可衡量的
"""

    def analyze_task(self, user_request: str) -> dict:
        """分析用户任务，返回结构化分析"""
        prompt = f"""
分析以下用户任务，输出 JSON 格式的结构化分析:

任务: {user_request}

请分析并输出:
{{
    "core_problem": "核心要解决的问题",
    "scope": "任务范围",
    "constraints": ["约束条件列表"],
    "success_criteria": ["成功标准列表"],
    "potential_challenges": ["潜在挑战列表"]
}}
"""
        result = self.call_llm(prompt)
        return self._parse_json(result)

    def decompose_to_features(self, task_analysis: dict) -> list[Feature]:
        """将任务分解为功能单元"""
        prompt = f"""
基于以下任务分析，分解为具体的功能单元（Features）:

分析: {task_analysis}

要求:
1. 每个功能应该是独立的、可测试的
2. 功能应该遵循"完成标准"原则
3. 考虑功能间的依赖关系

请输出功能列表，格式:
- 功能1: [名称] - [一句话描述]
- 功能2: [名称] - [一句话描述]
...
"""
        result = self.call_llm(prompt)

        features = []
        for line in result.split("\n"):
            if "-" in line:
                parts = line.split("-", 1)
                if len(parts) == 2:
                    name = parts[0].replace("-", "").strip()
                    desc = parts[1].strip()
                    features.append(Feature(
                        id=str(uuid.uuid4())[:8],
                        name=name,
                        description=desc,
                        priority=len(features),
                        status=TaskStatus.PENDING
                    ))

        if not features:
            features.append(Feature(
                id=str(uuid.uuid4())[:8],
                name="主任务",
                description=task_analysis.get("core_problem", ""),
                priority=0,
                status=TaskStatus.PENDING
            ))

        return features

    def define_acceptance_criteria(self, feature: Feature) -> list[str]:
        """为功能定义验收标准"""
        prompt = f"""
为以下功能定义具体的验收标准（3-5 条）:

功能: {feature.name}
描述: {feature.description}

要求:
- 每条标准必须可测试、可验证
- 使用动词开头：验证、检查、确认、测试
- 标准要具体，避免模糊表述

输出格式:
1. [标准1]
2. [标准2]
3. [标准3]
"""
        result = self.call_llm(prompt)

        criteria = []
        for line in result.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                criteria.append(line.lstrip("0123456789.- ").strip())

        return criteria

    def negotiate_contract(
        self,
        feature: Feature,
        generator_offer: str,
        evaluator_requirements: list[str]
    ) -> Contract:
        """与 Evaluator 协商契约"""
        prompt = f"""
你是契约协调者，帮助 Generator 和 Evaluator 达成一致。

当前功能: {feature.name}
Generator 承诺: {generator_offer}
Evaluator 要求: {evaluator_requirements}

请综合双方意见，生成一个平衡的契约，包含:
1. Generator 的具体承诺
2. Evaluator 的验收标准
3. 明确的完成定义

输出格式:
契约承诺: [具体承诺]
验收标准: [标准列表]
完成定义: [完成意味着什么]
"""
        result = self.call_llm(prompt)

        contract = Contract(
            id=str(uuid.uuid4()),
            sprint_id="",
            feature_id=feature.id,
            generator_commitment=result,
            evaluator_criteria=evaluator_requirements
        )

        self.memory.save_contract(contract)
        return contract

    def plan_sprints(self, features: list[Feature]) -> list[dict]:
        """规划 Sprint 迭代"""
        prompt = f"""
将以下功能规划为 Sprint（每个 Sprint 包含 1-3 个功能）:

功能列表:
{chr(10).join([f"- {f.name}: {f.description}" for f in features])}

规则:
1. 有依赖关系的功能，后置的要在后面
2. 优先完成核心功能
3. 每个 Sprint 时间控制在 1-2 小时

输出格式:
Sprint 1: [功能列表]
Sprint 2: [功能列表]
...
"""
        result = self.call_llm(prompt)

        sprints = []
        current_sprint = None

        for line in result.split("\n"):
            if "Sprint" in line and ":" in line:
                sprint_name = line.split(":")[0].strip()
                current_sprint = {
                    "id": str(uuid.uuid4())[:8],
                    "name": sprint_name,
                    "features": []
                }
                sprints.append(current_sprint)
            elif current_sprint and "-" in line:
                current_sprint["features"].append(line.strip("- ").strip())

        return sprints if sprints else [{"id": "sprint-1", "name": "Sprint 1", "features": [f.id for f in features]}]

    def initialize_project(self, project_name: str, user_request: str) -> dict:
        """初始化项目，返回完整规划"""
        print(f"[{self.name}] 开始分析任务...")

        self.memory.initialize_project(project_name, user_request)
        task_analysis = self.analyze_task(user_request)
        features = self.decompose_to_features(task_analysis)

        for feature in features:
            feature.acceptance_criteria = self.define_acceptance_criteria(feature)
            self.memory.add_feature(feature)

        sprints = self.plan_sprints(features)

        self.memory.update_state({
            "status": TaskStatus.INITIALIZING.value,
            "task_analysis": task_analysis,
            "total_features": len(features),
            "total_sprints": len(sprints)
        })

        return {
            "task_analysis": task_analysis,
            "features": [f.to_dict() for f in features],
            "sprints": sprints
        }

    def think(self, context: dict) -> dict:
        """Initializer 核心思考逻辑"""
        action = context.get("action", "")

        if action == "initialize":
            return self.initialize_project(
                context.get("project_name", "未命名项目"),
                context.get("user_request", "")
            )
        elif action == "negotiate":
            return self.negotiate_contract(
                context.get("feature"),
                context.get("generator_offer", ""),
                context.get("evaluator_requirements", [])
            )

        return {"status": "unknown_action"}

    def _parse_json(self, text: str) -> dict:
        """解析 LLM 输出的 JSON"""
        import json
        import re

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"raw": text}
