#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金分析系统 - 定时任务
每日 14:40 自动获取基金数据并推送报告
"""

import sys
import os
import time
import datetime
import schedule
from typing import Callable, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fund_analyzer import get_daily_fund_report


class FundReportScheduler:
    """基金报告定时任务调度器"""
    
    def __init__(self, target_hour: int = 14, target_minute: int = 40):
        self.target_hour = target_hour
        self.target_minute = target_minute
        self.is_running = False
    
    def send_report(self):
        """发送基金报告"""
        print(f"\n{'='*60}")
        print(f"🕐 定时任务触发时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        try:
            # 获取基金报告
            report = get_daily_fund_report()
            
            # 打印报告
            print(report)
            
            # 这里可以扩展：发送邮件、微信、钉钉等通知
            # self.send_email(report)
            # self.send_wechat(report)
            
        except Exception as e:
            print(f"❌ 获取基金报告失败: {e}")
    
    def run_once(self):
        """立即运行一次报告"""
        print("🔄 立即执行一次基金报告...")
        self.send_report()
    
    def start(self, run_immediately: bool = False):
        """启动定时任务"""
        if run_immediately:
            self.run_once()
        
        # 设置定时任务
        schedule_time = f"{self.target_hour:02d}:{self.target_minute:02d}"
        schedule.every().day.at(schedule_time).do(self.send_report)
        
        print(f"\n{'='*60}")
        print(f"⏰ 基金报告定时任务已启动")
        print(f"📅 目标时间: 每天 {schedule_time}")
        print(f"{'='*60}\n")
        print("💡 按 Ctrl+C 停止定时任务\n")
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 定时任务已停止")
            self.is_running = False
    
    def stop(self):
        """停止定时任务"""
        self.is_running = False


def test_notification():
    """测试通知功能"""
    print("📧 测试通知功能")
    print("这里可以添加邮件、微信等通知方式的测试代码")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="基金分析定时任务")
    parser.add_argument("--once", action="store_true", help="立即运行一次并退出")
    parser.add_argument("--hour", type=int, default=14, help="目标小时 (默认 14)")
    parser.add_argument("--minute", type=int, default=40, help="目标分钟 (默认 40)")
    parser.add_argument("--test", action="store_true", help="测试通知功能")
    
    args = parser.parse_args()
    
    # 创建调度器
    scheduler = FundReportScheduler(target_hour=args.hour, target_minute=args.minute)
    
    if args.test:
        test_notification()
    elif args.once:
        scheduler.run_once()
    else:
        scheduler.start(run_immediately=False)
