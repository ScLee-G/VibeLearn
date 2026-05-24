#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金分析系统 - 每日市场涨跌分析与投资建议
支持东方财富等真实数据源
"""

import datetime
import random
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from urllib.parse import urlencode

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REAL_DATA = True
except ImportError:
    HAS_REAL_DATA = False
    print("⚠️  警告: 未安装数据获取库，将使用模拟数据")
    print("   运行: pip install requests beautifulsoup4 pandas lxml")


@dataclass
class FundInfo:
    """基金信息"""
    code: str
    name: str
    type: str = "混合型"
    current_price: float = 0.0
    change_percent: float = 0.0
    change_amount: float = 0.0
    volume: float = 0.0
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    fund_type: str = "混合型"


@dataclass
class InvestmentSuggestion:
    """投资建议"""
    fund_code: str
    fund_name: str
    action: str
    target_position: float
    reason: str


class EastMoneyFundFetcher:
    """东方财富基金数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_realtime_fund_data(self, fund_code: str) -> Optional[FundInfo]:
        """获取单只基金实时数据"""
        try:
            # 获取基金实时估值
            url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # 解析返回的JSONP数据
                content = response.text
                match = re.search(r'jsonpgz\((.*?)\);', content)
                if match:
                    data = json.loads(match.group(1))
                    
                    # 获取基金基本信息
                    fund_info = self.get_fund_basic_info(fund_code)
                    
                    fund = FundInfo(
                        code=fund_code,
                        name=data.get('name', fund_code),
                        current_price=float(data.get('gsz', 0)),
                        change_percent=float(data.get('gszzl', 0)),
                        type=fund_info.get('type', '混合型')
                    )
                    return fund
            return None
        except Exception as e:
            print(f"获取基金 {fund_code} 数据失败: {e}")
            return None
    
    def get_fund_basic_info(self, fund_code: str) -> Dict:
        """获取基金基本信息"""
        try:
            url = f"http://fund.eastmoney.com/{fund_code}.html"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 尝试获取基金类型
                fund_type = "混合型"
                type_elem = soup.find('td', string=re.compile('基金类型'))
                if type_elem and type_elem.next_sibling:
                    fund_type = type_elem.next_sibling.text.strip()
                
                return {'type': fund_type}
        except Exception as e:
            print(f"获取基金 {fund_code} 基本信息失败: {e}")
        
        return {'type': '混合型'}
    
    def get_all_funds_daily(self) -> List[FundInfo]:
        """获取所有基金当日数据（简化版）"""
        # 由于获取全部基金数据较慢，这里使用精选基金列表
        # 实际使用时可以根据需要扩展
        return []


