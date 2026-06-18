"""
Harness 增强版 - 使用示例集合
====================================================
1. Skill 路由系统演示
2. 记忆沉淀系统演示
3. 上下文压缩演示
4. 多 Agent 协作演示
5. 端到端完整任务流
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from harness_advanced import (
    HarnessController,
    SkillRegistry,
    Task,
    MemorySystem,
    ContextCompressor,
    SubAgent,
    FileReadSkill,
    FileWriteSkill,
    CodeReviewSkill,
    WebSearchSkill,
    SummarySkill,
    SafetyCheckSkill,
    ProjectAssistantSkill,
    build_default_registry,
)


def example_1_skill_routing():
    """示例 1：Skill 分层路由系统"""
    print("\n" + "="*70)
    print("【示例 1】Skill 分层路由系统")
    print("="*70)

    registry = build_default_registry()
    print(f"\n✅ 已注册 {len(registry.all())} 个 Skill:")
    for skill in registry.all():
        print(f"   - [{skill.level.upper():>9}] {skill.name:<18} {skill.description}")

    # 测试几个查询
    test_queries = [
        "帮我审查项目代码中的问题",
        "搜索最新的大模型架构",
        "读取 config.py 的内容",
        "帮我分解一个新项目任务",
    ]
    print("\n🔍 路由测试:")
    for q in test_queries:
        matched = registry.route(Task(id="t", description=q))
        names = [m.name for m in matched[:3]]
        print(f"   查询: '{q[:40]}...'")
        print(f"   -> 路由到: {names}")
        print()


def example_2_memory_system():
    """示例 2：自进化记忆沉淀系统"""
    print("\n" + "="*70)
    print("【示例 2】自进化记忆沉淀系统")
    print("="*70)

    memory = MemorySystem("./.harness_memory/demo")

    # 模拟若干次 Skill 执行
    from harness_advanced import SkillExecutionLog

    tasks = [
        ("file_read", "读取 config.py", "成功读取，200 行", True),
        ("file_read", "读取 config.py", "成功读取，200 行", True),
        ("code_review", "审查 main.py", "发现 3 处 TODO", True),
        ("code_review", "审查 broken.py", "失败 - 文件不存在", False),
        ("web_search", "搜索大模型应用", "找到 5 篇资料", True),
    ]

    print("\n📚 记录 5 次 Skill 执行到情景记忆:")
    for skill_name, inp, out, success in tasks:
        log = SkillExecutionLog(
            skill_name=skill_name, input=inp, output=out,
            success=success, duration_ms=120, tokens=500,
        )
        memory.record_execution(log)
        print(f"   - {skill_name}: {'✓' if success else '✗'} {inp}")

    # 总结程序化经验
    print("\n🎓 添加程序化经验（程序性记忆）:")
    memory.add_lesson("file_read", "读取前检查文件是否存在", "read / file_read")
    memory.add_lesson("code_review", "审查前先看文件总行数，超过 500 行建议拆分", "large file / review")
    print("   - '读取前检查文件是否存在' -> file_read")
    print("   - '审查前先检查总行数' -> code_review")

    # 回忆
    print("\n🔮 回忆 file_read 的相似执行:")
    recalled = memory.recall_similar("file_read", "读取 config.py")
    for r in recalled:
        print(f"   - [{r.timestamp[11:19]}] success={r.success} tokens={r.tokens}")

    print("\n📈 记忆统计:")
    stats = memory.stats()
    for k, v in stats.items():
        print(f"   - {k}: {v}")

    print("\n👤 用户画像:")
    profile = memory.get_user_profile()
    print(f"   - 最成功 Skill: {profile['top_skills']}")


def example_3_context_compression():
    """示例 3：分层上下文压缩器"""
    print("\n" + "="*70)
    print("【示例 3】分层上下文压缩器")
    print("="*70)

    memory = MemorySystem("./.harness_memory/compressor_demo")
    compressor = ContextCompressor(memory)

    # 构造一个大的工具输出
    large_output = "[文件内容]\n"
    for i in range(100):
        large_output += f"def function_{i}(arg):  # 函数定义行\n"
        large_output += f"    '''文档字符串 - 功能说明'''\n"
        large_output += f"    result = arg * 2 + {i}  # 简单逻辑\n"
        large_output += f"    return result\n\n"
    large_output += "\n⚠ 关键: 注意处理 None 值\nTODO: 需要重构这段代码\n"

    print(f"\n📄 原始输出: {len(large_output)} 字符 / {len(large_output.splitlines())} 行")

    # 压缩
    compressed = compressor.compress_result("file_read", large_output)
    print(f"\n✅ 压缩状态: {'已压缩' if compressed['compressed'] else '无需压缩'}")
    print(f"   原始大小: {compressed.get('original_size', len(large_output))}")
    print(f"   压缩后大小: {compressed.get('compressed_size', len(large_output))}")
    if compressed.get('compressed'):
        ratio = compressed.get('original_size', 1) / max(compressed.get('compressed_size', 1), 1)
        print(f"   压缩比: ~ {ratio:.1f}x")
        print(f"   归档文件: {compressed.get('archived_at', '')}")
        print(f"\n   压缩后摘要内容:\n{'-'*60}")
        print(compressed["content"][:400])
        print(f"{'-'*60}\n   ...")

    # 对话历史压缩
    print("\n💬 对话历史压缩:")
    history = [
        {"role": "user", "content": f"早期对话 {i} - 初始化项目，设置依赖"*5}
        for i in range(20)
    ]
    compressed_history = compressor.compress_conversation(history, max_history=5)
    print(f"   原始对话: {len(history)} 轮")
    print(f"   压缩后: {len(compressed_history)} 轮 (1 轮摘要 + 最近 5 轮)")
    print(f"   摘要轮内容: {compressed_history[0]['content'][:100]}...")


def example_4_multi_agent_collaboration():
    """示例 4：中心化多 Agent 协作"""
    print("\n" + "="*70)
    print("【示例 4】中心化多 Agent 协作")
    print("="*70)

    controller = HarnessController("multi_agent_demo")
    print(f"\n🤖 已启动 {len(controller.sub_agents)} 个子 Agent:")
    for name, agent in controller.sub_agents.items():
        print(f"   - {name:<14} (角色: {agent.role:<8} · 工具: {', '.join(agent.allowed_tools)})")

    # 子 Agent 权限测试
    test_cases = [
        ("coder", "写入文件"),  # coder 有权限
        ("coder", "rm -rf /"),   # 安全拦截
        ("researcher", "搜索资料"),
        ("safety", "安全审查"),
    ]
    print("\n🔐 子 Agent 权限与安全测试:")
    for agent_name, action in test_cases:
        agent = controller.sub_agents[agent_name]
        skill_map = controller._build_skill_dict()
        task = Task(id="test", description=action, context={"target": action, "query": action})

        # 先安全检查
        if "rm" in action.lower() or "删除" in action:
            safety = agent.execute(task, {"safety_check": SafetyCheckSkill()})
            risk = safety["result"].get("risk_level", "-")
            print(f"   Agent[{agent_name}] 执行 '{action}' -> 风险: {risk}")
        else:
            result = agent.execute(task, skill_map)
            print(f"   Agent[{agent_name}] 执行 '{action}' -> {'成功' if result['success'] else '失败'}")

    # 主 Agent 路由
    print("\n🎯 主 Agent 自动选择示例:")
    queries = ["帮我写代码", "搜索资料", "审查脚本", "分解任务"]
    for q in queries:
        agent = controller._pick_agent(q)
        print(f"   查询 '{q}' -> Agent '{agent.name}' ({agent.role})")


def example_5_end_to_end():
    """示例 5：端到端完整任务流"""
    print("\n" + "="*70)
    print("【示例 5】端到端完整任务流 (Harness 增强版)")
    print("="*70)

    controller = HarnessController("e2e_demo")

    # 教学：添加一些程序化经验
    controller.add_lesson(
        "code_review",
        "审查 Python 代码需关注: 1) import 循环 2) 异常处理 3) 类型注解",
        "python / review",
    )
    controller.add_lesson(
        "file_write",
        "写入新文件前先确保父目录存在",
        "file write / directory",
    )

    tasks = [
        "请审查项目代码，并指出潜在问题",
        "帮我搜索最新的 AI 应用资料",
        "请帮我分解这个项目，并编写一个摘要",
    ]

    results = []
    for i, task in enumerate(tasks, 1):
        print(f"\n\n🚀 Sprint #{i}: {task}")
        result = controller.run(task)
        results.append(result)

    # 最终状态
    print("\n\n" + "="*70)
    print("📊 执行完毕 · 系统状态")
    print("="*70)
    status = controller.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")

    # 记忆增长可视化
    print("\n🧠 记忆系统演化:")
    print(f"   Sprint数: {controller.sprint_counter} | "
          f"情景记忆: {len(controller.memory.episodic)} | "
          f"程序化经验: {len(controller.memory.procedural)}")


if __name__ == "__main__":
    print("🎓 Harness 驾驭系统增强版 - 示例集合\n")

    # 按序执行所有示例
    example_1_skill_routing()
    example_2_memory_system()
    example_3_context_compression()
    example_4_multi_agent_collaboration()
    example_5_end_to_end()

    print("\n" + "="*70)
    print("✅ 所有示例执行完毕")
    print("="*70)

    # 状态摘要
    print("\n💡 核心概念总结:")
    print("   1. Skill 路由 - 按关键词+层级匹配最合适的 Skill")
    print("   2. 记忆沉淀 - 程序性经验 + 情景记忆 + 用户画像 三轨演进")
    print("   3. 上下文压缩 - 大结果外部化 + 对话摘要 + 结构化要点")
    print("   4. 多 Agent - 主控制器编排 + 子 Agent 权限隔离 + Fork/Worktree 模式")
    print("   5. 安全审查 - 规则过滤 + AI 风险分类 + 人工确认三重保护")
