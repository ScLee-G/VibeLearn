"""
Harness Controller（驾驭控制器）- 核心编排器

协调三个 Agent 的协作:
1. Initializer: 初始化任务，分解功能，协商契约
2. Generator: 执行任务，提交成果
3. Evaluator: 评估提交物，决定通过或修复

Harness 特性:
- 外部记忆持久化
- 上下文压缩
- 错误恢复
- 状态管理
"""

import os
import json
from typing import Optional, Any
from pathlib import Path

from .harness_base import BaseAgent, AgentRole, Feature, Contract, TaskStatus, Sprint
from .memory_system import ExternalMemory
from .context_manager import ContextManager
from .agents import InitializerAgent, GeneratorAgent, EvaluatorAgent


class HarnessController:
    """Harness 驾驭控制器"""

    def __init__(
        self,
        project_path: str,
        project_name: str,
        llm_client: Any
    ):
        self.project_path = Path(project_path)
        self.project_name = project_name
        self.llm_client = llm_client

        self.memory = ExternalMemory(str(self.project_path))
        self.context_manager = ContextManager()

        self.initializer = InitializerAgent(llm_client, self.memory, self.context_manager)
        self.generator = GeneratorAgent(llm_client, self.memory, self.context_manager)
        self.evaluator = EvaluatorAgent(llm_client, self.memory, self.context_manager)

        self.current_sprint: Optional[Sprint] = None
        self.current_feature: Optional[Feature] = None
        self.current_contract: Optional[Contract] = None

    def initialize_project(self, user_request: str) -> dict:
        """初始化项目"""
        print("=" * 60)
        print("Harness 系统启动")
        print("=" * 60)

        init_result = self.initializer.initialize_project(
            self.project_name,
            user_request
        )

        print(f"\n[{self.initializer.name}] 项目初始化完成:")
        print(f"  - 分析任务: {init_result['task_analysis']['core_problem']}")
        print(f"  - 功能数量: {len(init_result['features'])}")
        print(f"  - Sprint 数量: {len(init_result['sprints'])}")

        return init_result

    def execute_sprint(self, sprint_id: str = None) -> dict:
        """执行 Sprint"""
        features = self.memory.get_pending_features()

        if not features:
            return {"status": "no_pending_features", "message": "没有待处理的功能"}

        sprint_features = features[:3] if len(features) > 3 else features

        print(f"\n{'=' * 60}")
        print(f"开始 Sprint: {sprint_id or 'default'}")
        print(f"{'=' * 60}")
        print(f"功能列表: {[f.name for f in sprint_features]}")

        sprint_results = []

        for feature in sprint_features:
            result = self.execute_feature(feature)
            sprint_results.append(result)

        print(f"\n{'=' * 60}")
        print(f"Sprint 完成")
        print(f"{'=' * 60}")
        print(f"完成: {len([r for r in sprint_results if r['approved']])}/{len(sprint_results)}")

        return {
            "sprint_id": sprint_id,
            "features": sprint_results,
            "summary": {
                "total": len(sprint_results),
                "passed": len([r for r in sprint_results if r["approved"]]),
                "failed": len([r for r in sprint_results if not r["approved"]])
            }
        }

    def execute_feature(self, feature: Feature) -> dict:
        """执行单个功能"""
        print(f"\n{'-' * 60}")
        print(f"开始执行功能: {feature.name}")
        print(f"{'-' * 60}")

        self.current_feature = feature
        self.memory.update_state({
            "current_feature": feature.id,
            "status": TaskStatus.EXECUTING.value
        })

        contract = self._negotiate_and_create_contract(feature)

        generator_result = self.generator.execute_feature(feature, contract)

        if not generator_result["success"]:
            return {
                "feature_id": feature.id,
                "feature_name": feature.name,
                "approved": False,
                "reason": "Generator 执行失败",
                "result": generator_result
            }

        submission = {
            "feature": feature.to_dict(),
            "contract": contract.to_dict(),
            "result": generator_result,
            "generator_notes": "自测通过"
        }

        evaluation_result = self.evaluator.evaluate_submission(
            feature,
            submission,
            contract
        )

        if evaluation_result["approved"]:
            self.evaluator.approve_feature(feature)
            return {
                "feature_id": feature.id,
                "feature_name": feature.name,
                "approved": True,
                "evaluation": evaluation_result
            }
        else:
            revision_result = self._handle_revision(feature, submission, evaluation_result)
            return {
                "feature_id": feature.id,
                "feature_name": feature.name,
                "approved": revision_result["approved"],
                "issues": evaluation_result["issues"],
                "revisions": revision_result.get("revisions", [])
            }

    def _negotiate_and_create_contract(self, feature: Feature) -> Contract:
        """协商并创建契约"""
        print(f"[{self.initializer.name}] 协商契约...")

        generator_commitment = self.generator.understand_contract(
            Contract(
                id="temp",
                sprint_id="",
                feature_id=feature.id,
                generator_commitment="",
                evaluator_criteria=feature.acceptance_criteria
            )
        )

        negotiated_commitment, final_criteria = self.evaluator.negotiate_requirements(
            feature,
            generator_commitment.get("commitment", "")
        )

        contract = self.evaluator.create_contract(
            feature,
            negotiated_commitment,
            final_criteria
        )

        self.current_contract = contract
        print(f"[{self.initializer.name}] 契约已创建，包含 {len(final_criteria)} 条验收标准")

        return contract

    def _handle_revision(
        self,
        feature: Feature,
        submission: dict,
        evaluation_result: dict
    ) -> dict:
        """处理修订请求"""
        max_revisions = 3
        revision_count = 0

        while not evaluation_result["approved"] and revision_count < max_revisions:
            revision_count += 1
            print(f"\n[{self.evaluator.name}] 修订请求 #{revision_count}")

            feedback = {
                "issues": evaluation_result["issues"],
                "criteria_results": evaluation_result["criteria_results"]
            }

            fix_result = self.generator.handle_evaluator_feedback(feedback)

            if fix_result.get("action") == "proceed":
                break

            for fix in fix_result.get("fixes", []):
                print(f"  修复: {fix['issue']} -> {fix['fix'][:50]}...")

            new_submission = {
                **submission,
                "fixes": fix_result.get("fixes", []),
                "revision_count": revision_count
            }

            evaluation_result = self.evaluator.evaluate_submission(
                feature,
                new_submission,
                self.current_contract
            )

        if evaluation_result["approved"]:
            self.evaluator.approve_feature(feature)
            return {
                "approved": True,
                "revisions": revision_count
            }
        else:
            return {
                "approved": False,
                "revisions": revision_count,
                "reason": f"经过 {max_revisions} 次修订仍未通过"
            }

    def resume_from_state(self) -> dict:
        """从状态恢复执行"""
        state = self.memory.get_state()

        if state.get("current_feature"):
            feature = self.memory.get_feature(state["current_feature"])
            if feature:
                print(f"恢复执行功能: {feature.name}")
                return self.execute_feature(feature)

        if state.get("status") == TaskStatus.PENDING.value:
            return self.execute_sprint()

        return {"status": "nothing_to_resume"}

    def get_project_status(self) -> dict:
        """获取项目状态"""
        completed = self.memory.get_completed_features()
        pending = self.memory.get_pending_features()
        state = self.memory.get_state()

        return {
            "project_name": self.project_name,
            "status": state.get("status", "unknown"),
            "current_feature": state.get("current_feature"),
            "completed_features": len(completed),
            "pending_features": len(pending),
            "completion_rate": len(completed) / (len(completed) + len(pending)) if (completed or pending) else 0
        }

    def export_state(self) -> str:
        """导出状态"""
        return self.memory.get_full_context()

    def run(self, user_request: str) -> dict:
        """运行完整的 Harness 流程"""
        init_result = self.initialize_project(user_request)

        all_results = {
            "initialization": init_result,
            "sprints": []
        }

        while self.memory.get_pending_features():
            sprint_result = self.execute_sprint()
            all_results["sprints"].append(sprint_result)

            if sprint_result.get("summary", {}).get("failed", 0) >= 2:
                print("\n警告: Sprint 中有多个功能失败，暂停检查")
                break

        final_status = self.get_project_status()
        all_results["final_status"] = final_status

        print("\n" + "=" * 60)
        print("Harness 执行完成")
        print("=" * 60)
        print(f"完成率: {final_status['completion_rate']:.1%}")
        print(f"完成功能: {final_status['completed_features']}")
        print(f"待处理: {final_status['pending_features']}")

        return all_results
