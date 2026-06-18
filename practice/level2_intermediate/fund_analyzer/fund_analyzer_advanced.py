#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金分析系统 - 增强版（Advanced）
================================================
核心能力：
1. 技术指标分析（移动均线、MACD、RSI、波动率）
2. 多策略回测（均值回归 / 动量 / 均线穿越 / 定投）
3. 策略对比评估（收益率、胜率、最大回撤、夏普比）
4. 真实数据源 + 模拟数据双轨
5. 个性化持仓建议（基于用户成本价）
6. 可视化报告（ASCII 图表 + JSON 导出）
7. 风险等级评估与资产配置建议

本模块为 Level 2 进阶项目，重点展示：
- 时间序列分析与信号工程
- 策略模式 (Strategy Pattern) 实现多策略
- 回测框架设计（滑点、手续费、仓位管理）
- 投资组合理论（Modern Portfolio Theory）简化实现
"""

import sys
import os
import json
import math
import random
import datetime
import statistics
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Callable
from collections import defaultdict


# ============================================================
# 数据结构
# ============================================================

@dataclass
class PricePoint:
    """单日价格数据点"""
    date: str
    price: float
    change_pct: float = 0.0
    volume: float = 0.0


@dataclass
class FundProfile:
    """基金完整画像"""
    code: str
    name: str
    fund_type: str
    current_price: float
    change_pct: float
    history: List[PricePoint] = field(default_factory=list)

    # 技术指标（由分析器计算）
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    volatility_20: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0

    # 信号
    signal: str = "观望"  # 买入/卖出/观望/强买/强卖
    signal_confidence: float = 0.0

    # 指标缓存
    _history_computed: bool = False


@dataclass
class BacktestResult:
    """策略回测结果"""
    strategy_name: str
    total_return: float       # 总收益率 %
    annual_return: float      # 年化收益 %
    win_rate: float           # 胜率
    max_drawdown: float       # 最大回撤 %
    sharpe_ratio: float       # 夏普比率
    trades: int               # 交易次数
    final_value: float        # 最终资产
    benchmark_return: float   # 基准收益（买入持有）
    excess_return: float      # 超额收益
    equity_curve: List[float] = field(default_factory=list)  # 净值曲线


@dataclass
class PortfolioAdvice:
    """投资组合建议"""
    risk_level: str           # 保守 / 稳健 / 平衡 / 进取 / 激进
    suggested_allocation: Dict[str, float]  # 类别 -> 建议仓位 %
    top_picks: List[Tuple[str, str, float]]  # (代码, 名称, 建议权重)
    reason: str


# ============================================================
# 数据层
# ============================================================

class MockHistoryGenerator:
    """模拟历史数据生成器（保证离线可运行）

    基于几何布朗运动 (Geometric Brownian Motion) 生成价格序列：
        P(t+1) = P(t) * exp((mu - 0.5*sigma^2) * dt + sigma * sqrt(dt) * Z)
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate(self, code: str, name: str, fund_type: str,
                 days: int = 180, start_price: Optional[float] = None,
                 mu: Optional[float] = None, sigma: Optional[float] = None) -> FundProfile:
        """生成指定基金的历史价格序列"""

        # 按基金类型设置不同的漂移和波动
        type_params = {
            "指数型": (0.0004, 0.015),
            "混合型": (0.0003, 0.012),
            "股票型": (0.0005, 0.018),
            "债券型": (0.00015, 0.004),
            "QDII": (0.00035, 0.016),
        }
        default_mu, default_sigma = type_params.get(fund_type, (0.0003, 0.015))

        if mu is None:
            mu = default_mu + random.uniform(-0.0002, 0.0003)
        if sigma is None:
            sigma = default_sigma + random.uniform(-0.003, 0.003)

        if start_price is None:
            start_price = round(random.uniform(1.0, 4.0), 3)

        # 生成价格序列
        prices: List[float] = [start_price]
        today = datetime.date.today()

        for i in range(1, days):
            dt = 1 / 252  # 假设 252 个交易日
            z = random.gauss(0, 1)
            drift = (mu - 0.5 * sigma ** 2) * dt
            shock = sigma * math.sqrt(dt) * z
            new_price = prices[-1] * math.exp(drift + shock)
            prices.append(round(new_price, 4))

        # 构造 PricePoint 列表
        history = []
        for i, p in enumerate(prices):
            day = today - datetime.timedelta(days=days - 1 - i)
            prev_p = prices[i - 1] if i > 0 else p
            change = (p - prev_p) / prev_p * 100 if prev_p > 0 else 0.0
            history.append(PricePoint(
                date=day.strftime("%Y-%m-%d"),
                price=p,
                change_pct=round(change, 2),
                volume=round(random.uniform(5e6, 5e8), 0),
            ))

        current_price = prices[-1]
        change_pct = history[-1].change_pct if len(history) > 1 else 0.0

        return FundProfile(
            code=code,
            name=name,
            fund_type=fund_type,
            current_price=round(current_price, 4),
            change_pct=round(change_pct, 2),
            history=history,
        )


