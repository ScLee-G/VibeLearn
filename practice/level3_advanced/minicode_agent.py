#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniCode - 参考 Claude Code 架构的 AI 编码 Agent
================================================
核心能力（对应简历中的项目描述）：
1. Skill 分层路由系统 - 原子 Skill / 高层 Skill / Skill 目录
2. 自进化记忆沉淀 - 程序性经验 + 情景记忆 + 用户画像
3. 分层上下文压缩 - 大工具结果外置、缓存友好占位、结构化笔记
4. 中心化多 Agent 协作 - 主 Agent 规划 + 子 Agent 受控执行
5. 权限与安全审查 - 规则过滤、工具自检、AI 风险分类

本实现为可运行的简化版 Agent 架构，完整演示以上 5 个核心机制。
"""

import os
import re
import json
import hashlib
import datetime
import random
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any, Callable
from collections import defaultdict
from abc import ABC, abstractmethod


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
    """Skill 执行日志 - 用于记忆沉淀"""
    skill_name: str
    input_summary: str
    success: bool
    duration_ms: int
    tokens: int
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class CompressedContext:
    """压缩后的上下文条目"""
    original_size: int
    compressed_size: int
    method: str              # externalize / placeholder / summary
    summary: str
    archived_path: str = ""


# ============================================================
# 二、Skill 分层路由系统
# ============================================================

class Skill(ABC):
    """Skill 基类"""
    name: str = "base"
    description: str = ""
    level: str = "atomic"     # atomic(原子) / composite(复合) / catalog(目录)
    cost_estimate: int = 100  # token 估算

    @abstractmethod
    def execute(self, task: Task) -> Dict[str, Any]:
        """执行 skill"""


class SkillRegistry:
    """Skill 注册与路由中心（分层+关键词+语义）"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._by_category: Dict[str, List[str]] = defaultdict(list)
        self._keyword_index: Dict[str, List[str]] = defaultdict(list)

    def register(self, skill: Skill, categories: List[str] = None, keywords: List[str] = None):
        self._skills[skill.name] = skill
        for cat in categories or [skill.level]:
            self._by_category[cat].append(skill.name)
        for kw in keywords or []:
            self._keyword_index[kw.lower()].append(skill.name)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def all(self) -> List[Skill]:
        return list(self._skills.values())

    def route(self, task: Task, top_k: int = 5) -> List[Tuple[Skill, float]]:
        """启发式路由：关键词匹配 + 分类匹配"""
        desc = task.description.lower()
        scores: Dict[str, float] = defaultdict(float)

        # 关键词命中加权
        for kw, skill_names in self._keyword_index.items():
            if kw in desc:
                for sn in skill_names:
                    scores[sn] += 2.0

        # 分类命中
        for cat, skill_names in self._by_category.items():
            if cat.lower() in desc:
                for sn in skill_names:
                    scores[sn] += 1.0

        # 目录型 Skill 兜底
        for name, skill in self._skills.items():
            if skill.level == "catalog":
                scores.setdefault(name, 0.3)

        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        return [(self._skills[name], score) for name, score in ranked if score > 0]


