#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金分析系统 - 每日市场涨跌分析与投资建议
"""

import datetime
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class FundInfo:
    """基金信息"""
    code: str
    name: str
    type: str  # 股票型、混合型、债券型、指数型
    current_price: float
    change_percent: float
    change_amount: float
    volume: float
    pe_ratio: float
    pb_ratio: float


@dataclass
class InvestmentSuggestion:
    """投资建议"""
    fund_code: str
    fund_name: str
    action: str  # 建仓、加仓、减仓、持有
    target_position: float  # 目标仓位百分比
    reason: str


class FundAnalyzer:
    """基金分析器"""
    
    def __init__(self):
        self.mock_funds = self._init_mock_funds()
    
    def _init_mock_funds(self) -> List[FundInfo]:
        """初始化模拟基金数据（实际项目中应从API获取）"""
        funds_data = [
            ("000001", "沪深300指数基金", "指数型", 1.523, 0.85, 0.013, 12345678, 12.5, 1.3),
            ("000002", "科技创新混合基金", "混合型", 2.345, -1.23, -0.029, 8765432, 35.2, 4.5),
            ("000003", "消费龙头股票基金", "股票型", 3.210, 2.15, 0.068, 23456789, 28.7, 3.2),
            ("000004", "医疗健康债券基金", "债券型", 1.089, 0.15, 0.002, 5678901, 18.9, 1.1),
            ("000005", "新能源指数基金", "指数型", 1.876, -2.45, -0.047, 15678901, 45.3, 5.8),
            ("000006", "金融行业混合基金", "混合型", 2.123, 0.56, 0.012, 9876543, 10.2, 0.9),
            ("000007", "军工主题股票基金", "股票型", 1.789, 1.89, 0.033, 11234567, 52.1, 2.8),
            ("000008", "纯债增强基金", "债券型", 1.234, 0.08, 0.001, 7654321, 8.5, 0.8),
            ("000009", "创业板指数基金", "指数型", 1.456, -0.98, -0.014, 18765432, 42.3, 3.5),
            ("000010", "价值成长混合基金", "混合型", 2.678, 0.34, 0.009, 13456789, 22.8, 1.9)
        ]
        
        return [FundInfo(*data) for data in funds_data]
    
    def get_market_overview(self) -> Dict:
        """获取市场概览"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 计算平均涨跌幅
        avg_change = sum(f.change_percent for f in self.mock_funds) / len(self.mock_funds)
        
        # 统计涨跌数量
        up_count = sum(1 for f in self.mock_funds if f.change_percent > 0)
        down_count = sum(1 for f in self.mock_funds if f.change_percent < 0)
        flat_count = sum(1 for f in self.mock_funds if f.change_percent == 0)
        
        # 按类型分组
        type_stats = {}
        for fund in self.mock_funds:
            if fund.type not in type_stats:
                type_stats[fund.type] = {"count": 0, "avg_change": 0}
            type_stats[fund.type]["count"] += 1
            type_stats[fund.type]["avg_change"] += fund.change_percent
        
        for fund_type in type_stats:
            type_stats[fund_type]["avg_change"] /= type_stats[fund_type]["count"]
        
        return {
            "date": today,
            "avg_change": round(avg_change, 2),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "type_stats": type_stats,
            "top_gainers": sorted(self.mock_funds, key=lambda x: -x.change_percent)[:3],
            "top_losers": sorted(self.mock_funds, key=lambda x: x.change_percent)[:3]
        }
    
    def analyze_fund(self, fund: FundInfo) -> Dict:
        """分析单只基金"""
        score = 0
        reasons = []
        
        # 基于估值分析
        if fund.pe_ratio < 15:
            score += 30
            reasons.append("PE估值较低，具有安全边际")
        elif fund.pe_ratio > 40:
            score -= 20
            reasons.append("PE估值偏高，注意风险")
        
        if fund.pb_ratio < 2:
            score += 20
            reasons.append("PB估值合理")
        elif fund.pb_ratio > 4:
            score -= 15
            reasons.append("PB估值较高")
        
        # 基于涨跌幅分析
        if fund.change_percent > 2:
            score += 10
            reasons.append("今日表现强势")
        elif fund.change_percent < -2:
            score -= 10
            reasons.append("今日回调较大")
        
        # 基于成交量
        if fund.volume > 10000000:
            score += 10
            reasons.append("成交量活跃，流动性好")
        
        return {
            "fund": fund,
            "score": score,
            "reasons": reasons,
            "risk_level": "低" if score > 40 else "中" if score > 20 else "高"
        }
    
    def generate_investment_suggestions(self, top_n: int = 5) -> List[InvestmentSuggestion]:
        """生成投资建议"""
        # 分析所有基金
        analyzed = [self.analyze_fund(fund) for fund in self.mock_funds]
        
        # 按得分排序
        sorted_funds = sorted(analyzed, key=lambda x: -x["score"])
        
        suggestions = []
        for i, item in enumerate(sorted_funds[:top_n]):
            fund = item["fund"]
            score = item["score"]
            reasons = item["reasons"]
            
            # 根据得分确定操作建议
            if score >= 40:
                action = "建仓/加仓"
                target = random.uniform(15, 25)
            elif score >= 25:
                action = "建仓"
                target = random.uniform(10, 15)
            elif score >= 10:
                action = "持有"
                target = random.uniform(5, 10)
            else:
                action = "减仓/观望"
                target = random.uniform(0, 5)
            
            reason_text = "；".join(reasons) if reasons else "综合评估"
            
            suggestions.append(InvestmentSuggestion(
                fund_code=fund.code,
                fund_name=fund.name,
                action=action,
                target_position=round(target, 1),
                reason=reason_text
            ))
        
        return suggestions
    
    def format_report(self) -> str:
        """格式化报告"""
        overview = self.get_market_overview()
        suggestions = self.generate_investment_suggestions()
        
        report = []
        report.append("📊 " + "="*50)
        report.append(f"📅 日期：{overview['date']}")
        report.append("📊 " + "="*50)
        report.append("")
        report.append("📈 【市场概览】")
        report.append(f"   平均涨跌幅：{overview['avg_change']:+}%")
        report.append(f"   上涨：{overview['up_count']}只  |  下跌：{overview['down_count']}只  |  平盘：{overview['flat_count']}只")
        report.append("")
        report.append("🏆 【行业表现】")
        for fund_type, stats in overview["type_stats"].items():
            report.append(f"   {fund_type}：{stats['avg_change']:+.2f}% ({stats['count']}只)")
        report.append("")
        report.append("🚀 【涨幅前三】")
        for fund in overview["top_gainers"]:
            report.append(f"   {fund.name} ({fund.code})：{fund.change_percent:+.2f}%")
        report.append("")
        report.append("📉 【跌幅前三】")
        for fund in overview["top_losers"]:
            report.append(f"   {fund.name} ({fund.code})：{fund.change_percent:+.2f}%")
        report.append("")
        report.append("💡 " + "="*50)
        report.append("💡 【投资建议】（经验老道投资者视角）")
        report.append("💡 " + "="*50)
        report.append("")
        
        for i, suggestion in enumerate(suggestions, 1):
            report.append(f"{i}. {suggestion.fund_name} ({suggestion.fund_code})")
            report.append(f"   👉 操作：{suggestion.action}")
            report.append(f"   🎯 建议仓位：{suggestion.target_position}%")
            report.append(f"   📝 理由：{suggestion.reason}")
            report.append("")
        
        report.append("⚠️ 免责声明：以上建议仅供参考，不构成投资建议。")
        report.append("   投资有风险，入市需谨慎！")
        report.append("")
        report.append("📊 " + "="*50)
        
        return "\n".join(report)


def get_daily_fund_report() -> str:
    """获取每日基金报告"""
    analyzer = FundAnalyzer()
    return analyzer.format_report()


if __name__ == "__main__":
    print(get_daily_fund_report())
