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
- 资源监控
- 性能追踪
- 超时控制
- 缓存优化
"""

import os
import sys
import json
import time
from typing import Optional, Any
from pathlib import Path
from dataclasses import asdict

from .harness_base import BaseAgent, AgentRole, Feature, Contract, TaskStatus, Sprint
from .memory_system import ExternalMemory
from .context_manager import ContextManager
from .agents import InitializerAgent, GeneratorAgent, EvaluatorAgent
from .resource_manager import (
    ResourceMonitor,
    PerformanceTracker,
    TimeoutManager,
    SimpleCache,
    ResourceOptimizer
)


class HarnessController:
    """Harness 驾驭控制器"""

    def __init__(
        self,
        project_path: str,
        project_name: str,
        llm_client: Any,
        enable_resource_monitoring: bool = True,
        feature_timeout_seconds: int = 300,
        max_cpu_percent: float = 95.0,
        max_memory_percent: float = 90.0,
        max_disk_percent: float = 95.0,
    ):
        self.project_path = Path(project_path)
        self.project_name = project_name
        self.llm_client = llm_client

        # 资源配置
        self.enable_resource_monitoring = enable_resource_monitoring
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.max_disk_percent = max_disk_percent

        # 核心组件
        self.memory = ExternalMemory(str(self.project_path))
        self.context_manager = ContextManager()

        self.initializer = InitializerAgent(llm_client, self.memory, self.context_manager)
        self.generator = GeneratorAgent(llm_client, self.memory, self.context_manager)
        self.evaluator = EvaluatorAgent(llm_client, self.memory, self.context_manager)

        # 性能管理
        self.resource_monitor = ResourceMonitor(str(self.project_path / ".harness"))
        self.performance_tracker = PerformanceTracker()
        self.timeout_manager = TimeoutManager(feature_timeout_seconds)
        self.response_cache = SimpleCache(max_size=50, ttl_seconds=1800)
        self.resource_optimizer = ResourceOptimizer()

        # 状态
        self.current_sprint: Optional[Sprint] = None
        self.current_feature: Optional[Feature] = None
        self.current_contract: Optional[Contract] = None
        self._resource_warning_shown = False

    def check_resources(self) -> tuple[bool, list[str]]:
        """检查系统资源是否充足"""
        if not self.enable_resource_monitoring:
            return True, []

        snapshot = self.resource_monitor.snapshot()
        warnings = []

        if snapshot.cpu_percent > self.max_cpu_percent:
            warnings.append(f"CPU 使用率过高: {snapshot.cpu_percent:.1f}% (上限: {self.max_cpu_percent}%)")

        if snapshot.memory_percent > self.max_memory_percent:
            warnings.append(f"内存使用率过高: {snapshot.memory_percent:.1f}% (上限: {self.max_memory_percent}%)")

        if snapshot.disk_percent > self.max_disk_percent:
            warnings.append(f"磁盘空间不足: {snapshot.disk_percent:.1f}% (上限: {self.max_disk_percent}%)")

        return len(warnings) == 0, warnings

    def initialize_project(self, user_request: str) -> dict:
        """初始化项目"""
        print("=" * 60)
        print("Harness 系统启动")
        print("=" * 60)

        # 启动性能追踪
        self.performance_tracker.start()

        # 检查资源
        if self.enable_resource_monitoring:
            print("\n[系统] 检查资源状态...")
            snapshot = self.resource_monitor.snapshot()
            print(f"  - 内存使用: {snapshot.memory_percent:.1f}%")
            print(f"  - CPU 使用: {snapshot.cpu_percent:.1f}%")
            print(f"  - 磁盘使用: {snapshot.disk_percent:.1f}%")

            ok, warnings = self.check_resources()
            if not ok:
                print("\n⚠️ 资源警告:")
                for w in warnings:
                    print(f"   - {w}")
                print("\n继续执行可能影响性能，建议关闭其他应用。\n")

        init_result = self.initializer.initialize_project(
            self.project_name,
            user_request
        )

        print(f"\n[{self.initializer.name}] 项目初始化完成:")
        print(f"  - 分析任务: {init_result['task_analysis']['core_problem']}")
        print(f"  - 功能数量: {len(init_result['features'])}")
        print(f"  - Sprint 数量: {len(init_result['sprints'])}")

        # 预估资源需求
        estimated_disk = self.resource_optimizer.estimate_disk_needed(len(init_result['features']))
        print(f"  - 预估磁盘需求: {estimated_disk:.1f} MB")

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

        # 执行前检查资源
        if self.enable_resource_monitoring:
            ok, warnings = self.check_resources()
            if not ok and not self._resource_warning_shown:
                print("\n⚠️ 资源警告:")
                for w in warnings:
                    print(f"   - {w}")
                self._resource_warning_shown = True
                print()

        self.current_feature = feature
        self.memory.update_state({
            "current_feature": feature.id,
            "status": TaskStatus.EXECUTING.value
        })

        # 设置超时
        self.timeout_manager.set_timeout(f"feature_{feature.id}", 300)

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

        try:
            while self.memory.get_pending_features():
                # 周期性资源检查
                if self.enable_resource_monitoring:
                    self.resource_monitor.snapshot()

                sprint_result = self.execute_sprint()
                all_results["sprints"].append(sprint_result)

                if sprint_result.get("summary", {}).get("failed", 0) >= 2:
                    print("\n警告: Sprint 中有多个功能失败，暂停检查")
                    break

                # Sprint 之间小休息
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n用户中断，保存进度...")

        except Exception as e:
            print(f"\n\n错误: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 保存最终状态
            self._finalize_execution(all_results)

        return all_results

    def _finalize_execution(self, all_results: dict):
        """完成执行后的清理和报告"""
        final_status = self.get_project_status()
        all_results["final_status"] = final_status

        # 停止性能追踪
        self.performance_tracker.record_feature_completion(
            final_status['completed_features'],
            final_status['completed_features'] + final_status['pending_features']
        )
        performance_metrics = self.performance_tracker.stop()
        all_results["performance"] = asdict(performance_metrics)

        # 保存性能数据
        metrics_path = self.project_path / ".harness" / "performance.json"
        with open(metrics_path, "w") as f:
            json.dump(asdict(performance_metrics), f, indent=2)

        print("\n" + "=" * 60)
        print("Harness 执行完成")
        print("=" * 60)
        print(f"完成率: {final_status['completion_rate']:.1%}")
        print(f"完成功能: {final_status['completed_features']}")
        print(f"待处理: {final_status['pending_features']}")

        # 显示性能报告
        print("\n性能报告:")
        print(f"  总耗时: {performance_metrics.total_duration_seconds:.1f} 秒")
        print(f"  API 调用: {performance_metrics.total_api_calls}")
        print(f"  平均响应: {performance_metrics.avg_response_time_seconds:.2f} 秒/次")

        # 资源使用统计
        if self.enable_resource_monitoring:
            final_snapshot = self.resource_monitor.snapshot()
            print(f"\n最终资源状态:")
            print(f"  内存: {final_snapshot.memory_percent:.1f}%")
            print(f"  CPU: {final_snapshot.cpu_percent:.1f}%")
            print(f"  磁盘: {final_snapshot.disk_percent:.1f}%")

            avg_usage = self.resource_monitor.get_average_usage()
            if avg_usage:
                print(f"\n平均资源使用:")
                print(f"  内存: {avg_usage['avg_memory_percent']:.1f}%")
                print(f"  CPU: {avg_usage['avg_cpu_percent']:.1f}%")

        print(f"\n详细日志和数据已保存到: {self.project_path / '.harness'}")

    def get_performance_report(self) -> dict:
        """获取性能报告"""
        return {
            "current": asdict(self.performance_tracker.stop()) if self.performance_tracker._start_time else None,
            "resource": self.resource_monitor.get_average_usage(),
            "cache_size": self.response_cache.size()
        }

    def clear_cache(self):
        """清空响应缓存"""
        self.response_cache.clear()
        print("缓存已清空")

    def get_system_info(self) -> dict:
        """获取系统信息"""
        import platform

        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "harness_version": "1.0.0"
        }
