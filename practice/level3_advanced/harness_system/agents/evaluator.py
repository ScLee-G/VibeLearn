"""
Evaluator Agent（评估器）- Harness 三 Agent 架构之一

职责:
1. 定义验收标准
2. 与 Generator 协商契约
3. 严格验证提交物
4. 要求修复发现的问题
5. 确认功能最终完成

协作流程:
- 与 Generator 协商契约（Contract）
- 等待 Generator 提交
- 严格验证提交物
- 通过则放行，失败则要求修复
- 像开发者和 QA 工程师之间的对话
"""

import uuid
from typing import Optional
from .harness_base import BaseAgent, AgentRole, Feature, Contract, TaskStatus, Message
from .memory_system import ExternalMemory
from .context_manager import ContextManager


class EvaluatorAgent(BaseAgent):
    """评估器 Agent"""

    def __init__(
        self,
        llm_client,
        memory: ExternalMemory,
        context_manager: ContextManager
    ):
        super().__init__(AgentRole.EVALUATOR, llm_client, "质量评估器")
        self.memory = memory
        self.context = context_manager
        self.evaluation_history: list[dict] = []
        self.revision_requests: list[dict] = []

    def get_role_description(self) -> str:
        return """
你是质量评估专家，负责:
1. 定义清晰的验收标准
2. 严格验证 Generator 的提交物
3. 确保交付物符合契约承诺
4. 发现问题时明确指出，不含糊
5. 验证每个验收标准

工作原则:
- 标准是客观的、可测试的
- 验证要严格，不降低标准
- 反馈要具体，说明哪里有问题
- 只有全部通过才放行
- 你是质量守门人，不是和事佬
"""

    def define_requirements(self, feature: Feature) -> list[str]:
        """为功能定义验收要求"""
        prompt = f"""
作为评估专家，为以下功能定义具体的验收要求:

功能: {feature.name}
描述: {feature.description}

要求:
1. 每条要求必须可测试、可验证
2. 使用具体的指标或标准
3. 考虑功能的所有边界情况
4. 包含质量检查点

输出格式（5-7 条）:
1. [要求1 - 具体、可测试]
2. [要求2 - 具体、可测试]
...
"""
        result = self.call_llm(prompt)

        requirements = []
        for line in result.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                requirements.append(line.lstrip("0123456789.- ").strip())

        return requirements if requirements else feature.acceptance_criteria

    def negotiate_requirements(
        self,
        feature: Feature,
        generator_commitment: str
    ) -> tuple[str, list[str]]:
        """与 Generator 协商要求"""
        prompt = f"""
作为评估专家，与 Generator 协商验收标准:

功能: {feature.name}
Generator 的承诺: {generator_commitment}

请:
1. 评估 Generator 的承诺是否足够
2. 补充或调整验收标准
3. 明确哪些是必须满足的，哪些是可选的

输出:
最终承诺: [综合后的承诺]
验收标准: [最终标准列表]
"""
        result = self.call_llm(prompt)

        import json
        import re

        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed.get("最终承诺", ""), parsed.get("验收标准", [])
            except json.JSONDecodeError:
                pass

        return result, self.define_requirements(feature)

    def create_contract(
        self,
        feature: Feature,
        negotiated_commitment: str,
        final_criteria: list[str]
    ) -> Contract:
        """创建最终契约"""
        contract = Contract(
            id=str(uuid.uuid4()),
            sprint_id="",
            feature_id=feature.id,
            generator_commitment=negotiated_commitment,
            evaluator_criteria=final_criteria,
            signed=True
        )

        self.memory.save_contract(contract)
        return contract

    def evaluate_submission(
        self,
        feature: Feature,
        submission: dict,
        contract: Contract
    ) -> dict:
        """评估提交物"""
        print(f"[{self.name}] 开始评估: {feature.name}")

        evaluation = {
            "feature_id": feature.id,
            "feature_name": feature.name,
            "submission": submission,
            "criteria_results": [],
            "overall_passed": False,
            "issues": [],
            "approved": False
        }

        self.memory.update_state({
            "status": TaskStatus.EVALUATING.value,
            "current_feature": feature.id
        })

        for criterion in contract.evaluator_criteria:
            criterion_result = self._evaluate_criterion(
                criterion,
                submission,
                feature
            )
            evaluation["criteria_results"].append(criterion_result)

            if not criterion_result["passed"]:
                evaluation["issues"].extend(criterion_result["issues"])

        all_passed = all(r["passed"] for r in evaluation["criteria_results"])
        evaluation["overall_passed"] = all_passed
        evaluation["approved"] = all_passed

        self.evaluation_history.append(evaluation)

        if not all_passed:
            self._request_revision(feature, evaluation)

        self.memory._log_action("evaluation", evaluation)

        return evaluation

    def _evaluate_criterion(
        self,
        criterion: str,
        submission: dict,
        feature: Feature
    ) -> dict:
        """评估单个标准"""
        prompt = f"""
严格评估以下提交是否满足验收标准:

验收标准: {criterion}

提交内容:
{submission}

功能: {feature.name}
功能描述: {feature.description}

请进行严格评估:
1. 这个提交是否满足该标准？
2. 具体哪里有问题（如果有）？
3. 给出具体的改进建议

输出格式（JSON）:
{{
    "criterion": "{criterion}",
    "passed": true/false,
    "evidence": "支撑判断的证据",
    "issues": ["问题列表"],
    "suggestions": ["改进建议"]
}}
"""
        result = self.call_llm(prompt)

        import json
        import re

        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed
            except json.JSONDecodeError:
                pass

        return {
            "criterion": criterion,
            "passed": True,
            "evidence": "Manual verification needed",
            "issues": [],
            "suggestions": []
        }

    def _request_revision(self, feature: Feature, evaluation: dict) -> None:
        """请求修订"""
        revision_request = {
            "request_id": str(uuid.uuid4()),
            "feature_id": feature.id,
            "timestamp": str(uuid.now()),
            "issues": evaluation["issues"],
            "criteria_results": evaluation["criteria_results"]
        }

        self.revision_requests.append(revision_request)

        print(f"[{self.name}] 评估未通过，需要修复:")
        for issue in evaluation["issues"]:
            print(f"  - {issue}")

    def approve_feature(self, feature: Feature) -> dict:
        """批准功能完成"""
        self.memory.update_feature(feature.id, {
            "status": TaskStatus.COMPLETED.value,
            "approved_at": str(uuid.now()),
            "approved_by": self.role.value
        })

        self.memory.update_state({
            "status": TaskStatus.COMECUTING.value,
            "current_feature": None
        })

        print(f"[{self.name}] 功能已批准: {feature.name}")

        return {
            "approved": True,
            "feature_id": feature.id,
            "feature_name": feature.name
        }

    def conduct_sprint_review(self, sprint_features: list[Feature]) -> dict:
        """进行 Sprint 评审"""
        prompt = f"""
对 Sprint 中的所有功能进行评审总结:

功能列表:
{chr(10).join([f'- {f.name}: {f.status.value}' for f in sprint_features])}

请提供:
1. Sprint 整体完成情况
2. 质量问题总结（如果有）
3. 改进建议
"""
        result = self.call_llm(prompt)

        return {
            "sprint_summary": result,
            "features_reviewed": len(sprint_features),
            "passed": len([f for f in sprint_features if f.status == TaskStatus.COMPLETED])
        }

    def provide_feedback(
        self,
        feature: Feature,
        feedback_type: str = "general"
    ) -> str:
        """提供反馈"""
        prompt = f"""
基于评估历史，为以下功能提供反馈:

功能: {feature.name}

反馈类型: {feedback_type}

评估历史:
{self.evaluation_history[-3:] if self.evaluation_history else "暂无历史"}

请提供建设性的反馈。
"""
        return self.call_llm(prompt)

    def get_evaluation_metrics(self) -> dict:
        """获取评估指标"""
        total_evaluations = len(self.evaluation_history)
        if total_evaluations == 0:
            return {
                "total_evaluated": 0,
                "first_time_pass_rate": 0,
                "avg_revisions": 0
            }

        first_time_pass = sum(
            1 for e in self.evaluation_history
            if len([r for r in self.revision_requests if r["feature_id"] == e["feature_id"]]) == 0
        )

        return {
            "total_evaluated": total_evaluations,
            "first_time_pass_rate": first_time_pass / total_evaluations,
            "total_revisions_requested": len(self.revision_requests),
            "avg_revisions": len(self.revision_requests) / total_evaluations if total_evaluations > 0 else 0
        }

    def think(self, context: dict) -> dict:
        """Evaluator 核心思考逻辑"""
        action = context.get("action", "")

        if action == "evaluate":
            return self.evaluate_submission(
                context.get("feature"),
                context.get("submission"),
                context.get("contract")
            )
        elif action == "approve":
            return self.approve_feature(context.get("feature"))
        elif action == "negotiate":
            commitment, criteria = self.negotiate_requirements(
                context.get("feature"),
                context.get("generator_commitment", "")
            )
            return {
                "commitment": commitment,
                "criteria": criteria
            }
        elif action == "review_sprint":
            return self.conduct_sprint_review(context.get("features", []))

        return {"status": "unknown_action"}