class FundDataSource:
    """数据源（模拟数据为主，真实数据为可选增强）"""

    DEFAULT_FUNDS = [
        ("161725", "招商中证白酒指数", "指数型"),
        ("005827", "易方达蓝筹精选混合", "混合型"),
        ("001938", "中欧时代先锋股票", "股票型"),
        ("320007", "诺安成长混合", "混合型"),
        ("007339", "易方达中小盘混合", "混合型"),
        ("512880", "证券ETF", "指数型"),
        ("159915", "创业板ETF", "指数型"),
        ("159919", "沪深300ETF", "指数型"),
        ("512690", "酒ETF", "指数型"),
        ("001475", "易方达国防军工混合", "股票型"),
        ("510500", "中证500ETF", "指数型"),
        ("005669", "前海开源公用事业股票", "股票型"),
    ]

    BOND_FUNDS = [
        ("000914", "中债聚利债券A", "债券型"),
        ("000187", "华泰柏瑞丰盛纯债A", "债券型"),
    ]

    def __init__(self, use_real: bool = False):
        self.use_real = use_real  # 当前版本使用模拟数据，保证可复现
        self.generator = MockHistoryGenerator(seed=2026)

    def get_fund_pool(self, codes: Optional[List[str]] = None) -> List[FundProfile]:
        """获取基金池"""
        pool = self.DEFAULT_FUNDS + self.BOND_FUNDS
        if codes:
            pool = [(c, n, t) for (c, n, t) in pool if c in codes]
            # 补齐不在预设池中的基金
            for c in codes:
                if not any(c == code for code, _, _ in pool):
                    pool.append((c, f"基金{c}", "混合型"))

        profiles = []
        for code, name, ftype in pool:
            profile = self.generator.generate(
                code=code, name=name, fund_type=ftype,
                days=180,
            )
            profiles.append(profile)
        return profiles


# ============================================================
# 技术指标计算
# ============================================================

