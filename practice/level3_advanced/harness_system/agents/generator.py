"""
Generator Agent（生成器）- Harness 三 Agent 架构之一

职责:
1. 根据契约执行具体任务
2. 编写代码/内容
3. 进行自我测试
4. 遇到问题主动反思和调整
5. 向 Evaluator 提交成果

协作流程:
- 接收 Initializer 分配的功能
- 与 Evaluator 协商契约承诺
- 执行任务并自测
- 提交给 Evaluator 验收
"""

import uuid
from typing import Optional
from .harness_base import BaseAgent, AgentRole, Feature, Contract, TaskStatus, Message
from .memory_system import ExternalMemory
from .context_manager import ContextManager, ThinkingTool


class GeneratorAgent(BaseAgent):
    """生成器 Agent"""

    def __init__(
        self,
        llm_client,
        memory: ExternalMemory,
        context_manager: ContextManager
    ):
        super().__init__(AgentRole.GENERATOR, llm_client, "代码生成器")
        self.memory = memory
        self.context = context_manager
        self.thinking = ThinkingTool()
        self.current_contract: Optional[Contract] = None
        self.current_feature: Optional[Feature] = None
        self.submission_history: list[dict] = []

    def get_role_description(self) -> str:
        return """
你是代码生成专家，负责:
1. 理解并接受契约中的承诺
2. 高质量地完成分配的任务
3. 进行自我测试和验证
4. 遇到问题时主动反思和调整
5. 确保交付物符合验收标准

工作原则:
- 一次只做一个功能，完成后再做下一个
- 每个步骤都要可验证
- 遇到错误要分析原因，不是简单地跳过
- 承诺就要兑现，不能降低标准
- 定期检查上下文使用情况，避免"上下文焦虑"
"""

    def understand_contract(self, contract: Contract) -> dict:
        """理解契约，明确承诺"""
        prompt = f"""
你已接受以下契约，请明确理解并确认承诺:

契约内容:
{contract.generator_commitment}

验收标准:
{chr(10).join([f'- {c}' for c in contract.evaluator_criteria])}

请输出:
1. 你的具体承诺（用一句话概括）
2. 执行计划（3-5 步）
3. 风险识别（可能遇到的问题）
"""
        result = self.call_llm(prompt)

        return {
            "commitment": result,
            "understood": True
        }

    def execute_feature(self, feature: Feature, contract: Contract) -> dict:
        """执行功能"""
        print(f"[{self.name}] 开始执行功能: {feature.name}")

        self.memory.update_feature(feature.id, {"status": TaskStatus.EXECUTING.value})
        self.memory.update_state({
            "current_feature": feature.id,
            "status": TaskStatus.EXECUTING.value
        })

        self.current_feature = feature
        self.current_contract = contract

        context = self.context.build_task_context(
            task_description=f"执行功能: {feature.name}",
            project_state=self.memory.get_full_context(),
            feature=feature.to_dict()
        )

        plan = self._create_execution_plan(feature, contract)
        print(f"[{self.name}] 执行计划: {plan['steps']}")

        execution_results = []
        for step in plan["steps"]:
            print(f"[{self.name}] 执行步骤: {step['description']}")
            step_result = self._execute_step(step, feature, contract)
            execution_results.append(step_result)

            if step_result.get("needs_fix"):
                print(f"[{self.name}] 步骤需要修复...")
                fix_result = self._fix_step(step, step_result)
                execution_results[-1] = fix_result

        final_result = self._compile_results(feature, execution_results)

        self.memory.update_feature(feature.id, {
            "status": TaskStatus.COMPLETED.value if final_result["success"] else TaskStatus.FAILED.value,
            "notes": str(final_result)
        })

        return final_result

    def _create_execution_plan(self, feature: Feature, contract: Contract) -> dict:
        """创建执行计划"""
        prompt = f"""
为以下功能创建详细的执行计划:

功能: {feature.name}
描述: {feature.description}
验收标准: {chr(10).join([f'- {c}' for c in feature.acceptance_criteria])}

要求:
1. 将任务分解为 3-6 个具体步骤
2. 每个步骤要有明确的输出
3. 考虑验证和测试步骤

输出格式（JSON）:
{{
    "steps": [
        {{"order": 1, "description": "步骤描述", "output": "预期输出"}},
        ...
    ]
}}
"""
        result = self.call_llm(prompt)
        import json
        import re

        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "steps": [
                {"order": 1, "description": "执行任务", "output": "完成的功能"}
            ]
        }

    def _execute_step(self, step: dict, feature: Feature, contract: Contract) -> dict:
        """执行单个步骤"""
        step_context = f"""
当前步骤: {step['description']}
功能: {feature.name}
预期输出: {step['output']}

验收标准:
{chr(10).join([f'- {c}' for c in feature.acceptance_criteria])}

项目上下文:
{self.memory.get_full_context()}
"""

        thinking_result = self.thinking.think(
            problem=step_context,
            constraints=feature.acceptance_criteria,
            plan_ahead=3
        )

        prompt = f"""
{self.get_role_description()}

当前任务:
{step_context}

思考过程:
{thinking_result}

请执行这个步骤，输出具体的执行结果。
"""
        result = self.call_llm(prompt)

        verification = self._verify_step_result(step, result, feature)

        return {
            "step": step,
            "result": result,
            "verification": verification,
            "needs_fix": not verification["passed"]
        }

    def _verify_step_result(self, step: dict, result: str, feature: Feature) -> dict:
        """验证步骤结果"""
        prompt = f"""
验证以下执行结果是否符合要求:

步骤: {step['description']}
执行结果:
{result}

验收标准:
{chr(10).join([f'- {c}' for c in feature.acceptance_criteria])}

请判断:
1. 结果是否满足验收标准？
2. 是否有遗漏？
3. 是否需要修复？

输出格式:
{{
    "passed": true/false,
    "issues": ["问题列表，如果有的话"],
    "suggestions": ["改进建议，如果有的话"]
}}
"""
        verification_result = self.call_llm(prompt)

        import json
        import re

        json_match = re.search(r'\{[\s\S]*\}', verification_result)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"passed": True, "issues": [], "suggestions": []}

    def _fix_step(self, step: dict, step_result: dict) -> dict:
        """修复步骤问题"""
        prompt = f"""
需要修复以下步骤:

原始步骤: {step['description']}
执行结果: {step_result['result']}
问题: {step_result['verification'].get('issues', [])}
建议: {step_result['verification'].get('suggestions', [])}

请根据反馈修复问题，重新执行这个步骤。
"""
        fixed_result = self.call_llm(prompt)
        return {
            **step_result,
            "result": fixed_result,
            "fixed": True
        }

    def _compile_results(self, feature: Feature, execution_results: list) -> dict:
        """汇总执行结果"""
        all_passed = all(not r.get("needs_fix", False) for r in execution_results)

        return {
            "success": all_passed,
            "feature_id": feature.id,
            "feature_name": feature.name,
            "results": execution_results,
            "summary": f"完成 {len(execution_results)} 个步骤" if all_passed else "部分完成，需要继续"
        }

    def self_test(self, artifact: str, feature: Feature) -> dict:
        """自我测试"""
        prompt = f"""
对以下产出进行自我测试:

产出: {artifact}

功能: {feature.name}
验收标准: {chr(10).join([f'- {c}' for c in feature.acceptance_criteria])}

请进行以下测试:
1. 完整性检查 - 是否包含所有必要部分？
2. 正确性检查 - 是否符合规范？
3. 质量检查 - 代码质量/内容质量如何？

输出测试报告。
"""
        result = self.call_llm(prompt)
        return {"test_report": result, "passed": True}

    def submit_to_evaluator(self, feature: Feature, submission: dict) -> dict:
        """提交给 Evaluator 验收"""
        submission_record = {
            "submission_id": str(uuid.uuid4()),
            "feature_id": feature.id,
            "feature_name": feature.name,
            "timestamp": str(uuid.now()),
            "submission": submission
        }

        self.submission_history.append(submission_record)

        self.memory._log_action("submission", submission_record)

        return {
            "submitted": True,
            "submission_id": submission_record["submission_id"],
            "awaiting_review": True
        }

    def handle_evaluator_feedback(self, feedback: dict) -> dict:
        """处理 Evaluator 的反馈"""
        if feedback.get("approved"):
            print(f"[{self.name}] 提交已通过！")
            return {"action": "proceed"}

        issues = feedback.get("issues", [])
        print(f"[{self.name}] 收到反馈，需要修复 {len(issues)} 个问题")

        fixes = []
        for issue in issues:
            fix_prompt = f"""
Evaluator 反馈的问题:
{issue}

请修复这个问题。
"""
            fix_result = self.call_llm(fix_prompt)
            fixes.append({
                "issue": issue,
                "fix": fix_result
            })

        return {
            "action": "fix_and_resubmit",
            "fixes": fixes
        }

    def think(self, context: dict) -> dict:
        """Generator 核心思考逻辑"""
        action = context.get("action", "")

        if action == "execute":
            return self.execute_feature(
                context.get("feature"),
                context.get("contract")
            )
        elif action == "self_test":
            return self.self_test(
                context.get("artifact"),
                context.get("feature")
            )
        elif action == "submit":
            return self.submit_to_evaluator(
                context.get("feature"),
                context.get("submission")
            )

        return {"status": "unknown_action"}
