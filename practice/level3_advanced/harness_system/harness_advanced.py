"""
Harness 驾驭系统 - 增强版 (Advanced Harness)
========================================================
核心增强：
1. Skill 分层路由系统 - 原子 Skill、复合 Skill、Skill 目录
2. 自进化记忆沉淀 - 程序性经验 / 情景记忆 / 用户画像
3. 分层上下文压缩 - 外部化结果、占位压缩、结构化摘要
4. 中心化多 Agent 协作 - 子 Agent 受限工具调用 + Fork/Worktree 模式
5. 权限与安全审查 - 规则过滤、工具自检、AI 风险分类

设计参考 Claude Code 的多层架构，用 Python 模拟完整生命周期。
"""

import json
import os
import time
import hashlib
import random
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Callable
from abc import ABC, abstractmethod
from collections import defaultdict


# ============================================================
# 一、数据结构
# ============================================================

@dataclass
class Task:
    """用户任务"""
    id: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 3  # 1-5
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class SkillExecutionLog:
    """Skill 执行日志（用于记忆沉淀）"""
    skill_name: str
    input: str
    output: str
    success: bool
    duration_ms: int
    tokens: int
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def key(self) -> str:
        return hashlib.md5(
            f"{self.skill_name}:{self.input[:200]}".encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()


# ============================================================
# 二、Skill 分层路由系统
# ============================================================

class Skill(ABC):
    """Skill 基类"""
    name: str = "base"
    description: str = ""
    level: str = "atomic"  # atomic(原子) / composite(复合) / catalog(目录)
    cost: int = 1  # token 成本估算

    @abstractmethod
    def execute(self, task: Task, memory: "MemorySystem") -> Dict[str, Any]:
        pass


class SkillRegistry:
    """Skill 注册与路由中心"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._category_index: Dict[str, List[str]] = defaultdict(list)
        self._keyword_index: Dict[str, List[str]] = defaultdict(list)

    def register(self, skill: Skill, categories: List[str] = None, keywords: List[str] = None):
        self._skills[skill.name] = skill
        categories = categories or [skill.level]
        for cat in categories:
            self._category_index[cat].append(skill.name)
        for kw in keywords or []:
            self._keyword_index[kw.lower()].append(skill.name)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def all(self) -> List[Skill]:
        return list(self._skills.values())

    def route(self, task: Task) -> List[Skill]:
        """基于关键词 + 分类的启发式路由"""
        desc = task.description.lower()
        scores = defaultdict(float)

        # 关键词匹配
        for kw, skill_names in self._keyword_index.items():
            if kw in desc:
                for sn in skill_names:
                    scores[sn] += 2.0

        # 分类匹配
        for cat, skill_names in self._category_index.items():
            if cat.lower() in desc:
                for sn in skill_names:
                    scores[sn] += 1.0

        # 目录型 Skill 始终作为 fallback
        for name, skill in self._skills.items():
            if skill.level == "catalog":
                scores.setdefault(name, 0.3)

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        matched = [self._skills[name] for name, score in ranked if score > 0]

        if not matched:
            # fallback: 返回所有目录型 Skill
            matched = [s for s in self._skills.values() if s.level == "catalog"]
        return matched[:5]

    def summary(self) -> str:
        """返回当前 Skill 体系摘要（用于提示 LLM）"""
        lines = ["可用 Skill 体系:"]
        for skill in self._skills.values():
            lines.append(f"  - [{skill.level.upper()}] {skill.name}: {skill.description}")
        return "\n".join(lines)


# ---- 具体 Skill 实现 ----

class FileReadSkill(Skill):
    """原子 Skill - 读取文件"""
    name = "file_read"
    description = "读取本地文件内容"
    level = "atomic"

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        filepath = task.context.get("filepath")
        if not filepath:
            return {"success": False, "error": "未提供 filepath"}
        try:
            p = Path(filepath)
            if not p.exists():
                return {"success": False, "error": f"文件不存在: {filepath}"}
            content = p.read_text(encoding="utf-8")
            return {"success": True, "content": content, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileWriteSkill(Skill):
    """原子 Skill - 写入文件"""
    name = "file_write"
    description = "将内容写入本地文件"
    level = "atomic"

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        filepath = task.context.get("filepath")
        content = task.context.get("content", "")
        try:
            p = Path(filepath)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"success": True, "filepath": filepath, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class WebSearchSkill(Skill):
    """原子 Skill - 模拟网络搜索"""
    name = "web_search"
    description = "在网络上搜索最新信息"
    level = "atomic"

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        query = task.context.get("query", task.description)
        # 模拟搜索结果
        results = [
            f"[模拟结果1] 关于 '{query}' 的最新资料 - source A",
            f"[模拟结果2] 关于 '{query}' 的行业报告 - source B",
            f"[模拟结果3] 相关技术讨论 - source C",
        ]
        return {"success": True, "query": query, "results": results, "count": len(results)}


class CodeReviewSkill(Skill):
    """复合 Skill - 代码审查（组合 file_read + 规则检查）"""
    name = "code_review"
    description = "审查代码质量、风格与潜在 Bug"
    level = "composite"

    CHECKS = {
        "print调试": "是否遗留 print 调试语句",
        "TODO/FIXME": "是否遗留未完成标记",
        "长函数": "是否存在超过 100 行的函数",
        "异常处理": "是否缺少 try/except",
        "硬编码": "是否存在硬编码的密钥/路径",
    }

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        filepath = task.context.get("filepath")
        read_result = FileReadSkill().execute(
            Task(id="inner", description=f"读取 {filepath}", context={"filepath": filepath}),
            memory,
        )
        if not read_result.get("success"):
            return read_result
        content = read_result.get("content", "")
        findings = []
        for check_name, check_desc in self.CHECKS.items():
            if check_name.lower() in content.lower() or check_name in content:
                findings.append(f"发现 '{check_name}' 相关问题 - {check_desc}")

        # 粗略行数统计
        lines = content.splitlines()
        if len(lines) > 200:
            findings.append(f"文件总行数 {len(lines)}，建议拆分")

        # 简单安全性规则
        security_keywords = ["password", "apikey", "secret_key", "token"]
        for kw in security_keywords:
            if kw in content.lower():
                findings.append(f"潜在敏感信息泄露: 发现 '{kw}'")

        return {
            "success": True,
            "filepath": filepath,
            "findings": findings,
            "total_lines": len(lines),
            "risk_level": "高" if len(findings) >= 3 else ("中" if len(findings) >= 1 else "低"),
        }


class SummarySkill(Skill):
    """复合 Skill - 内容摘要/上下文压缩"""
    name = "summarize"
    description = "对长文档或长工具输出进行结构化摘要"
    level = "composite"

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        content = task.context.get("content", task.description)
        target_ratio = task.context.get("ratio", 0.2)  # 压缩到原长度的 20%

        lines = content.splitlines()
        # 启发式摘要：保留首段 + 每段首句 + 含关键标记的行
        key_lines = []
        key_markers = ["关键", "重要", "核心", "TODO", "注意", "⚠", "error", "fail"]
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if i < 3 or any(km in line for km in key_markers):
                key_lines.append(stripped)
            elif i % max(1, int(1 / target_ratio)) == 0:
                key_lines.append(stripped)

        summary = "\n".join(key_lines[:20])  # 最多 20 行
        return {
            "success": True,
            "summary": summary,
            "original_size": len(content),
            "compressed_size": len(summary),
            "ratio": len(summary) / max(1, len(content)),
        }


class SafetyCheckSkill(Skill):
    """复合 Skill - 安全审查/风险分类"""
    name = "safety_check"
    description = "对计划执行的操作进行前置风险审查"
    level = "composite"

    DANGEROUS_PATTERNS = [
        ("rm -rf", "危险: 可能递归删除文件"),
        ("format c:", "危险: 格式化系统盘"),
        ("drop table", "高危: 删除数据库表"),
        ("delete from", "警告: 删除数据，需确认条件"),
        ("git push --force", "警告: 强制推送可能覆盖他人提交"),
        ("sudo", "注意: 需要管理员权限"),
    ]

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        target = task.context.get("target", task.description)
        issues = []
        for pattern, risk_desc in self.DANGEROUS_PATTERNS:
            if pattern.lower() in target.lower():
                issues.append(f"[{pattern}] {risk_desc}")

        # 自进化记忆 - 检查过去类似操作的失败案例
        past_failures = memory.recall_failed("safety_check")
        if past_failures:
            issues.append(f"历史警告: {len(past_failures)} 次失败案例，建议人工确认")

        risk = "高" if len(issues) >= 2 else ("中" if len(issues) == 1 else "低")

        return {
            "success": True,
            "risk_level": risk,
            "issues": issues,
            "approved": risk == "低",
        }


class ProjectAssistantSkill(Skill):
    """目录/助手 Skill - 协调其他原子 Skill"""
    name = "project_assistant"
    description = "项目协调助手，根据任务分解路由至其他 Skill"
    level = "catalog"

    def execute(self, task: Task, memory) -> Dict[str, Any]:
        # 基于描述的简单任务拆分
        subtasks = self._decompose(task.description)
        results = []
        for sub_desc, skill_hint in subtasks:
            results.append({
                "subtask": sub_desc,
                "suggested_skill": skill_hint,
                "status": "待执行",
            })
        return {
            "success": True,
            "subtasks": results,
            "total_subtasks": len(results),
            "orchestration_plan": "由控制器分发至具体 Skill",
        }

    @staticmethod
    def _decompose(description: str) -> List[Tuple[str, str]]:
        subtasks = []
        if "代码" in description or "编码" in description:
            subtasks.append(("审查代码质量", "code_review"))
        if "写" in description or "保存" in description:
            subtasks.append(("写入文件", "file_write"))
        if "读" in description or "查看" in description:
            subtasks.append(("读取文件", "file_read"))
        if "搜索" in description or "查资料" in description:
            subtasks.append(("网络搜索", "web_search"))
        if not subtasks:
            subtasks.append(("摘要任务", "summarize"))
        return subtasks


def build_default_registry() -> SkillRegistry:
    """构建默认 Skill 注册表"""
    registry = SkillRegistry()
    registry.register(FileReadSkill(), categories=["io", "atomic"], keywords=["读取", "file", "read", "打开"])
    registry.register(FileWriteSkill(), categories=["io", "atomic"], keywords=["写入", "write", "保存", "save"])
    registry.register(WebSearchSkill(), categories=["research"], keywords=["搜索", "search", "最新", "资料"])
    registry.register(CodeReviewSkill(), categories=["code", "composite"], keywords=["审查", "review", "代码", "code"])
    registry.register(SummarySkill(), categories=["compress", "composite"], keywords=["摘要", "总结", "压缩"])
    registry.register(SafetyCheckSkill(), categories=["security", "composite"], keywords=["安全", "审查", "风险"])
    registry.register(ProjectAssistantSkill(), categories=["orchestrator"], keywords=["项目", "助手", "分解"])
    return registry


# ============================================================
# 三、自进化记忆沉淀系统
# ============================================================

class MemorySystem:
    """记忆系统（程序化经验 / 情景记忆 / 用户画像）"""

    def __init__(self, storage_dir: str = "./.harness_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 三类记忆
        self.procedural: List[Dict[str, Any]] = []  # 程序性经验
        self.episodic: List[SkillExecutionLog] = []   # 情景记忆 (Skill 执行)
        self.user_profile: Dict[str, Any] = {
            "preferences": defaultdict(int),
            "successful_skills": defaultdict(int),
            "failed_skills": defaultdict(int),
        }

        self._load()

    # ---- 记录 API ----

    def record_execution(self, log: SkillExecutionLog):
        """记录一次 Skill 执行（情景记忆）"""
        self.episodic.append(log)

        # 更新用户画像
        if log.success:
            self.user_profile["successful_skills"][log.skill_name] += 1
        else:
            self.user_profile["failed_skills"][log.skill_name] += 1

        self._save()

    def add_lesson(self, skill_name: str, lesson: str, pattern: str):
        """添加程序化经验（从成功/失败案例中总结）"""
        entry = {
            "skill": skill_name,
            "lesson": lesson,
            "pattern": pattern,
            "created_at": datetime.datetime.now().isoformat(),
            "hit_count": 0,
        }
        self.procedural.append(entry)
        self._save()

    def update_user_preference(self, key: str, value: Any):
        """更新用户画像"""
        self.user_profile["preferences"][key] = value
        self._save()

    # ---- 回忆 API ----

    def recall_similar(self, skill_name: str, input_text: str, top_k: int = 3) -> List[SkillExecutionLog]:
        """回忆相似的历史执行"""
        key = hashlib.md5(input_text[:200].encode("utf-8"), usedforsecurity=False).hexdigest()
        # 简化：按 skill 名称过滤 + 时间倒序
        relevant = [e for e in self.episodic if e.skill_name == skill_name]
        return sorted(relevant, key=lambda x: x.timestamp, reverse=True)[:top_k]

    def recall_lessons(self, skill_name: str) -> List[Dict[str, Any]]:
        """回忆该 Skill 的程序化经验"""
        relevant = [p for p in self.procedural if p["skill"] == skill_name]
        for p in relevant:
            p["hit_count"] = p.get("hit_count", 0) + 1
        self._save()
        return relevant

    def recall_failed(self, skill_name: str) -> List[SkillExecutionLog]:
        """回忆某 Skill 的失败案例"""
        return [e for e in self.episodic if e.skill_name == skill_name and not e.success][-5:]

    def get_user_profile(self) -> Dict[str, Any]:
        """获取用户画像"""
        success = dict(self.user_profile["successful_skills"])
        fail = dict(self.user_profile["failed_skills"])
        prefs = dict(self.user_profile["preferences"])
        return {
            "preferences": prefs,
            "successful_skills": success,
            "failed_skills": fail,
            "top_skills": sorted(success.items(), key=lambda x: -x[1])[:3],
        }

    # ---- 持久化 ----

    def _save(self):
        try:
            data = {
                "procedural": self.procedural,
                "episodic": [asdict(e) for e in self.episodic[-500:]],  # 最多保留 500 条
                "user_profile": {
                    "preferences": dict(self.user_profile["preferences"]),
                    "successful_skills": dict(self.user_profile["successful_skills"]),
                    "failed_skills": dict(self.user_profile["failed_skills"]),
                },
            }
            (self.storage_dir / "memory.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def _load(self):
        try:
            path = self.storage_dir / "memory.json"
            if not path.exists():
                return
            data = json.loads(path.read_text(encoding="utf-8"))
            self.procedural = data.get("procedural", [])
            self.episodic = [SkillExecutionLog(**e) for e in data.get("episodic", [])]
            up = data.get("user_profile", {})
            self.user_profile["preferences"] = defaultdict(int, up.get("preferences", {}))
            self.user_profile["successful_skills"] = defaultdict(int, up.get("successful_skills", {}))
            self.user_profile["failed_skills"] = defaultdict(int, up.get("failed_skills", {}))
        except Exception:
            pass

    def stats(self) -> Dict[str, int]:
        return {
            "procedural_count": len(self.procedural),
            "episodic_count": len(self.episodic),
            "total_success": sum(self.user_profile["successful_skills"].values()),
            "total_failure": sum(self.user_profile["failed_skills"].values()),
        }


# ============================================================
# 四、分层上下文压缩器
# ============================================================

class ContextCompressor:
    """分层上下文压缩器

    三层压缩策略：
    1. 外部化大结果：将大工具输出写入文件，主上下文中只保留摘要
    2. 占位符压缩：将重复/冗余 token 替换为结构标记
    3. 结构化摘要：对对话历史做要点抽取
    """

    LARGE_RESULT_THRESHOLD = 2000  # 字符
    PLACEHOLDER_TOKEN = "…(已截断，见外部文件)…"

    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.archived_files: List[str] = []

    def compress_result(self, skill_name: str, result: str, save_dir: str = "./.harness_context") -> Dict[str, Any]:
        """压缩单个工具结果"""
        size = len(result)
        if size <= self.LARGE_RESULT_THRESHOLD:
            return {"compressed": False, "content": result, "size": size}

        # 外部化大结果
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        filename = f"{skill_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path(save_dir) / filename
        filepath.write_text(result, encoding="utf-8")
        self.archived_files.append(str(filepath))

        # 结构化摘要（SummarySkill 启发式）
        lines = result.splitlines()
        head = "\n".join(lines[:5])
        key_info = "\n".join([l for l in lines[:30] if any(k in l for k in ["关键", "错误", "注意", "重要"])][:5])
        summary = f"[摘要] 该输出共 {len(lines)} 行 / {size} 字符\n前几行:\n{head}\n\n关键信息:\n{key_info or '(无)'}"

        return {
            "compressed": True,
            "content": summary,
            "original_size": size,
            "compressed_size": len(summary),
            "archived_at": str(filepath),
            "placeholder": self.PLACEHOLDER_TOKEN,
        }

    def compress_conversation(self, history: List[Dict[str, str]], max_history: int = 6) -> List[Dict[str, str]]:
        """压缩对话历史：只保留最近 N 轮 + 早期摘要"""
        if len(history) <= max_history:
            return history
        early = history[:len(history) - max_history]
        recent = history[-max_history:]
        # 对早期历史做摘要
        summary_lines = [f"[早期对话摘要 · 共 {len(early)} 轮]"]
        for i, msg in enumerate(early, 1):
            role = msg.get("role", "unknown")
            text = msg.get("content", "")[:80]
            summary_lines.append(f"  {i}. [{role}] {text}")
        return [{"role": "system", "content": "\n".join(summary_lines)}] + recent

    def stats(self) -> Dict[str, Any]:
        return {
            "archived_files_count": len(self.archived_files),
            "archived_files": self.archived_files[-5:],
        }


# ============================================================
# 五、中心化多 Agent 协作
# ============================================================

class SubAgent:
    """子 Agent - 权限受限的执行单元"""

    def __init__(self, name: str, role: str, allowed_tools: List[str],
                 max_tokens: int = 8000, parent: "HarnessController" = None):
        self.name = name
        self.role = role
        self.allowed_tools = set(allowed_tools)
        self.max_tokens = max_tokens
        self.parent = parent
        self.task_log: List[str] = []
        self.token_used = 0

    def can_use(self, tool_name: str) -> bool:
        """检查是否有权限调用指定工具"""
        return tool_name in self.allowed_tools

    def execute(self, task: Task, tools_available: Dict[str, Skill]) -> Dict[str, Any]:
        """在权限控制下执行任务"""
        if not tools_available:
            return {"success": False, "error": "未提供工具集"}

        # 路由：由注册表为子 Agent 选择合适的工具
        matched = [name for name, skill in tools_available.items() if name in self.allowed_tools]
        if not matched:
            return {"success": False, "error": f"Agent '{self.name}' 没有权限调用任何工具"}

        # 简化：选择第一个匹配的 Skill 执行
        chosen = matched[0]
        skill = tools_available[chosen]
        self.task_log.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 调用 {chosen}")
        result = skill.execute(task, self.parent.memory if self.parent else MemorySystem())
        self.token_used += skill.cost * 100

        return {
            "success": True,
            "agent": self.name,
            "role": self.role,
            "tool_used": chosen,
            "result": result,
            "tokens_used": self.token_used,
        }


class HarnessController:
    """Harness 主控制器 - 协调 Skill / 记忆 / 压缩 / 子 Agent"""

    def __init__(self, project_name: str = "harness_demo"):
        self.project_name = project_name
        self.registry = build_default_registry()
        self.memory = MemorySystem(f"./.harness_projects/{project_name}/memory")
        self.compressor = ContextCompressor(self.memory)
        self.sub_agents: Dict[str, SubAgent] = {}
        self.conversation_history: List[Dict[str, str]] = []
        self.sprint_counter = 0

        # 预置几个子 Agent（不同权限等级）
        self._bootstrap_agents()

    # ---- 子 Agent 配置 ----

    def _bootstrap_agents(self):
        self.sub_agents = {
            "coder": SubAgent(
                name="coder", role="代码工程师",
                allowed_tools=["file_read", "file_write", "code_review", "summarize"],
                parent=self,
            ),
            "researcher": SubAgent(
                name="researcher", role="研究员",
                allowed_tools=["web_search", "file_read", "summarize"],
                parent=self,
            ),
            "safety": SubAgent(
                name="safety", role="安全审查员",
                allowed_tools=["safety_check", "file_read", "summarize"],
                parent=self,
            ),
            "coordinator": SubAgent(
                name="coordinator", role="项目协调者",
                allowed_tools=["project_assistant", "summarize", "file_read"],
                parent=self,
            ),
        }

    # ---- 任务执行主流程 ----

    def run(self, user_input: str) -> Dict[str, Any]:
        """执行完整的任务 - 分解 -> 路由 -> 执行 -> 审查 -> 输出"""
        start = time.time()
        self.sprint_counter += 1
        task_id = f"task_{self.sprint_counter:03d}"

        print(f"\n{'='*70}")
        print(f"🏁 Harness 启动 · Sprint #{self.sprint_counter}")
        print(f"   任务: {user_input[:60]}")
        print(f"{'='*70}\n")

        task = Task(id=task_id, description=user_input)
        self.conversation_history.append({"role": "user", "content": user_input})

        # 1) Skill 路由
        print("[1/5] 🔍 Skill 路由 ...")
        candidates = self.registry.route(task)
        print(f"      匹配到 {len(candidates)} 个 Skill:")
        for c in candidates[:3]:
            print(f"       - [{c.level.upper()}] {c.name} - {c.description}")

        # 2) 记忆检索（检查是否有相似的成功历史）
        print("\n[2/5] 🧠 记忆检索 ...")
        similar = self.memory.recall_similar(candidates[0].name if candidates else "none", user_input)
        if similar:
            print(f"      找到 {len(similar)} 条相似执行记录")
            lessons = self.memory.recall_lessons(candidates[0].name)
            if lessons:
                print(f"      程序化经验: {len(lessons)} 条")
        else:
            print("      无历史记录（首次执行此类任务）")

        # 3) 安全审查
        print("\n[3/5] 🛡  安全审查 ...")
        safety_result = self.sub_agents["safety"].execute(
            Task(id="safety", description="审查任务的安全性", context={"target": user_input}),
            self._build_skill_dict(),
        )
        risk = safety_result.get("result", {}).get("risk_level", "低")
        issues = safety_result.get("result", {}).get("issues", [])
        print(f"      风险等级: {risk}")
        for issue in issues[:3]:
            print(f"      - {issue}")

        if risk == "高":
            print("      ⚠ 高风险操作，暂停执行，请人工确认")
            return {"success": False, "stage": "safety_block", "risk": risk, "issues": issues}

        # 4) 选择合适的子 Agent 执行
        print("\n[4/5] 🤖 子 Agent 执行 ...")
        agent = self._pick_agent(user_input)
        print(f"      选择 Agent: {agent.name} ({agent.role})")
        print(f"      可用工具: {', '.join(agent.allowed_tools)}")

        # 为子 Agent 准备工具集（严格遵循权限）
        available = {name: skill for name, skill in self._build_skill_dict().items()
                     if agent.can_use(name)}

        exec_result = agent.execute(task, available)
        print(f"      执行结果: {'成功' if exec_result.get('success') else '失败'}")

        # 5) 结果压缩 + 记忆沉淀
        print("\n[5/5] 📦 结果压缩 + 记忆沉淀 ...")
        raw_result_str = json.dumps(exec_result, ensure_ascii=False)
        compressed = self.compressor.compress_result(
            candidates[0].name if candidates else "unknown", raw_result_str,
        )
        print(f"      压缩比: {compressed.get('original_size', len(raw_result_str))} -> "
              f"{compressed.get('compressed_size', len(raw_result_str))} chars")

        # 记录到情景记忆
        log = SkillExecutionLog(
            skill_name=candidates[0].name if candidates else "unknown",
            input=user_input,
            output=compressed.get("content", "")[:500],
            success=exec_result.get("success", False),
            duration_ms=int((time.time() - start) * 1000),
            tokens=agent.token_used,
        )
        self.memory.record_execution(log)
        print(f"      已保存到情景记忆 (total={len(self.memory.episodic)})")

        # 对话历史
        self.conversation_history.append({"role": "assistant", "content": compressed.get("content", "")})

        duration_ms = int((time.time() - start) * 1000)
        print(f"\n✅ 完成 · 总耗时: {duration_ms}ms")

        return {
            "success": True,
            "task_id": task_id,
            "duration_ms": duration_ms,
            "risk_level": risk,
            "agent": agent.name,
            "result": exec_result,
            "compressed": compressed,
            "memory_stats": self.memory.stats(),
        }

    # ---- 辅助方法 ----

    def _build_skill_dict(self) -> Dict[str, Skill]:
        return {s.name: s for s in self.registry.all()}

    def _pick_agent(self, description: str) -> SubAgent:
        """根据任务描述选择最合适的子 Agent"""
        if any(k in description for k in ["代码", "编程", "写", "review", "审查"]):
            return self.sub_agents["coder"]
        if any(k in description for k in ["搜索", "资料", "调研", "研究"]):
            return self.sub_agents["researcher"]
        if any(k in description for k in ["安全", "风险", "删除"]):
            return self.sub_agents["safety"]
        return self.sub_agents["coordinator"]

    # ---- 状态输出 ----

    def get_status(self) -> Dict[str, Any]:
        return {
            "project": self.project_name,
            "sprints": self.sprint_counter,
            "skills_available": len(self.registry.all()),
            "sub_agents": list(self.sub_agents.keys()),
            "memory": self.memory.stats(),
            "compressor": self.compressor.stats(),
            "conversation_turns": len(self.conversation_history),
        }

    def add_lesson(self, skill_name: str, lesson: str, pattern: str):
        """手动添加程序化经验（教学模式）"""
        self.memory.add_lesson(skill_name, lesson, pattern)
        print(f"📝 已添加经验: {lesson}")


# ============================================================
# 主入口：交互式演示
# ============================================================

def run_interactive_demo():
    """交互式演示 - 展示完整 Harness 生命周期"""
    print("="*70)
    print("🎓 Harness 驾驭系统 · 增强版 交互式演示")
    print("="*70)

    controller = HarnessController("vibelearn_demo")

    # 预置教学经验
    controller.add_lesson(
        "file_write",
        "写入前应先检查路径合法性与父目录是否存在",
        "file_write / create / 新文件",
    )
    controller.add_lesson(
        "code_review",
        "代码审查需关注敏感信息泄露，避免硬编码 token/password",
        "code_review / 安全 / 审查",
    )

    # 示例任务流
    demo_tasks = [
        "帮我审查项目中的代码质量，重点关注潜在 Bug",
        "请搜索最新的 AI Agent 架构资料并整理摘要",
        "帮我写一个简单的 Python 脚本，保存到 outputs/hello.py",
        "请分析这个项目的代码结构，并给出改进建议",
    ]

    for i, task in enumerate(demo_tasks, 1):
        result = controller.run(task)
        # 模拟压缩对话历史
        controller.conversation_history = controller.compressor.compress_conversation(
            controller.conversation_history, max_history=8
        )

    # 状态总结
    print("\n" + "="*70)
    print("📊 运行结束 · 系统状态")
    print("="*70)
    status = controller.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")

    print("\n👤 用户画像:")
    profile = controller.memory.get_user_profile()
    for k, v in profile.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    run_interactive_demo()