class TechnicalAnalyzer:
    """技术指标分析器"""

    @staticmethod
    def sma(prices: List[float], window: int) -> List[float]:
        """简单移动均线 (Simple Moving Average)"""
        result = []
        for i in range(len(prices)):
            if i < window - 1:
                result.append(sum(prices[:i + 1]) / (i + 1))
            else:
                result.append(sum(prices[i - window + 1:i + 1]) / window)
        return result

    @staticmethod
    def ema(prices: List[float], window: int) -> List[float]:
        """指数移动均线 (Exponential Moving Average)"""
        if not prices:
            return []
        k = 2 / (window + 1)
        ema_values = [prices[0]]
        for p in prices[1:]:
            ema_values.append(p * k + ema_values[-1] * (1 - k))
        return ema_values

    @staticmethod
    def rsi(prices: List[float], window: int = 14) -> float:
        """相对强弱指数 (Relative Strength Index) - 返回最新值"""
        if len(prices) < window + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, min(len(prices), window + 10)):
            diff = prices[i] - prices[i - 1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-diff)
        avg_gain = statistics.mean(gains[-window:]) if gains else 0
        avg_loss = statistics.mean(losses[-window:]) if losses else 0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    @classmethod
    def macd(cls, prices: List[float]) -> Tuple[float, float]:
        """MACD 线与信号线（返回最新值）"""
        if len(prices) < 35:
            return 0.0, 0.0
        ema12 = cls.ema(prices, 12)
        ema26 = cls.ema(prices, 26)
        macd_line = [a - b for a, b in zip(ema12, ema26)]
        signal_line = cls.ema(macd_line, 9)
        return round(macd_line[-1], 4), round(signal_line[-1], 4)

    @staticmethod
    def volatility(prices: List[float], window: int = 20) -> float:
        """年化波动率"""
        if len(prices) < window + 1:
            return 0.0
        returns = []
        for i in range(1, min(len(prices), window + 1)):
            if prices[i - 1] > 0:
                returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
        if len(returns) < 2:
            return 0.0
        std = statistics.pstdev(returns)
        return round(std * math.sqrt(252) * 100, 2)  # 年化，百分比

    @staticmethod
    def max_drawdown(prices: List[float]) -> float:
        """最大回撤 (Max Drawdown) %"""
        if len(prices) < 2:
            return 0.0
        peak = prices[0]
        max_dd = 0.0
        for p in prices:
            peak = max(peak, p)
            dd = (peak - p) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
        return round(max_dd, 2)

    @staticmethod
    def sharpe(prices: List[float], risk_free: float = 0.03) -> float:
        """简化夏普比率 (Sharpe Ratio)"""
        if len(prices) < 3:
            return 0.0
        daily_returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                daily_returns.append(prices[i] / prices[i - 1] - 1)
        if not daily_returns:
            return 0.0
        mean_r = statistics.mean(daily_returns)
        std_r = statistics.pstdev(daily_returns) if len(daily_returns) > 1 else 0
        if std_r == 0:
            return 0.0
        return round((mean_r * 252 - risk_free) / (std_r * math.sqrt(252)), 2)

    @classmethod
    def analyze_profile(cls, profile: FundProfile) -> FundProfile:
        """为单个基金计算所有技术指标并生成信号"""
        if profile._history_computed:
            return profile

        prices = [p.price for p in profile.history]
        if not prices:
            return profile

        # 计算均线
        ma5_list = cls.sma(prices, 5)
        ma10_list = cls.sma(prices, 10)
        ma20_list = cls.sma(prices, 20)
        ma60_list = cls.sma(prices, 60)

        profile.ma5 = round(ma5_list[-1], 4)
        profile.ma10 = round(ma10_list[-1], 4)
        profile.ma20 = round(ma20_list[-1], 4)
        profile.ma60 = round(ma60_list[-1], 4)

        # RSI、MACD、波动率
        profile.rsi = cls.rsi(prices)
        profile.macd, profile.macd_signal = cls.macd(prices)
        profile.volatility_20 = cls.volatility(prices)
        profile.max_drawdown = cls.max_drawdown(prices)
        profile.sharpe_ratio = cls.sharpe(prices)

        # 生成综合信号
        profile.signal, profile.signal_confidence = cls._generate_signal(profile, prices, ma20_list, ma60_list)
        profile._history_computed = True
        return profile

    @classmethod
    def _generate_signal(cls, profile: FundProfile, prices: List[float],
                         ma20_list: List[float], ma60_list: List[float]) -> Tuple[str, float]:
        """基于多因子打分生成信号"""
        score = 0.0
        signals = []

        current_price = prices[-1]

        # 因子1：均线位置（价格相对于 MA20 / MA60）
        if current_price > profile.ma20 and current_price > profile.ma60:
            score += 2
            signals.append("站上双均线")
        elif current_price < profile.ma20 and current_price < profile.ma60:
            score -= 2
            signals.append("跌破双均线")
        elif current_price > profile.ma20:
            score += 0.5
            signals.append("站上短期均线")

        # 因子2：均线多空排列（MA20 > MA60 为多头排列）
        if profile.ma20 > profile.ma60:
            score += 1.5
            signals.append("均线多头排列")
        else:
            score -= 1
            signals.append("均线空头排列")

        # 因子3：RSI 超买超卖
        if profile.rsi < 30:
            score += 2
            signals.append(f"RSI超卖({profile.rsi})")
        elif profile.rsi > 70:
            score -= 1.5
            signals.append(f"RSI超买({profile.rsi})")
        elif profile.rsi < 45:
            score += 0.5
        elif profile.rsi > 60:
            score -= 0.3

        # 因子4：MACD 金叉/死叉（简化：MACD > Signal 且 MACD > 0 为强势）
        if profile.macd > profile.macd_signal and profile.macd > 0:
            score += 1.5
            signals.append("MACD金叉零上")
        elif profile.macd < profile.macd_signal and profile.macd < 0:
            score -= 1.5
            signals.append("MACD死叉零下")
        elif profile.macd > profile.macd_signal:
            score += 0.5

        # 因子5：回撤修正（跌得多 = 反弹机会）
        if profile.max_drawdown > 20:
            score += 1
            signals.append("深度回撤可能反弹")
        elif profile.max_drawdown < 5:
            score -= 0.3
            signals.append("近期位置偏高")

        # 映射到信号
        if score >= 4:
            signal = "强买"
        elif score >= 1.5:
            signal = "买入"
        elif score >= -0.5:
            signal = "观望"
        elif score >= -2.5:
            signal = "减仓"
        else:
            signal = "强卖"

        confidence = min(1.0, abs(score) / 6 + 0.3)
        return signal, round(confidence, 2)


