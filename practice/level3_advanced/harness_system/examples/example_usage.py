"""
Harness Agent 系统使用示例

演示如何基于 Anthropic 三 Agent 架构构建 Harness 驾驭系统
"""

import os
import openai
from pathlib import Path

from harness_system import HarnessController


def create_llm_client():
    """创建 LLM 客户端"""
    return openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )


def example_simple_task():
    """示例：简单任务"""
    client = create_llm_client()

    project_path = Path("./example_projects/simple_task")
    project_path.mkdir(parents=True, exist_ok=True)

    controller = HarnessController(
        project_path=str(project_path),
        project_name="简单计算任务",
        llm_client=client
    )

    result = controller.run("计算 1 到 100 的所有质数之和")

    print("\n最终结果:")
    print(f"完成率: {result['final_status']['completion_rate']:.1%}")
    print(f"完成功能: {result['final_status']['completed_features']}")

    return result


def example_data_processing():
    """示例：数据处理任务"""
    client = create_llm_client()

    project_path = Path("./example_projects/data_processing")
    project_path.mkdir(parents=True, exist_ok=True)

    controller = HarnessController(
        project_path=str(project_path),
        project_name="数据分析任务",
        llm_client=client
    )

    result = controller.run("""
    分析销售数据文件 sales.csv，生成包含以下内容的报告:
    1. 月度销售额趋势
    2. 产品类别销量排名
    3. 异常值检测
    4. 改进建议
    """)

    return result


def example_web_app():
    """示例：Web 应用开发"""
    client = create_llm_client()

    project_path = Path("./example_projects/web_app")
    project_path.mkdir(parents=True, exist_ok=True)

    controller = HarnessController(
        project_path=str(project_path),
        project_name="待办事项应用",
        llm_client=client
    )

    result = controller.run("""
    创建一个待办事项 Web 应用:
    1. 用户可以添加、完成、删除待办事项
    2. 待办事项存储在本地
    3. 界面简洁美观
    4. 支持移动端适配
    """)

    return result


def example_multi_sprint():
    """示例：多 Sprint 迭代"""
    client = create_llm_client()

    project_path = Path("./example_projects/multi_sprint")
    project_path.mkdir(parents=True, exist_ok=True)

    controller = HarnessController(
        project_path=str(project_path),
        project_name="博客系统",
        llm_client=client
    )

    result = controller.run("""
    构建一个博客系统，包含:
    - 用户注册登录
    - 文章发布和编辑
    - 评论功能
    - 标签分类
    - 搜索功能
    """)

    for i, sprint in enumerate(result["sprints"]):
        print(f"\nSprint {i+1}:")
        print(f"  总功能: {sprint['summary']['total']}")
        print(f"  通过: {sprint['summary']['passed']}")
        print(f"  失败: {sprint['summary']['failed']}")

    return result


def demo_harness_components():
    """演示 Harness 各组件"""
    from harness_system import (
        ExternalMemory,
        ContextManager,
        ThinkingTool,
        Feature,
        TaskStatus
    )

    memory = ExternalMemory("./demo_project")
    memory.initialize_project("演示项目", "这是一个 Harness 系统演示")

    feature = Feature(
        id="demo-001",
        name="演示功能",
        description="演示 Harness 组件的使用",
        status=TaskStatus.PENDING,
        acceptance_criteria=["可以运行", "输出正确"]
    )
    memory.add_feature(feature)

    context_mgr = ContextManager()
    context = context_mgr.build_task_context(
        task_description="执行演示功能",
        project_state=memory.get_full_context(),
        feature=feature.to_dict()
    )
    print("上下文构建结果（前500字符）:")
    print(context[:500])

    thinking = ThinkingTool()
    result = thinking.think(
        problem="演示思考过程",
        constraints=["约束1", "约束2"],
        plan_ahead=3
    )
    print("\n思考过程:")
    print(result)


if __name__ == "__main__":
    print("=" * 60)
    print("Harness Agent 系统演示")
    print("=" * 60)

    print("\n1. 演示 Harness 组件:")
    demo_harness_components()

    print("\n" + "=" * 60)
    print("2. 运行实际任务（取消注释以下任一行来运行）:")
    print("=" * 60)
    print("   - example_simple_task()")
    print("   - example_data_processing()")
    print("   - example_web_app()")
    print("   - example_multi_sprint()")

    # 取消注释以下行来运行实际任务:
    # result = example_simple_task()
