#!/usr/bin/env python3
"""
Harness Agent 系统 - 主入口

使用方法:
    python run_harness.py "你的任务描述"

示例:
    python run_harness.py "帮我创建一个待办事项 Web 应用"
    python run_harness.py "分析 sales.csv 文件，生成销售报告"
"""

import os
import sys
import argparse
from pathlib import Path

import openai

from harness_system import HarnessController


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Harness Agent 系统 - Anthropic 三 Agent 架构实现",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_harness.py "帮我创建一个待办事项 Web 应用"
  python run_harness.py "分析销售数据，生成报告"
  python run_harness.py --project my_project "构建用户管理系统"
        """
    )

    parser.add_argument(
        "task",
        nargs="?",
        default=None,
        help="要执行的任务描述"
    )

    parser.add_argument(
        "--project",
        "-p",
        default="harness_project",
        help="项目名称 (默认: harness_project)"
    )

    parser.add_argument(
        "--path",
        default="./projects",
        help="项目路径 (默认: ./projects)"
    )

    parser.add_argument(
        "--model",
        default="deepseek-chat",
        help="使用的模型 (默认: deepseek-chat)"
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="交互模式"
    )

    return parser.parse_args()


def create_llm_client(model: str = "deepseek-chat"):
    """创建 LLM 客户端"""
    return openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    )


def interactive_mode(controller: HarnessController):
    """交互模式"""
    print("\n" + "=" * 60)
    print("Harness 交互模式")
    print("=" * 60)
    print("输入你的任务，或输入 'status' 查看项目状态")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input(">>> ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("退出 Harness 系统")
                break

            if user_input.lower() == "status":
                status = controller.get_project_status()
                print(f"\n项目状态: {status['project_name']}")
                print(f"完成率: {status['completion_rate']:.1%}")
                print(f"已完成: {status['completed_features']} 功能")
                print(f"待处理: {status['pending_features']} 功能\n")
                continue

            if not user_input:
                continue

            result = controller.run(user_input)

            print("\n" + "=" * 60)
            print("执行完成")
            print("=" * 60)
            print(f"完成率: {result['final_status']['completion_rate']:.1%}")

        except KeyboardInterrupt:
            print("\n\n中断执行...")
            break
        except Exception as e:
            print(f"\n错误: {e}")


def main():
    """主函数"""
    args = parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请设置 OPENAI_API_KEY 环境变量")
        print("Linux/Mac: export OPENAI_API_KEY=your_api_key")
        print("Windows: set OPENAI_API_KEY=your_api_key")
        sys.exit(1)

    project_path = Path(args.path) / args.project
    project_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Harness Agent 系统")
    print("=" * 60)
    print(f"项目: {args.project}")
    print(f"路径: {project_path}")
    print(f"模型: {args.model}")
    print("=" * 60)

    client = create_llm_client(args.model)

    controller = HarnessController(
        project_path=str(project_path),
        project_name=args.project,
        llm_client=client
    )

    if args.interactive:
        interactive_mode(controller)
    elif args.task:
        print(f"\n开始执行任务: {args.task}\n")
        result = controller.run(args.task)

        print("\n" + "=" * 60)
        print("执行完成")
        print("=" * 60)
        print(f"完成率: {result['final_status']['completion_rate']:.1%}")
        print(f"已完成: {result['final_status']['completed_features']} 功能")
        print(f"待处理: {result['final_status']['pending_features']} 功能")

        print("\n详细结果已保存到项目目录的 .harness/ 文件夹中")
    else:
        print("错误: 请提供任务描述或使用 --interactive 模式")
        print("使用 --help 查看更多选项")
        sys.exit(1)


if __name__ == "__main__":
    main()