# ============================================================
# 策略层（策略模式）
# ============================================================

class TradingStrategy:
    """交易策略基类"""
    name: str = "Base"

    def generate_signals(self, profile: FundProfile) -> List[int]:
        """对每个交易日生成信号：1=买入, -1=卖出, 0=持有"""
        return [0] * len(profile.history)


class MovingAverageCrossoverStrategy(TradingStrategy):
    """双均线穿越策略：MA5 上穿 MA20 买入，下穿卖出"""
    name = "均线穿越 (MA5 vs MA20)"

    def generate_signals(self, profile: FundProfile) -> List[int]:
        prices = [p.price for p in profile.history]
        ma5 = TechnicalAnalyzer.sma(prices, 5)
        ma20 = TechnicalAnalyzer.sma(prices, 20)
        signals = [0] * len(prices)
        for i in range(1, len(prices)):
            if ma5[i - 1] <= ma20[i - 1] and ma5[i] > ma20[i]:
                signals[i] = 1  # 金叉买入
            elif ma5[i - 1] >= ma20[i - 1] and ma5[i] < ma20[i]:
                signals[i] = -1  # 死叉卖出
        return signals


class RSIMeanReversionStrategy(TradingStrategy):
    """均值回归策略：RSI 超卖(<30)买入，超买(>70)卖出"""
    name = "均值回归 (RSI 30/70)"

    def generate_signals(self, profile: FundProfile) -> List[int]:
        prices = [p.price for p in profile.history]
        signals = [0] * len(prices)
        for i in range(14, len(prices)):
            window = prices[max(0, i - 14):i + 1]
            rsi_val = TechnicalAnalyzer.rsi(window)
            if rsi_val < 30:
                signals[i] = 1
            elif rsi_val > 70:
                signals[i] = -1
        return signals


class MomentumStrategy(TradingStrategy):
    """动量策略：过去20日涨幅为正则买入（追涨）"""
    name = "动量策略 (20日动量)"

    def generate_signals(self, profile: FundProfile) -> List[int]:
        prices = [p.price for p in profile.history]
        signals = [0] * len(prices)
        window = 20
        for i in range(window, len(prices)):
            momentum = (prices[i] - prices[i - window]) / prices[i - window]
            if momentum > 0.03:  # 3% 以上触发买入
                signals[i] = 1
            elif momentum < -0.05:  # -5% 止损
                signals[i] = -1
        return signals


class DollarCostAveragingStrategy(TradingStrategy):
    """定投策略：每20天固定买入一次"""
    name = "定投策略 (每20天)"

    def generate_signals(self, profile: FundProfile) -> List[int]:
        signals = [0] * len(profile.history)
        for i in range(30, len(signals), 20):
            signals[i] = 1
        return signals


# ============================================================
# 回测引擎
# ============================================================