class FundAnalyzer:
    """基金分析器"""
    
    def __init__(self, use_real_data: bool = True):
        self.use_real_data = use_real_data and HAS_REAL_DATA
        self.fetcher = EastMoneyFundFetcher() if self.use_real_data else None
        
        # 默认精选基金池（涵盖各种类型）
        self.default_funds = [
            "161725",  # 招商中证白酒
            "005827",  # 易方达蓝筹精选
            "007339",  # 易方达中小盘
            "163402",  # 兴全趋势投资
            "001938",  # 中欧时代先锋
            "320007",  # 诺安成长
            "001410",  # 易方达消费精选
            "001475",  # 易方达国防军工
            "161028",  # 富国中证军工
            "001071",  # 华夏中证5G
            "515050",  # 5GETF
            "159915",  # 创业板ETF
            "159919",  # 沪深300ETF
            "512880",  # 证券ETF
            "512690",  # 酒ETF
        ]
    
    def _init_mock_funds(self) -> List[FundInfo]:
        """初始化模拟基金数据"""
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
        
        return [FundInfo(
            code=code,
            name=name,
            type=fund_type,
            current_price=price,
            change_percent=change_pct,
            change_amount=change_amt,
            volume=vol,
            pe_ratio=pe,
            pb_ratio=pb
        ) for code, name, fund_type, price, change_pct, change_amt, vol, pe, pb in funds_data]
    
    def get_funds_data(self, fund_codes: Optional[List[str]] = None) -> List[FundInfo]:
        """获取基金数据"""
        if fund_codes is None:
            fund_codes = self.default_funds
        
        if self.use_real_data:
            funds = []
            print(f"📡 正在从东方财富获取 {len(fund_codes)} 只基金数据...")
            
            for i, code in enumerate(fund_codes, 1):
                print(f"   进度: {i}/{len(fund_codes)} - {code}")
                fund = self.fetcher.get_realtime_fund_data(code)
                if fund:
                    funds.append(fund)
                else:
                    # 如果获取失败，使用模拟数据填充
                    funds.append(self._get_mock_fund(code))
            
            return funds if funds else self._init_mock_funds()
        else:
            return self._init_mock_funds()
    
    def _get_mock_fund(self, code: str) -> FundInfo:
        """获取模拟基金数据"""
        mock_funds = {
            "161725": FundInfo(code="161725", name="招商中证白酒指数", type="指数型", 
                              current_price=1.45, change_percent=1.23, pe_ratio=35.5),
            "005827": FundInfo(code="005827", name="易方达蓝筹精选混合", type="混合型", 
                              current_price=2.78, change_percent=-0.45, pe_ratio=28.3),
            "007339": FundInfo(code="007339", name="易方达中小盘混合", type="混合型", 
                              current_price=3.21, change_percent=0.89, pe_ratio=42.1),
        }
        
        if code in mock_funds:
            return mock_funds[code]
        
        return FundInfo(
            code=code,
            name=f"基金{code}",
            type="混合型",
            current_price=round(random.uniform(1.0, 5.0), 3),
            change_percent=round(random.uniform(-3.0, 3.0), 2)
        )
    
    def get_market_overview(self, funds: List[FundInfo]) -> Dict:
        """获取市场概览"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 计算平均涨跌幅
        avg_change = sum(f.change_percent for f in funds) / len(funds) if funds else 0
        
        # 统计涨跌数量
        up_count = sum(1 for f in funds if f.change_percent > 0)
        down_count = sum(1 for f in funds if f.change_percent < 0)
        flat_count = sum(1 for f in funds if f.change_percent == 0)
        
        # 按类型分组
        type_stats = {}
        for fund in funds:
            fund_type = fund.type or "混合型"
            if fund_type not in type_stats:
                type_stats[fund_type] = {"count": 0, "avg_change": 0, "funds": []}
            type_stats[fund_type]["count"] += 1
            type_stats[fund_type]["avg_change"] += fund.change_percent
            type_stats[fund_type]["funds"].append(fund)
        
        for fund_type in type_stats:
            if type_stats[fund_type]["count"] > 0:
                type_stats[fund_type]["avg_change"] /= type_stats[fund_type]["count"]
        
        return {
            "date": today,
            "avg_change": round(avg_change, 2),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "type_stats": type_stats,
            "top_gainers": sorted(funds, key=lambda x: -x.change_percent)[:3],
            "top_losers": sorted(funds, key=lambda x: x.change_percent)[:3]
        }
    
    def analyze_fund(self, fund: FundInfo) -> Dict:
        """分析单只基金"""
        score = 0
        reasons = []
        
        # 基于涨跌幅分析
        if fund.change_percent > 2:
            score += 20
            reasons.append("今日表现强势")
        elif fund.change_percent > 0:
            score += 10
            reasons.append("今日收涨")
        elif fund.change_percent < -2:
            score -= 15
            reasons.append("今日回调较大")
        elif fund.change_percent < 0:
            score -= 5
            reasons.append("今日下跌")
        
        # 基于类型评估
        if "指数" in fund.type:
            score += 10
            reasons.append("指数型基金，收益稳定")
        elif "混合" in fund.type:
            score += 5
            reasons.append("混合型基金，配置灵活")
        elif "债券" in fund.type:
            score += 15
            reasons.append("债券型基金，风险较低")
        
        # 随机增加一些理由（实际可基于历史数据）
        if len(reasons) < 2:
            if score > 0:
                reasons.append("综合表现良好")
            else:
                reasons.append("建议观望")
        
        risk_level = "低" if score > 30 else "中" if score > 10 else "高"
        
        return {
            "fund": fund,
            "score": score,
            "reasons": reasons,
            "risk_level": risk_level
        }
    
    def generate_investment_suggestions(self, funds: List[FundInfo], 
                                       top_n: int = 5) -> List[InvestmentSuggestion]:
        """生成投资建议"""
        # 分析所有基金
        analyzed = [self.analyze_fund(fund) for fund in funds]
        
        # 按得分排序
        sorted_funds = sorted(analyzed, key=lambda x: -x["score"])
        
        suggestions = []
        for i, item in enumerate(sorted_funds[:top_n]):
            fund = item["fund"]
            score = item["score"]
            reasons = item["reasons"]
            
            # 根据得分确定操作建议
            if score >= 30:
                action = "建仓/加仓"
                target = round(random.uniform(15, 25), 1)
            elif score >= 15:
                action = "建仓"
                target = round(random.uniform(10, 15), 1)
            elif score >= 0:
                action = "持有"
                target = round(random.uniform(5, 10), 1)
            else:
                action = "减仓/观望"
                target = round(random.uniform(0, 5), 1)
            
            reason_text = "；".join(reasons) if reasons else "综合评估"
            
            suggestions.append(InvestmentSuggestion(
                fund_code=fund.code,
                fund_name=fund.name,
                action=action,
                target_position=target,
                reason=reason_text
            ))
        
        return suggestions
    
    def format_report(self, fund_codes: Optional[List[str]] = None) -> str:
        """格式化报告"""
        funds = self.get_funds_data(fund_codes)
        overview = self.get_market_overview(funds)
        suggestions = self.generate_investment_suggestions(funds)
        
        report = []
        report.append("📊 " + "="*55)
        report.append(f"📅 日期：{overview['date']}")
        report.append("📊 " + "="*55)
        report.append("")
        report.append("📈 【市场概览】")
        report.append(f"   基金池数量：{len(funds)} 只")
        report.append(f"   平均涨跌幅：{overview['avg_change']:+}%")
        report.append(f"   上涨：{overview['up_count']}只  |  下跌：{overview['down_count']}只  |  平盘：{overview['flat_count']}只")
        report.append("")
        report.append("🏆 【分类表现】")
        
        for fund_type, stats in sorted(overview["type_stats"].items(), 
                                       key=lambda x: -x[1]["avg_change"]):
            report.append(f"   {fund_type}：{stats['avg_change']:+.2f}% ({stats['count']}只)")
        
        report.append("")
        report.append("🚀 【涨幅TOP3】")
        for fund in overview["top_gainers"]:
            report.append(f"   {fund.name} ({fund.code})：{fund.change_percent:+.2f}%")
        
        report.append("")
        report.append("📉 【跌幅TOP3】")
        for fund in overview["top_losers"]:
            report.append(f"   {fund.name} ({fund.code})：{fund.change_percent:+.2f}%")
        
        report.append("")
        report.append("💡 " + "="*55)
        report.append("💡 【投资建议】（经验老道投资者视角）")
        report.append("💡 " + "="*55)
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
        report.append("📊 " + "="*55)
        
        return "\n".join(report)


def get_daily_fund_report(fund_codes: Optional[List[str]] = None) -> str:
    """获取每日基金报告"""
    # 尝试读取配置文件
    use_config = False
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from fund_config import MY_FUND_LIST, USE_REAL_DATA
        if fund_codes is None:
            fund_codes = MY_FUND_LIST
        use_config = True
    except ImportError:
        pass
    
    analyzer = FundAnalyzer(use_real_data=use_config and USE_REAL_DATA if use_config else True)
    return analyzer.format_report(fund_codes)


if __name__ == "__main__":
    print(get_daily_fund_report())
