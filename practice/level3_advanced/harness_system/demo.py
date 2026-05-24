#!/usr/bin/env python3
"""
Harness Agent 系统 - 快速演示

运行演示任务，展示 Harness 系统的工作方式
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import openai

from harness_system import HarnessController


def main():
    """运行演示"""
    print("=" * 60)
    print("Harness Agent 系统 - 快速演示")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请先设置 OPENAI_API_KEY")
        print("export OPENAI_API_KEY=your_api_key")
        sys.exit(1)

    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    )

    project_path = Path("./demo_project")
    project_path.mkdir(exist_ok=True)

    controller = HarnessController(
        project_path=str(project_path),
        project_name="演示项目",
        llm_client=client
    )

    print("\n演示任务: 计算斐波那契数列的前20项\n")

    result = controller.run("计算斐波那契数列的前20项并保存到 fibonacci.txt")

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)
    print(f"完成率: {result['final_status']['completion_rate']:.1%}")

    if result.get("sprints"):
        for i, sprint in enumerate(result["sprints"]):
            print(f"\nSprint {i+1}:")
            for feat in sprint.get("features", []):
                status = "✓" if feat.get("approved") else "✗"
                print(f"  {status} {feat.get('feature_name', 'unknown')}")


if __name__ == "__main__":
    main()
