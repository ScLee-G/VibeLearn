#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金分析系统使用示例
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fund_analyzer import get_daily_fund_report, FundAnalyzer


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 获取每日基金报告")
    print("=" * 60)
    report = get_daily_fund_report()
    print(report)
    print("\n\n")


def example_custom_analysis():
    """自定义分析示例"""
    print("=" * 60)
    print("示例 2: 自定义分析")
    print("=" * 60)
    
    analyzer = FundAnalyzer()
    
    # 获取市场概览
    overview = analyzer.get_market_overview()
    print(f"市场平均涨跌幅：{overview['avg_change']:+}%")
    print(f"上涨基金：{overview['up_count']}只")
    print(f"下跌基金：{overview['down_count']}只")
    print()
    
    # 生成投资建议
    suggestions = analyzer.generate_investment_suggestions(top_n=3)
    print("精选投资建议（Top 3）：")
    for i, s in enumerate(suggestions, 1):
        print(f"{i}. {s.fund_name}")
        print(f"   操作：{s.action}")
        print(f"   建议仓位：{s.target_position}%")
        print()


if __name__ == "__main__":
    example_basic_usage()
    example_custom_analysis()
