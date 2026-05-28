#!/usr/bin/env python3
"""
多 Agent 代码审查系统 - 主程序入口
"""

import argparse
import os
from .review_controller import ReviewController


def load_code_from_file(file_path: str) -> str:
    """从文件加载代码"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def print_report(review_result: dict):
    """打印审查报告"""
    summary = review_result['summary']
    
    print("\n" + "="*60)
    print("📋 代码审查报告")
    print("="*60)
    
    print(f"\n整体评级: {summary.get('overall_rating', '未知')}")
    print(f"问题总数: {summary.get('total_issues', 0)}")
    print(f"高优先级问题: {summary.get('high_severity_count', 0)}")
    print(f"\n总结: {summary.get('summary', '')}")
    
    if summary.get('recommendations'):
        print("\n📝 改进建议:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print(f"\n📄 详细报告:\n{summary.get('detailed_report', '')}")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='多 Agent 代码审查系统')
    parser.add_argument('code', nargs='?', help='要审查的代码文件路径或代码内容')
    parser.add_argument('-f', '--file', help='代码文件路径')
    parser.add_argument('-p', '--parallel', action='store_true', help='并行审查模式')
    parser.add_argument('-s', '--show-all', action='store_true', help='显示所有 Agent 的详细结果')
    
    args = parser.parse_args()
    
    # 获取代码
    if args.file:
        code = load_code_from_file(args.file)
    elif args.code:
        if os.path.isfile(args.code):
            code = load_code_from_file(args.code)
        else:
            code = args.code
    else:
        print("请提供要审查的代码或文件路径")
        parser.print_help()
        return
    
    # 创建审查控制器
    controller = ReviewController()
    
    # 执行审查
    if args.parallel:
        result = controller.run_review_parallel(code)
    else:
        result = controller.run_review(code)
    
    # 打印报告
    print_report(result)
    
    # 显示详细结果
    if args.show_all:
        print("\n" + "="*60)
        print("🔍 各 Agent 详细结果")
        print("="*60)
        for agent_name, agent_result in result['individual_results'].items():
            print(f"\n--- {agent_name} ---")
            import json
            print(json.dumps(agent_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
