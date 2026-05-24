"""
外部记忆系统 - Harness 核心基础设施

使用文件系统作为外部记忆，替代依赖上下文窗口的记忆方式。
核心文件:
- feature_list.json: 项目功能清单
- progress_log.json: 详细执行日志
- state.json: 当前状态快照
- contracts/: 契约存储
- context_archive/: 压缩后的上下文归档
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from .harness_base import Feature, Sprint, Contract, TaskStatus


class ExternalMemory:
    """外部记忆系统"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memory_path = self.project_path / ".harness"
        self.feature_list_path = self.memory_path / "feature_list.json"
        self.progress_log_path = self.memory_path / "progress_log.json"
        self.state_path = self.memory_path / "state.json"
        self.contracts_path = self.memory_path / "contracts"
        self.context_archive_path = self.memory_path / "context_archive"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录结构存在"""
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.contracts_path.mkdir(exist_ok=True)
        self.context_archive_path.mkdir(exist_ok=True)

    def initialize_project(self, project_name: str, description: str = "") -> None:
        """初始化项目记忆"""
        if not self.feature_list_path.exists():
            data = {
                "project_name": project_name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "features": []
            }
            self._save_json(self.feature_list_path, data)

        if not self.progress_log_path.exists():
            self._save_json(self.progress_log_path, {"logs": []})

        if not self.state_path.exists():
            state = {
                "current_sprint": None,
                "current_feature": None,
                "status": TaskStatus.PENDING.value,
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(self.state_path, state)

    def add_feature(self, feature: Feature) -> None:
        """添加功能到清单"""
        data = self._load_json(self.feature_list_path)
        data["features"].append(feature.to_dict())
        self._save_json(self.feature_list_path, data)
        self._log_action("feature_added", feature.to_dict())

    def update_feature(self, feature_id: str, updates: dict) -> None:
        """更新功能状态"""
        data = self._load_json(self.feature_list_path)
        for f in data["features"]:
            if f["id"] == feature_id:
                f.update(updates)
                break
        self._save_json(self.feature_list_path, data)
        self._log_action("feature_updated", {"feature_id": feature_id, "updates": updates})

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """获取功能详情"""
        data = self._load_json(self.feature_list_path)
        for f in data["features"]:
            if f["id"] == feature_id:
                return Feature.from_dict(f)
        return None

    def get_pending_features(self) -> list[Feature]:
        """获取待处理的功能列表"""
        data = self._load_json(self.feature_list_path)
        return [
            Feature.from_dict(f)
            for f in data["features"]
            if f["status"] == TaskStatus.PENDING.value
        ]

    def get_completed_features(self) -> list[Feature]:
        """获取已完成的功能列表"""
        data = self._load_json(self.feature_list_path)
        return [
            Feature.from_dict(f)
            for f in data["features"]
            if f["status"] == TaskStatus.COMPLETED.value
        ]

    def update_state(self, updates: dict) -> None:
        """更新当前状态"""
        state = self._load_json(self.state_path)
        state.update(updates)
        state["last_updated"] = datetime.now().isoformat()
        self._save_json(self.state_path, state)

    def get_state(self) -> dict:
        """获取当前状态"""
        return self._load_json(self.state_path)

    def save_contract(self, contract: Contract) -> None:
        """保存契约"""
        path = self.contracts_path / f"{contract.id}.json"
        self._save_json(path, contract.to_dict())
        self._log_action("contract_saved", contract.to_dict())

    def get_contract(self, contract_id: str) -> Optional[Contract]:
        """获取契约"""
        path = self.contracts_path / f"{contract_id}.json"
        if path.exists():
            data = self._load_json(path)
            return Contract(**data)
        return None

    def archive_context(self, feature_id: str, context: str) -> None:
        """归档压缩后的上下文"""
        archive_file = self.context_archive_path / f"{feature_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(archive_file, "w", encoding="utf-8") as f:
            f.write(context)
        self._log_action("context_archived", {"feature_id": feature_id, "file": str(archive_file)})

    def get_archived_contexts(self, feature_id: str) -> list[str]:
        """获取归档的上下文"""
        pattern = f"{feature_id}_*.txt"
        archives = sorted(self.context_archive_path.glob(pattern), key=os.path.getmtime)
        contexts = []
        for archive in archives:
            with open(archive, "r", encoding="utf-8") as f:
                contexts.append(f.read())
        return contexts

    def _log_action(self, action: str, data: dict) -> None:
        """记录操作日志"""
        log = self._load_json(self.progress_log_path)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "data": data
        }
        log["logs"].append(log_entry)
        self._save_json(self.progress_log_path, log)

    def get_recent_logs(self, count: int = 50) -> list:
        """获取最近的日志"""
        log = self._load_json(self.progress_log_path)
        return log["logs"][-count:]

    def get_full_context(self) -> str:
        """获取完整上下文（用于重新加载世界）"""
        context_parts = []

        context_parts.append("=" * 60)
        context_parts.append("项目状态摘要")
        context_parts.append("=" * 60)

        state = self.get_state()
        context_parts.append(f"\n当前状态: {state.get('status', 'unknown')}")
        context_parts.append(f"当前 Sprint: {state.get('current_sprint', 'none')}")
        context_parts.append(f"当前 Feature: {state.get('current_feature', 'none')}")

        data = self._load_json(self.feature_list_path)
        context_parts.append(f"\n项目: {data.get('project_name', 'unknown')}")

        context_parts.append("\n已完成的功能:")
        for f in data["features"]:
            if f["status"] == TaskStatus.COMPLETED.value:
                context_parts.append(f"  - [{f['id']}] {f['name']}")

        context_parts.append("\n进行中的功能:")
        for f in data["features"]:
            if f["status"] not in [TaskStatus.COMPLETED.value, TaskStatus.PENDING.value]:
                context_parts.append(f"  - [{f['id']}] {f['name']} ({f['status']})")

        context_parts.append("\n待处理的功能:")
        for f in data["features"]:
            if f["status"] == TaskStatus.PENDING.value:
                context_parts.append(f"  - [{f['id']}] {f['name']}")

        context_parts.append("\n" + "=" * 60)
        context_parts.append("最近操作日志")
        context_parts.append("=" * 60)
        recent_logs = self.get_recent_logs(20)
        for log in recent_logs:
            context_parts.append(f"\n[{log['timestamp']}] {log['action']}")

        return "\n".join(context_parts)

    def _load_json(self, path: Path) -> dict:
        """加载 JSON 文件"""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_json(self, path: Path, data: dict) -> None:
        """保存 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def backup(self, backup_path: Optional[str] = None) -> str:
        """备份整个记忆系统"""
        if backup_path is None:
            backup_path = str(self.memory_path.parent / f".harness_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copytree(self.memory_path, backup_path, dirs_exist_ok=True)
        return backup_path

    def restore(self, backup_path: str) -> None:
        """从备份恢复"""
        if Path(backup_path).exists():
            shutil.rmtree(self.memory_path)
            shutil.copytree(backup_path, self.memory_path)