class BacktestEngine:
    """简化回测引擎"""

    INITIAL_CAPITAL = 10000.0
    SLIPPAGE = 0.001     # 0.1% 滑点
    FEE = 0.0005         # 0.05% 手续费

    def run(self, profile: FundProfile, strategy: TradingStrategy) -> BacktestResult:
        """运行单策略回测"""
        signals = strategy.generate_signals(profile)
        prices = [p.price for p in profile.history]
        n = len(prices)

        cash = self.INITIAL_CAPITAL
        shares = 0.0
        equity_curve = []
        trade_count = 0
        winning_trades = 0
        entry_price = 0.0
        peak = self.INITIAL_CAPITAL
        max_dd = 0.0

        for i in range(n):
            # 执行信号
            if signals[i] == 1 and cash > 0:
                usable_cash = cash * 0.9  # 每次用90%仓位
                effective_price = prices[i] * (1 + self.SLIPPAGE)
                fee = usable_cash * self.FEE
                buy_shares = (usable_cash - fee) / effective_price
                shares += buy_shares
                cash -= usable_cash
                entry_price = prices[i]
                trade_count += 1
            elif signals[i] == -1 and shares > 0:
                effective_price = prices[i] * (1 - self.SLIPPAGE)
                proceeds = shares * effective_price
                fee = proceeds * self.FEE
                cash += proceeds - fee
                # 统计盈亏
                if prices[i] > entry_price and entry_price > 0:
                    winning_trades += 1
                shares = 0
                trade_count += 1

            # 记录净值
            total_value = cash + shares * prices[i]
            equity_curve.append(round(total_value, 2))
            peak = max(peak, total_value)
            max_dd = max(max_dd, (peak - total_value) / peak)

        # 强制平仓以计算最终收益
        final_price = prices[-1]
        if shares > 0:
            cash += shares * final_price * (1 - self.SLIPPAGE)
            shares = 0

        total_return = (cash - self.INITIAL_CAPITAL) / self.INITIAL_CAPITAL * 100
        days = max(n / 252, 1 / 252)
        annual_return = (cash / self.INITIAL_CAPITAL) ** (1 / days) - 1
        annual_return *= 100

        win_rate = winning_trades / trade_count * 100 if trade_count > 0 else 0.0

        # 基准（买入持有）
        benchmark_shares = self.INITIAL_CAPITAL * 0.9 / prices[0]
        benchmark_final = benchmark_shares * prices[-1] + self.INITIAL_CAPITAL * 0.1
        benchmark_return = (benchmark_final - self.INITIAL_CAPITAL) / self.INITIAL_CAPITAL * 100

        # 计算每日收益的夏普
        if len(equity_curve) > 10:
            daily_returns = []
            for i in range(1, len(equity_curve)):
                if equity_curve[i - 1] > 0:
                    daily_returns.append(equity_curve[i] / equity_curve[i - 1] - 1)
            if daily_returns and statistics.pstdev(daily_returns) > 0:
                sharpe = (statistics.mean(daily_returns) * 252 - 0.03) / (statistics.pstdev(daily_returns) * math.sqrt(252))
            else:
                sharpe = 0
        else:
            sharpe = 0

        return BacktestResult(
            strategy_name=strategy.name,
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            win_rate=round(win_rate, 1),
            max_drawdown=round(max_dd * 100, 2),
            sharpe_ratio=round(sharpe, 2),
            trades=trade_count,
            final_value=round(cash, 2),
            benchmark_return=round(benchmark_return, 2),
            excess_return=round(total_return - benchmark_return, 2),
            equity_curve=equity_curve[::7],  # 每周保留一个点，减少数据量
        )

    def run_all(self, profile: FundProfile) -> List[BacktestResult]:
        """运行所有预设策略"""
        strategies = [
            MovingAverageCrossoverStrategy(),
            RSIMeanReversionStrategy(),
            MomentumStrategy(),
            DollarCostAveragingStrategy(),
        ]
        return [self.run(profile, s) for s in strategies]


# ============================================================
# ASCII 图表工具
# ============================================================

