#!/usr/bin/env python3
"""
多 Agent 任务分工系统 - 主程序入口
"""

import argparse
from .task_coordinator import TaskCoordinator


def print_report(result: dict):
    """打印任务执行报告"""
    decomposition = result['decomposition']
    execution_results = result['execution_results']
    monitor_report = result['monitor_report']
    
    print("\n" + "="*60)
    print("📋 任务执行报告")
    print("="*60)
    
    print(f"\n📝 任务拆解结果:")
    print(f"  子任务总数: {decomposition.get('total_tasks', 0)}")
    print(f"  拆解总结: {decomposition.get('summary', '')}")
    
    print("\n🔧 执行结果:")
    for task_result in execution_results:
        status_icon = "✅" if task_result['status'] == 'completed' else "❌"
        print(f"  {status_icon} {task_result.get('title', '')}: {task_result.get('status', '')}")
    
    print("\n📊 监控报告:")
    print(f"  总体进度: {monitor_report.get('overall_progress', '0%')}")
    print(f"  已完成: {monitor_report.get('completed_tasks', 0)} / {monitor_report.get('total_tasks', 0)}")
    print(f"  总结: {monitor_report.get('summary', '')}")
    
    if monitor_report.get('recommendations'):
        print("\n💡 建议:")
        for i, rec in enumerate(monitor_report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='多 Agent 任务分工系统')
    parser.add_argument('task', help='要执行的任务描述')
    parser.add_argument('-p', '--parallel', action='store_true', help='并行执行模式')
    parser.add_argument('-s', '--show-all', action='store_true', help='显示所有详细结果')
    
    args = parser.parse_args()
    
    # 创建任务协调器
    coordinator = TaskCoordinator()
    
    # 执行任务
    if args.parallel:
        result = coordinator.run_task_parallel(args.task)
    else:
        result = coordinator.run_task(args.task)
    
    # 打印报告
    print_report(result)
    
    # 显示详细结果
    if args.show_all:
        import json
        print("\n" + "="*60)
        print("📄 详细结果")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
