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

    parser.add_argument(
        "--no-resource-monitor",
        action="store_true",
        help="禁用资源监控"
    )

    parser.add_argument(
        "--max-memory",
        type=float,
        default=90.0,
        help="最大内存使用率 (百分比, 默认: 90.0)"
    )

    parser.add_argument(
        "--max-cpu",
        type=float,
        default=95.0,
        help="最大 CPU 使用率 (百分比, 默认: 95.0)"
    )

    parser.add_argument(
        "--max-disk",
        type=float,
        default=95.0,
        help="最大磁盘使用率 (百分比, 默认: 95.0)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="单个功能超时时间 (秒, 默认: 300)"
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
    print("可用命令:")
    print("  <任务描述>  - 执行任务")
    print("  status      - 查看项目状态")
    print("  system      - 查看系统信息")
    print("  performance - 查看性能报告")
    print("  clear-cache - 清空响应缓存")
    print("  quit/exit   - 退出")
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

            if user_input.lower() == "system":
                info = controller.get_system_info()
                print(f"\n系统信息:")
                for k, v in info.items():
                    print(f"  {k}: {v}")
                print()
                continue

            if user_input.lower() == "performance":
                report = controller.get_performance_report()
                print(f"\n性能报告:")
                if report.get("current"):
                    print(f"  总耗时: {report['current'].get('total_duration_seconds', 0):.1f}s")
                    print(f"  API 调用: {report['current'].get('total_api_calls', 0)}")
                print(f"  缓存大小: {report.get('cache_size', 0)}")
                if report.get("resource"):
                    print(f"  平均内存: {report['resource'].get('avg_memory_percent', 0):.1f}%")
                    print(f"  平均 CPU: {report['resource'].get('avg_cpu_percent', 0):.1f}%")
                print()
                continue

            if user_input.lower() == "clear-cache":
                controller.clear_cache()
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
    print(f"资源监控: {'禁用' if args.no_resource_monitor else '启用'}")
    print("=" * 60)

    client = create_llm_client(args.model)

    controller = HarnessController(
        project_path=str(project_path),
        project_name=args.project,
        llm_client=client,
        enable_resource_monitoring=not args.no_resource_monitor,
        max_memory_percent=args.max_memory,
        max_cpu_percent=args.max_cpu,
        max_disk_percent=args.max_disk,
        feature_timeout_seconds=args.timeout
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