class AsciiChart:
    """极简 ASCII 图表生成器"""

    @staticmethod
    def sparkline(values: List[float], width: int = 50) -> str:
        """生成横向简易曲线（用字符表示高度）"""
        if not values:
            return "(无数据)"
        blocks = " ▁▂▃▄▅▆▇█"
        mn, mx = min(values), max(values)
        if mx == mn:
            return "─" * width
        step = (mx - mn) / 8
        # 按宽度采样
        if len(values) > width:
            sampled = [values[i * len(values) // width] for i in range(width)]
        else:
            sampled = values
        return "".join(blocks[min(8, max(1, int((v - mn) / step) + 1))] for v in sampled)

    @staticmethod
    def bar(label: str, value: float, max_value: float, width: int = 30) -> str:
        """生成横向柱状条"""
        if max_value == 0:
            filled = 0
        else:
            filled = int(abs(value) / max_value * width)
        bar_chars = "█" * filled
        sign = "+" if value > 0 else ""
        return f"{label:<20} |{bar_chars:<{width}}| {sign}{value:.2f}%"


# ============================================================
# 主分析器
# ============================================================

class AdvancedFundAnalyzer:
    """基金分析主控制器"""

    def __init__(self, codes: Optional[List[str]] = None, user_holdings: Optional[Dict] = None):
        self.data_source = FundDataSource(use_real=False)
        self.profiles: List[FundProfile] = []
        self.user_holdings = user_holdings or {}
        self.codes = codes
        self.backtest_results: Dict[str, List[BacktestResult]] = {}

    def load_and_analyze(self):
        """加载数据并执行分析"""
        print("[数据层] 加载基金池数据（含180天历史）...")
        self.profiles = self.data_source.get_fund_pool(self.codes)
        print(f"[数据层] 已加载 {len(self.profiles)} 只基金")

        print("[分析层] 计算技术指标并生成信号...")
        for p in self.profiles:
            TechnicalAnalyzer.analyze_profile(p)

        print("[回测层] 运行多策略回测（每只基金 4 个策略）...")
        engine = BacktestEngine()
        for p in self.profiles:
            results = engine.run_all(p)
            self.backtest_results[p.code] = results
        print(f"[回测层] 完成 {len(self.profiles)} 只基金 × 4 策略 = {len(self.profiles)*4} 组回测")

    # ---------- 输出 1：技术指标摘要表 ----------
    def format_tech_table(self) -> str:
        lines = [""]
        lines.append("📊 " + "=" * 80)
        lines.append("📊 【技术指标摘要】")
        lines.append("📊 " + "=" * 80)
        lines.append(
            f"{'代码':<8}{'名称':<18}{'类型':<8}{'现价':>8}{'涨跌%':>8}"
            f"{'MA20':>8}{'MA60':>8}{'RSI':>7}{'波动%':>7}{'回撤%':>7}{'夏普':>6}{'信号':<6}"
        )
        lines.append("─" * 80)
        for p in self.profiles:
            lines.append(
                f"{p.code:<8}{p.name[:16]:<18}{p.fund_type:<8}{p.current_price:>8.4f}"
                f"{p.change_pct:>+7.2f}  {p.ma20:>7.3f} {p.ma60:>7.3f}"
                f"{p.rsi:>7.1f}{p.volatility_20:>7.1f}{p.max_drawdown:>7.1f}"
                f"{p.sharpe_ratio:>6.2f}  {p.signal:<6}"
            )
        return "\n".join(lines)

    # ---------- 输出 2：策略对比（单只基金） ----------
    def format_strategy_comparison(self, fund_code: str) -> str:
        results = self.backtest_results.get(fund_code, [])
        if not results:
            return ""
        profile = next((p for p in self.profiles if p.code == fund_code), None)

        lines = [""]
        lines.append("🔬 " + "=" * 80)
        lines.append(f"🔬 【策略对比 - {profile.name if profile else fund_code} ({fund_code})】")
        lines.append("🔬 " + "=" * 80)
        lines.append(f"{'策略':<25}{'总收益%':>10}{'年化%':>10}{'胜率%':>8}"
                     f"{'最大回撤%':>12}{'夏普':>8}{'交易次':>7}{'超额%':>8}")
        lines.append("─" * 80)

        # 确定图表 y 轴最大值
        max_return = max(abs(r.total_return) for r in results) if results else 1

        for r in results:
            lines.append(
                f"{r.strategy_name:<25}{r.total_return:>+10.2f}{r.annual_return:>+10.2f}"
                f"{r.win_rate:>8.1f}{r.max_drawdown:>12.2f}{r.sharpe_ratio:>8.2f}"
                f"{r.trades:>7}{r.excess_return:>+8.2f}"
            )
            lines.append("    " + AsciiChart.sparkline(r.equity_curve, width=60))
        lines.append("")
        lines.append(f"📌 基准（买入持有）收益：{results[0].benchmark_return:+.2f}%")
        return "\n".join(lines)

    # ---------- 输出 3：推荐基金（综合评分排序） ----------
    def format_top_picks(self, top_n: int = 5) -> str:
        ranked = sorted(self.profiles, key=lambda p: -self._composite_score(p))
        lines = [""]
        lines.append("⭐ " + "=" * 80)
        lines.append(f"⭐ 【综合推荐 TOP{top_n}】（均线 + RSI + MACD + 夏普 多因子加权）")
        lines.append("⭐ " + "=" * 80)

        max_score = max(self._composite_score(p) for p in ranked) if ranked else 1.0

        for i, p in enumerate(ranked[:top_n], 1):
            score = self._composite_score(p)
            confidence = "高" if score > 4 else ("中" if score > 2 else "低")
            lines.append(f"\n{i}. {p.name} ({p.code}) - [{p.fund_type}]")
            lines.append(f"   信号: {p.signal}  置信度: {p.signal_confidence:.0%}  综合评分: {score:.2f}")
            lines.append(
                f"   现价: {p.current_price:.4f} | MA20: {p.ma20:.3f} | MA60: {p.ma60:.3f}"
                f" | RSI: {p.rsi:.1f} | 夏普: {p.sharpe_ratio:.2f}"
            )
            # 显示最佳策略
            best = max(self.backtest_results.get(p.code, []), key=lambda r: r.total_return)
            lines.append(f"   历史最佳策略: {best.strategy_name} -> 收益 {best.total_return:+.2f}%")

        return "\n".join(lines)

    @staticmethod
    def _composite_score(p: FundProfile) -> float:
        """综合评分（简化版多因子）"""
        score = 0.0
        if p.ma20 > p.ma60:
            score += 1.5
        if p.current_price > p.ma20:
            score += 1.0
        if 30 < p.rsi < 60:
            score += 1.0
        elif p.rsi < 30:
            score += 1.5
        if p.macd > p.macd_signal:
            score += 1.0
        score += max(p.sharpe_ratio, 0) * 0.3
        return score

    # ---------- 输出 4：用户持仓诊断 ----------
    def format_holding_diagnosis(self) -> str:
        if not self.user_holdings:
            return "\n💡 提示：在 fund_config.py MY_HOLDINGS 中填写您的持仓，可获得个性化诊断\n"

        lines = [""]
        lines.append("🧾 " + "=" * 80)
        lines.append("🧾 【用户持仓诊断】")
        lines.append("🧾 " + "=" * 80)

        total_position = sum(h.get("position", 0) for h in self.user_holdings.values())

        for code, info in self.user_holdings.items():
            profile = next((p for p in self.profiles if p.code == code), None)
            if not profile:
                continue
            cost = info.get("cost", 0)
            pos = info.get("position", 0)
            current = profile.current_price
            profit_pct = (current - cost) / cost * 100 if cost > 0 else 0

            # 结合信号给出建议
            advice_map = {
                "强买": f"📈 当前信号为【{profile.signal}】，可考虑加仓",
                "买入": f"🟢 当前信号为【{profile.signal}】，可持有或逢低加仓",
                "观望": f"🟡 当前信号为【{profile.signal}】，建议持有观察",
                "减仓": f"🟠 当前信号为【{profile.signal}】，可考虑分批减仓",
                "强卖": f"🔴 当前信号为【{profile.signal}】，建议减仓或离场",
            }

            lines.append(f"\n• {info.get('name', profile.name)} ({code})")
            lines.append(f"   成本价: {cost:.4f}  现价: {current:.4f}  浮动盈亏: {profit_pct:+.2f}%")
            lines.append(f"   仓位: {pos:.1f}%  波动率(年化): {profile.volatility_20:.1f}%  最大回撤: {profile.max_drawdown:.1f}%")
            lines.append(f"   {advice_map.get(profile.signal, '')}")

        lines.append(f"\n📌 总持仓仓位: {total_position:.1f}%")
        if total_position > 90:
            lines.append("⚠️  仓位较高，建议保留部分现金应对波动")
        elif total_position < 30:
            lines.append("💡 仓位较轻，可择机分批建仓")
        else:
            lines.append("✅ 仓位处于合理区间")
        return "\n".join(lines)

    # ---------- 输出 5：资产配置建议 ----------
    def format_portfolio_advice(self, risk_level: str = "平衡") -> str:
        """基于目标风险水平的简化资产配置"""
        templates = {
            "保守": {"债券型": 60, "指数型": 20, "混合型": 20, "股票型": 0},
            "稳健": {"债券型": 40, "指数型": 30, "混合型": 25, "股票型": 5},
            "平衡": {"债券型": 25, "指数型": 35, "混合型": 25, "股票型": 15},
            "进取": {"债券型": 10, "指数型": 35, "混合型": 30, "股票型": 25},
            "激进": {"债券型": 0, "指数型": 30, "混合型": 30, "股票型": 40},
        }
        allocation = templates.get(risk_level, templates["平衡"])

        # 从各类型中挑选一只最佳基金
        top_picks = []
        for ftype in allocation:
            candidates = [p for p in self.profiles if p.fund_type == ftype]
            if candidates:
                best = max(candidates, key=self._composite_score)
                top_picks.append((best.code, best.name, allocation[ftype]))

        lines = [""]
        lines.append("🎯 " + "=" * 80)
        lines.append(f"🎯 【资产配置建议 - 风险等级：{risk_level}】")
        lines.append("🎯 " + "=" * 80)
        lines.append("\n建议配置比例：")

        max_alloc = max(allocation.values())
        for ftype, pct in sorted(allocation.items(), key=lambda x: -x[1]):
            lines.append("   " + AsciiChart.bar(ftype, pct, max_alloc, width=30))

        lines.append("\n建议基金组合：")
        for code, name, weight in top_picks:
            profile = next((p for p in self.profiles if p.code == code), None)
            signal = profile.signal if profile else "-"
            lines.append(f"   • {name} ({code})  配置 {weight:.0f}%  [当前信号: {signal}]")

        lines.append("\n⚠️  以上建议基于历史数据模拟，不构成任何投资决策依据")
        return "\n".join(lines)

    # ---------- 输出 6：JSON 导出 ----------
    def export_json(self, filepath: str) -> str:
        export_data = {
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "funds": [],
            "strategy_summary": [],
        }
        for p in self.profiles:
            fund_data = {
                "code": p.code,
                "name": p.name,
                "type": p.fund_type,
                "price": p.current_price,
                "change_pct": p.change_pct,
                "ma5": p.ma5, "ma20": p.ma20, "ma60": p.ma60,
                "rsi": p.rsi, "macd": p.macd, "macd_signal": p.macd_signal,
                "volatility": p.volatility_20, "max_drawdown": p.max_drawdown,
                "sharpe": p.sharpe_ratio, "signal": p.signal,
            }
            export_data["funds"].append(fund_data)
            results = self.backtest_results.get(p.code, [])
            for r in results:
                export_data["strategy_summary"].append({
                    "fund_code": p.code,
                    "strategy": r.strategy_name,
                    "total_return": r.total_return,
                    "win_rate": r.win_rate,
                    "max_drawdown": r.max_drawdown,
                    "sharpe": r.sharpe_ratio,
                })

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        return filepath


# ============================================================
# 主入口
# ============================================================

def run_full_analysis(codes: Optional[List[str]] = None,
                      user_holdings: Optional[Dict] = None,
                      risk_level: str = "平衡",
                      top_n: int = 5) -> str:
    """完整运行增强版基金分析"""
    print("=" * 80)
    print("🤖 基金分析系统 - 增强版 (包含技术指标 / 回测 / 资产配置)")
    print("=" * 80)

    analyzer = AdvancedFundAnalyzer(codes=codes, user_holdings=user_holdings)
    analyzer.load_and_analyze()

    report_parts = []

    # 1. 技术指标摘要
    report_parts.append(analyzer.format_tech_table())

    # 2. 对第一只基金展示完整策略对比
    if analyzer.profiles:
        report_parts.append(analyzer.format_strategy_comparison(analyzer.profiles[0].code))

    # 3. 推荐基金
    report_parts.append(analyzer.format_top_picks(top_n=top_n))

    # 4. 持仓诊断
    report_parts.append(analyzer.format_holding_diagnosis())

    # 5. 资产配置建议
    report_parts.append(analyzer.format_portfolio_advice(risk_level=risk_level))

    # 6. 导出 JSON
    output_path = Path(__file__).parent / "outputs" / "fund_advanced_report.json"
    exported = analyzer.export_json(str(output_path))
    print(f"\n📁 详细数据已导出至: {exported}")

    final_report = "\n".join(report_parts)
    print(final_report)
    return final_report


if __name__ == "__main__":
    # 尝试加载用户配置
    try:
        from fund_config import MY_FUND_LIST, MY_HOLDINGS, USE_REAL_DATA
    except ImportError:
        MY_FUND_LIST = None
        MY_HOLDINGS = {}
        USE_REAL_DATA = False

    run_full_analysis(
        codes=MY_FUND_LIST,
        user_holdings=MY_HOLDINGS,
        risk_level="平衡",
        top_n=5,
    )
