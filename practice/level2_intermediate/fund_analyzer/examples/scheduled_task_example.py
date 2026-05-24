#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务使用示例
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduled_task import FundReportScheduler


def example_run_once():
    """立即运行一次报告示例"""
    print("=" * 60)
    print("示例 1: 立即运行一次基金报告")
    print("=" * 60)
    
    scheduler = FundReportScheduler()
    scheduler.run_once()
    print("\n\n")


def example_custom_time():
    """自定义定时时间示例"""
    print("=" * 60)
    print("示例 2: 设置自定义时间（每天 15:00）")
    print("=" * 60)
    
    # 创建调度器，设置为每天 15:00
    scheduler = FundReportScheduler(target_hour=15, target_minute=0)
    
    # 这里只是演示，实际运行时会启动定时循环
    print("✓ 定时任务配置完成: 每天 15:00")
    print("💡 使用命令行参数运行: python scheduled_task.py --hour 15 --minute 0")
    print("\n\n")


def example_command_line_usage():
    """命令行使用示例"""
    print("=" * 60)
    print("示例 3: 命令行使用方式")
    print("=" * 60)
    
    print("""
📋 常用命令:

1. 立即运行一次:
   python scheduled_task.py --once

2. 使用默认时间（每天 14:40）启动定时任务:
   python scheduled_task.py

3. 自定义时间启动（每天 09:30）:
   python scheduled_task.py --hour 9 --minute 30

4. 测试通知功能:
   python scheduled_task.py --test
    """)


if __name__ == "__main__":
    example_run_once()
    example_custom_time()
    example_command_line_usage()