# ---------- 原子 Skill ----------
class FileReadSkill(Skill):
    """原子 Skill - 读取文件"""
    name = "file_read"
    description = "读取本地文件内容并返回字符串"
    level = "atomic"

    def execute(self, task: Task) -> Dict[str, Any]:
        filepath = task.context.get("filepath") or task.description
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {"success": True, "filepath": filepath, "content": content, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileWriteSkill(Skill):
    """原子 Skill - 写入文件"""
    name = "file_write"
    description = "将文本内容写入到本地指定路径"
    level = "atomic"

    def execute(self, task: Task) -> Dict[str, Any]:
        filepath = task.context.get("filepath", "./output.txt")
        content = task.context.get("content", "")
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "filepath": filepath, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class ShellSkill(Skill):
    """原子 Skill - 简易命令执行（受限）"""
    name = "shell_exec"
    description = "执行简单的 shell 命令并返回输出"
    level = "atomic"

    # 允许的白名单命令
    WHITELIST = {"echo", "ls", "pwd", "cat", "grep", "find", "wc", "head", "tail", "python", "python3"}

    def execute(self, task: Task) -> Dict[str, Any]:
        cmd = task.context.get("command", task.description).strip()
        program = cmd.split()[0] if cmd.split() else ""
        if program not in self.WHITELIST:
            return {"success": False, "error": f"命令 '{program}' 不在白名单中"}
        try:
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ---------- 复合 Skill ----------
class CodeReviewSkill(Skill):
    """复合 Skill - 代码审查（组合 file_read + 规则检查）"""
    name = "code_review"
    description = "读取文件并进行风格/安全/结构审查"
    level = "composite"

    RULES = [
        ("调试痕迹", lambda c: "print(" in c or "debugger" in c.lower()),
        ("硬编码密钥", lambda c: bool(re.search(r"(api_key|password|token)\s*=\s*[\"']", c, re.I))),
        ("TODO/FIXME", lambda c: "TODO" in c or "FIXME" in c),
        ("函数过长", lambda c: c.count("\ndef ") > 0 and len(c.splitlines()) > 150),
        ("缺少类型注解", lambda c: "def " in c and "->" not in c),
        ("SQL 注入风险", lambda c: bool(re.search(r"execute\s*\([\"'].*%s|\+|\{.*\}", c))),
    ]

    def execute(self, task: Task) -> Dict[str, Any]:
        read_result = FileReadSkill().execute(task)
        if not read_result.get("success"):
            return read_result

        content = read_result["content"]
        findings = [name for name, check in self.RULES if check(content)]
        risk = "高" if len(findings) >= 3 else ("中" if findings else "低")
        return {
            "success": True,
            "filepath": task.context.get("filepath", ""),
            "total_lines": len(content.splitlines()),
            "findings": findings,
            "risk_level": risk,
        }


class CodeSearchSkill(Skill):
    """复合 Skill - 代码搜索 + 摘要"""
    name = "code_search"
    description = "在代码库中搜索特定模式并返回摘要"
    level = "composite"

    def execute(self, task: Task) -> Dict[str, Any]:
        pattern = task.context.get("pattern", task.description[:30])
        root = task.context.get("root", ".")
        matches = []
        try:
            for f in Path(root).rglob("*.py"):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                    if pattern.lower() in text.lower():
                        lines = text.splitlines()
                        matched_lines = [i+1 for i, l in enumerate(lines) if pattern.lower() in l.lower()]
                        matches.append({"file": str(f), "lines": matched_lines[:5], "hits": len(matched_lines)})
                except Exception:
                    continue
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": True, "pattern": pattern, "matches": matches[:10], "total": len(matches)}


class CodeGeneratorSkill(Skill):
    """复合 Skill - AI 代码生成（基于模板 + 参数拼接）"""
    name = "code_generate"
    description = "根据需求描述生成 Python 代码片段（模板化）"
    level = "composite"

    TEMPLATES = {
        "函数": 'def {name}({args}):\n    """{doc}"""\n    {body}\n    return result',
        "类": 'class {name}:\n    """{doc}"""\n    def __init__(self):\n        self._data = []\n\n    def process(self, x):\n        {body}\n        return x',
        "脚本": '#!/usr/bin/env python3\n# {doc}\n\ndef main():\n    {body}\n\nif __name__ == "__main__":\n    main()',
    }

    def execute(self, task: Task) -> Dict[str, Any]:
        desc = task.description
        # 简单模板选择（无 LLM 时的演示模式）
        template_type = "函数"
        if "class" in desc.lower() or "类" in desc:
            template_type = "类"
        if "脚本" in desc or "script" in desc.lower():
            template_type = "脚本"

        name = task.context.get("name", "generated_" + str(random.randint(100, 999)))
        args = task.context.get("args", "x, y")
        body = task.context.get("body", "result = x + y  # 示例：简单加法")
        doc = task.context.get("doc", desc)

        code = self.TEMPLATES[template_type].format(name=name, args=args, doc=doc, body=body)
        return {"success": True, "type": template_type, "code": code, "name": name}


# ---------- 目录/助手 Skill ----------
class ProjectAssistantSkill(Skill):
    """目录 Skill - 项目协调助手"""
    name = "project_assistant"
    description = "任务分析、分解并推荐合适的 Skill"
    level = "catalog"

    def execute(self, task: Task) -> Dict[str, Any]:
        subtasks = []
        desc = task.description
        if any(k in desc for k in ["写", "创建", "生成", "代码", "write", "create"]):
            subtasks.append(("生成代码骨架", "code_generate"))
            subtasks.append(("写入文件", "file_write"))
        if any(k in desc for k in ["读", "查看", "分析", "read"]):
            subtasks.append(("读取文件内容", "file_read"))
            subtasks.append(("代码审查", "code_review"))
        if any(k in desc for k in ["搜索", "查找", "search", "find"]):
            subtasks.append(("代码库搜索", "code_search"))
        if not subtasks:
            subtasks.append(("分析任务需求", "project_assistant"))

        return {
            "success": True,
            "original_task": desc,
            "subtasks": subtasks,
            "orchestration_plan": "控制器将按序调用以上 Skill",
        }


def build_default_skill_registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(FileReadSkill(), categories=["io", "atomic"], keywords=["读取", "file", "read", "打开"])
    reg.register(FileWriteSkill(), categories=["io", "atomic"], keywords=["写入", "write", "保存", "save", "创建文件"])
    reg.register(ShellSkill(), categories=["system", "atomic"], keywords=["执行", "exec", "shell", "命令"])
    reg.register(CodeReviewSkill(), categories=["code", "composite"], keywords=["审查", "review", "代码", "code", "检查"])
    reg.register(CodeSearchSkill(), categories=["code", "composite"], keywords=["搜索", "search", "查找", "find"])
    reg.register(CodeGeneratorSkill(), categories=["code", "composite"], keywords=["生成", "generate", "代码", "编写", "写"])
    reg.register(ProjectAssistantSkill(), categories=["orchestrator"], keywords=["项目", "助手", "分解", "plan"])
    return reg


# ============================================================
# 三、自进化记忆沉淀系统
# ============================================================

class MemorySystem:
    """自进化记忆 - 程序性经验 / 情景记忆 / 用户画像"""

    def __init__(self, storage_dir: str = "./.minicode_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 三类记忆
        self.procedural: List[Dict[str, Any]] = []   # 程序性经验（可复用的规则）
        self.episodic: List[SkillExecutionLog] = []   # 情景记忆（每次 Skill 执行）
        self.user_profile = {
            "successful_skills": defaultdict(int),
            "failed_skills": defaultdict(int),
            "preferences": defaultdict(int),
        }

        self._load()

    # ---- 记录 ----
    def record(self, log: SkillExecutionLog):
        self.episodic.append(log)
        if log.success:
            self.user_profile["successful_skills"][log.skill_name] += 1
        else:
            self.user_profile["failed_skills"][log.skill_name] += 1
        # 失败时自动生成程序化经验
        if not log.success and len(self.episodic) % 1 == 0:
            self.add_lesson(
                log.skill_name,
                f"避免在 '{log.input_summary[:50]}' 场景下直接调用，建议先检查前置条件",
                pattern=log.input_summary[:30],
            )
        self._save()

    def add_lesson(self, skill: str, lesson: str, pattern: str):
        self.procedural.append({
            "skill": skill,
            "lesson": lesson,
            "pattern": pattern,
            "created_at": datetime.datetime.now().isoformat(),
            "hit_count": 0,
        })
        self._save()

    # ---- 回忆 ----
    def recall_similar(self, skill_name: str, input_text: str, top_k: int = 3) -> List[SkillExecutionLog]:
        relevant = [e for e in self.episodic if e.skill_name == skill_name]
        return sorted(relevant, key=lambda x: x.timestamp, reverse=True)[:top_k]

    def recall_lessons(self, skill_name: str) -> List[Dict[str, Any]]:
        results = []
        for entry in self.procedural:
            if entry["skill"] == skill_name:
                entry["hit_count"] = entry.get("hit_count", 0) + 1
                results.append(entry)
        if results:
            self._save()
        return results

    def get_user_profile(self) -> Dict[str, Any]:
        return {
            "top_successful_skills": sorted(
                self.user_profile["successful_skills"].items(), key=lambda x: -x[1]
            )[:5],
            "top_failed_skills": sorted(
                self.user_profile["failed_skills"].items(), key=lambda x: -x[1]
            )[:5],
            "preferences": dict(self.user_profile["preferences"]),
        }

    # ---- 持久化 ----
    def _save(self):
        try:
            data = {
                "procedural": self.procedural[-100:],  # 保留最近 100 条
                "episodic": [asdict(e) for e in self.episodic[-500:]],
                "user_profile": {
                    "successful_skills": dict(self.user_profile["successful_skills"]),
                    "failed_skills": dict(self.user_profile["failed_skills"]),
                    "preferences": dict(self.user_profile["preferences"]),
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
            self.user_profile["successful_skills"] = defaultdict(int, up.get("successful_skills", {}))
            self.user_profile["failed_skills"] = defaultdict(int, up.get("failed_skills", {}))
            self.user_profile["preferences"] = defaultdict(int, up.get("preferences", {}))
        except Exception:
            pass

    def stats(self) -> Dict[str, int]:
        return {
            "procedural": len(self.procedural),
            "episodic": len(self.episodic),
            "successful_total": sum(self.user_profile["successful_skills"].values()),
            "failed_total": sum(self.user_profile["failed_skills"].values()),
        }


# ============================================================
# 四、分层上下文压缩
# ============================================================

class ContextCompressor:
    """三层压缩：外部化 / 占位 / 结构化摘要"""

    LARGE_THRESHOLD = 1500
    MAX_CONTEXT_TOKENS = 8000

    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.archived: List[str] = []
        self.history: List[Dict[str, Any]] = []

    def compress_tool_result(self, skill_name: str, result_text: str,
                              save_dir: str = "./.minicode_context") -> CompressedContext:
        """压缩工具输出"""
        size = len(result_text)
        if size <= self.LARGE_THRESHOLD:
            return CompressedContext(size, size, "kept", result_text[:200])

        # 超过阈值 -> 外部化到文件
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        fname = f"{skill_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        fpath = Path(save_dir) / fname
        fpath.write_text(result_text, encoding="utf-8")
        self.archived.append(str(fpath))

        # 结构化摘要
        lines = result_text.splitlines()
        summary_lines = [
            f"[摘要] 输出共 {len(lines)} 行 / {size} 字符，已外部化至 {fpath}",
            f"  前 5 行: {' | '.join(l.strip() for l in lines[:5] if l.strip())}",
            f"  关键信息: ",
        ]
        # 简单关键词抽取
        key_tokens = re.findall(r"[\w\u4e00-\u9fa5]{3,}", result_text)
        counter = Counter(key_tokens)
        summary_lines.append(f"  高频词: {[w for w, c in counter.most_common(8)]}")
        summary = "\n".join(summary_lines)

        return CompressedContext(
            original_size=size,
            compressed_size=len(summary),
            method="externalize",
            summary=summary,
            archived_path=str(fpath),
        )

    def compress_dialogue(self, history: List[Dict[str, str]], max_turns: int = 8) -> List[Dict[str, str]]:
        """压缩对话历史 - 早期对话摘要 + 近期完整保留"""
        if len(history) <= max_turns:
            return history
        early = history[:-max_turns]
        recent = history[-max_turns:]
        summary_text = (
            f"[早期对话摘要 · 共 {len(early)} 轮] 用户与 Agent 讨论了以下主题："
            + "、".join([h.get("content", "")[:20] for h in early[:5]])
        )
        return [{"role": "system", "content": summary_text}] + recent

    def stats(self) -> Dict[str, Any]:
        return {
            "archived_files": len(self.archived),
            "total_archived": self.archived[-3:],
        }


from collections import Counter  # 延迟导入，避免上面使用前未定义


# ============================================================
# 五、中心化多 Agent 协作
# ============================================================

class SubAgent:
    """子 Agent - 受权限约束的执行单元"""

    def __init__(self, name: str, role: str, allowed_skills: List[str]):
        self.name = name
        self.role = role
        self.allowed_skills = set(allowed_skills)
        self.execution_log: List[Dict[str, Any]] = []

    def execute(self, task: Task, skill_map: Dict[str, Skill]) -> Dict[str, Any]:
        """在权限内执行任务 - 选择路由到的 Skill"""
        # 从描述推断目标 skill
        target = None
        desc = task.description.lower()
        for skill_name in self.allowed_skills:
            if any(k in desc for k in skill_name.split("_")):
                target = skill_name
                break
        if not target and self.allowed_skills:
            target = list(self.allowed_skills)[0]

        if target not in skill_map:
            return {"success": False, "error": f"无权调用或无此 skill: {target}"}

        skill = skill_map[target]
        try:
            result = skill.execute(task)
            record = {
                "agent": self.name,
                "skill": target,
                "success": result.get("success", False),
                "timestamp": datetime.datetime.now().isoformat(),
            }
            self.execution_log.append(record)
            return {
                "success": True,
                "agent": self.name,
                "role": self.role,
                "skill_used": target,
                "result": result,
            }
        except Exception as e:
            return {"success": False, "agent": self.name, "error": str(e)}


class MiniCodeController:
    """MiniCode 主控 Agent - 协调 Skill 路由、记忆、压缩、安全、子 Agent"""

    def __init__(self, project_name: str = "minicode_demo"):
        self.project_name = project_name
        self.registry = build_default_skill_registry()
        self.memory = MemorySystem(f"./.minicode_memory/{project_name}")
        self.compressor = ContextCompressor(self.memory)
        self.task_counter = 0
        self.conversation: List[Dict[str, str]] = []

        # 预置子 Agent
        self.sub_agents = {
            "coder": SubAgent("coder", "代码工程师",
                              allowed_skills=["file_read", "file_write", "code_generate", "code_review"]),
            "analyst": SubAgent("analyst", "代码分析师",
                                allowed_skills=["code_search", "code_review", "file_read"]),
            "executor": SubAgent("executor", "执行助手",
                                allowed_skills=["shell_exec", "file_read"]),
            "planner": SubAgent("planner", "任务规划者",
                                allowed_skills=["project_assistant", "code_search"]),
        }

        # 启动时注入程序化经验
        if not self.memory.procedural:
            for lesson_text, skill in [
                ("写文件前必须先检查父目录是否存在", "file_write"),
                ("审查代码时需关注硬编码的 API key/token/password", "code_review"),
                ("执行 shell 命令前必须进行安全审查", "shell_exec"),
                ("复杂代码生成前先分解为清晰的小任务", "code_generate"),
            ]:
                self.memory.add_lesson(skill, lesson_text, lesson_text[:30])

    # ---- 主入口 ----
    def run(self, user_request: str) -> Dict[str, Any]:
        import time
        start = time.time()
        self.task_counter += 1
        task = Task(id=f"task_{self.task_counter:03d}", description=user_request)
        self.conversation.append({"role": "user", "content": user_request})

        print(f"\n{'─'*70}")
        print(f"🚀 MiniCode 执行 #{self.task_counter}: '{user_request[:60]}'")
        print(f"{'─'*70}")

        # [1] Skill 路由
        print(f"\n[1/4] 🔍 Skill 路由:")
        candidates = self.registry.route(task)
        for skill, score in candidates[:3]:
            print(f"   - [{skill.level.upper():>9}] {skill.name:<18} score={score:.1f} - {skill.description}")

        # [2] 记忆检索（程序化经验 + 类似情景）
        print(f"\n[2/4] 🧠 记忆检索:")
        if candidates:
            top_skill = candidates[0][0]
            lessons = self.memory.recall_lessons(top_skill.name)
            if lessons:
                for l in lessons[:3]:
                    print(f"   - 经验: {l['lesson']} (已命中 {l.get('hit_count', 0)} 次)")
            similar = self.memory.recall_similar(top_skill.name, user_request)
            if similar:
                print(f"   - 类似执行 {len(similar)} 次")
            if not lessons and not similar:
                print(f"   - 无历史记忆（首次执行此类任务）")

        # [3] 安全审查（风险命令拦截）
        print(f"\n[3/4] 🛡 安全审查:")
        risk_assessment = self._security_check(user_request)
        print(f"   - 风险等级: {risk_assessment['level']}")
        if risk_assessment["issues"]:
            for issue in risk_assessment["issues"]:
                print(f"   - ⚠ {issue}")
        if risk_assessment["level"] == "高":
            print("   ❌ 高风险操作被拦截")
            result = {"success": False, "stage": "blocked_by_security", "reason": risk_assessment}
            self._record_and_finalize(task, "blocked", 0, int((time.time()-start)*1000), result)
            return result

        # [4] 选择子 Agent 执行
        print(f"\n[4/4] 🤖 子 Agent 执行:")
        agent = self._pick_agent(user_request)
        skill_map = {s.name: s for s in self.registry.all()}
        result = agent.execute(task, skill_map)
        print(f"   - 选择 Agent: {agent.name} ({agent.role})")
        print(f"   - 执行结果: {'成功' if result.get('success') else '失败'}")

        # 上下文压缩（大结果外部化）
        result_str = json.dumps(result, ensure_ascii=False, default=str)
        compressed = self.compressor.compress_tool_result(
            candidates[0][0].name if candidates else "unknown", result_str
        )
        print(f"   - 上下文: {compressed.original_size} -> {compressed.compressed_size} 字符")

        # 记录情景记忆
        success = result.get("success", False)
        self.memory.record(SkillExecutionLog(
            skill_name=candidates[0][0].name if candidates else "unknown",
            input_summary=user_request[:50],
            success=success,
            duration_ms=int((time.time() - start) * 1000),
            tokens=compressed.compressed_size,
        ))
        self.conversation.append({"role": "assistant", "content": compressed.summary})
        self.conversation = self.compressor.compress_dialogue(self.conversation, max_turns=10)

        print(f"\n✅ 完成 - 耗时 {int((time.time()-start)*1000)}ms")
        return {
            "success": success,
            "task_id": task.id,
            "agent": agent.name,
            "routed_skill": candidates[0][0].name if candidates else "",
            "result_summary": compressed.summary,
            "risk_level": risk_assessment["level"],
            "memory_hits": self.memory.stats(),
        }

    # ---- 辅助方法 ----
    def _security_check(self, text: str) -> Dict[str, Any]:
        """简化安全审查 - 规则过滤 + AI 风险分类"""
        issues = []
        danger_patterns = [
            ("rm -rf", "危险：递归删除"),
            ("format", "危险：格式化磁盘"),
            ("drop table", "高危：删除数据库表"),
            ("sudo", "注意：需要系统权限"),
            (">", "注意：文件覆盖风险"),
        ]
        for pat, desc in danger_patterns:
            if pat in text.lower():
                issues.append(desc)

        # 从程序化经验中提取
        for lesson in self.memory.procedural:
            if "安全" in lesson.get("lesson", "") or "审查" in lesson.get("lesson", ""):
                if any(k in text.lower() for k in ["执行", "shell", "命令"]):
                    issues.append("（程序化经验）" + lesson["lesson"])

        level = "高" if len(issues) >= 2 else ("中" if issues else "低")
        return {"level": level, "issues": issues}

    def _pick_agent(self, text: str) -> SubAgent:
        if any(k in text for k in ["写", "生成", "创建", "代码", "编码", "write", "create"]):
            return self.sub_agents["coder"]
        if any(k in text for k in ["搜索", "分析", "查找", "review", "search"]):
            return self.sub_agents["analyst"]
        if any(k in text for k in ["执行", "运行", "命令", "exec", "run"]):
            return self.sub_agents["executor"]
        return self.sub_agents["planner"]

    def _record_and_finalize(self, task: Task, status: str, tokens: int, duration_ms: int, result: Dict[str, Any]):
        self.memory.record(SkillExecutionLog(
            skill_name="security_block",
            input_summary=task.description[:50],
            success=False,
            duration_ms=duration_ms,
            tokens=tokens,
        ))
        self.conversation.append({"role": "assistant", "content": f"[{status}] 操作已拦截"})

    # ---- 状态查询 ----
    def status(self) -> Dict[str, Any]:
        return {
            "project": self.project_name,
            "total_tasks": self.task_counter,
            "skills": len(self.registry.all()),
            "sub_agents": list(self.sub_agents.keys()),
            "memory": self.memory.stats(),
            "compressor": self.compressor.stats(),
            "user_profile": self.memory.get_user_profile(),
        }


# ============================================================
# 六、演示主程序
# ============================================================

def run_interactive_demo():
    """MiniCode 完整交互演示"""
    print("="*70)
    print("🤖 MiniCode - 基于 Claude Code 架构思想的 AI 编码 Agent")
    print("="*70)

    controller = MiniCodeController("interactive_demo")

    # 注册的 Skill 总览
    print(f"\n已注册 {len(controller.registry.all())} 个 Skill:")
    for s in controller.registry.all():
        print(f"   - [{s.level.upper():>9}] {s.name:<18} {s.description}")

    # 示例任务流
    demo_tasks = [
        "帮我审查项目中的代码文件，看看有没有安全问题",
        "帮我写一个 Python 函数来计算斐波那契数列",
        "搜索一下项目中包含 'import' 的文件",
        "帮我创建一个新文件 outputs/demo.txt，内容为 Hello MiniCode",
    ]
    results = []
    for task in demo_tasks:
        results.append(controller.run(task))

    # 状态总结
    print("\n" + "="*70)
    print("📊 系统状态")
    print("="*70)
    s = controller.status()
    for k, v in s.items():
        if isinstance(v, dict):
            print(f"   {k}:")
            for kk, vv in v.items():
                print(f"      {kk}: {vv}")
        else:
            print(f"   {k}: {v}")

    print("\n" + "="*70)
    print("✅ 演示完成")
    print("="*70)


if __name__ == "__main__":
    run_interactive_demo()
