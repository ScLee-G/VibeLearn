"""
基金分析系统增强版 - 使用示例
================================================
展示：技术指标、策略回测、持仓诊断、资产配置
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fund_analyzer_advanced import (
    TechnicalAnalyzer,
    BacktestEngine,
    MockHistoryGenerator,
    MovingAverageCrossoverStrategy,
    RSIMeanReversionStrategy,
    MomentumStrategy,
    DollarCostAveragingStrategy,
    AdvancedFundAnalyzer,
    AsciiChart,
)


def example_1_technical_indicators():
    """示例 1：单只基金的完整技术指标分析"""
    print("=" * 70)
    print("【示例 1】技术指标 - 招商中证白酒 (161725)")
    print("=" * 70)

    gen = MockHistoryGenerator(seed=100)
    profile = gen.generate("161725", "招商中证白酒指数", "指数型", days=180)
    TechnicalAnalyzer.analyze_profile(profile)

    print(f"基金代码: {profile.code} | 名称: {profile.name} | 类型: {profile.fund_type}")
    print(f"当前净值: {profile.current_price:.4f} | 日涨跌: {profile.change_pct:+.2f}%")
    print("-" * 70)
    print(f"  MA5   = {profile.ma5:.4f}")
    print(f"  MA10  = {profile.ma10:.4f}")
    print(f"  MA20  = {profile.ma20:.4f}")
    print(f"  MA60  = {profile.ma60:.4f}")
    print(f"  RSI(14)        = {profile.rsi:.2f}")
    print(f"  MACD           = {profile.macd:.4f}")
    print(f"  MACD Signal    = {profile.macd_signal:.4f}")
    print(f"  20日年化波动率 = {profile.volatility_20:.2f}%")
    print(f"  最大回撤       = {profile.max_drawdown:.2f}%")
    print(f"  夏普比率       = {profile.sharpe_ratio:.2f}")
    print(f"  综合信号       = {profile.signal} (置信度 {profile.signal_confidence:.0%})")
    print()

    # 价格走势 sparkline
    prices = [p.price for p in profile.history]
    print("  180日价格走势:")
    print("  " + AsciiChart.sparkline(prices, width=68))
    print(f"  起点: {prices[0]:.4f} → 终点: {prices[-1]:.4f}")
    return profile


def example_2_multi_strategy_backtest():
    """示例 2：对一只基金执行 4 个策略的回测对比"""
    print("\n" + "=" * 70)
    print("【示例 2】多策略回测对比")
    print("=" * 70)

    gen = MockHistoryGenerator(seed=2026)
    profile = gen.generate("005827", "易方达蓝筹精选混合", "混合型", days=180)
    TechnicalAnalyzer.analyze_profile(profile)

    strategies = [
        MovingAverageCrossoverStrategy(),
        RSIMeanReversionStrategy(),
        MomentumStrategy(),
        DollarCostAveragingStrategy(),
    ]
    engine = BacktestEngine()

    print(f"回测基金: {profile.name} ({profile.code})")
    print(f"回测周期: 180个交易日 | 初始资金: {BacktestEngine.INITIAL_CAPITAL} 元")
    print(f"滑点: {BacktestEngine.SLIPPAGE*100:.1f}% | 手续费: {BacktestEngine.FEE*100:.2f}%")
    print("-" * 70)

    results = []
    for s in strategies:
        result = engine.run(profile, s)
        results.append(result)
        print(f"\n  【{result.strategy_name}】")
        print(f"    最终资产: {result.final_value:,.2f} 元  | 总收益: {result.total_return:+.2f}%")
        print(f"    年化收益: {result.annual_return:+.2f}%  | 胜率: {result.win_rate:.1f}%")
        print(f"    最大回撤: {result.max_drawdown:.2f}%  | 夏普比: {result.sharpe_ratio:.2f}")
        print(f"    交易次数: {result.trades}  | 超额收益(vs. 持有): {result.excess_return:+.2f}%")
        print(f"    净值曲线: {AsciiChart.sparkline(result.equity_curve, width=60)}")

    # 最佳策略
    best = max(results, key=lambda r: r.total_return)
    print(f"\n  🏆 最佳策略: {best.strategy_name} 总收益 {best.total_return:+.2f}%")
    return results


def example_3_custom_backtest():
    """示例 3：自定义参数的策略回测（动量策略不同窗口期）"""
    print("\n" + "=" * 70)
    print("【示例 3】动量策略窗口期敏感性分析")
    print("=" * 70)

    gen = MockHistoryGenerator(seed=42)
    profile = gen.generate("159915", "创业板ETF", "指数型", days=250)

    class VariableMomentum(MomentumStrategy):
        def __init__(self, window: int, threshold: float):
            self.window = window
            self.threshold = threshold
            self.name = f"动量 (窗口{window}天 / 阈值{threshold*100:.0f}%)"

        def generate_signals(self, profile):
            prices = [p.price for p in profile.history]
            signals = [0] * len(prices)
            for i in range(self.window, len(prices)):
                momentum = (prices[i] - prices[i - self.window]) / prices[i - self.window]
                if momentum > self.threshold:
                    signals[i] = 1
                elif momentum < -self.threshold * 1.5:
                    signals[i] = -1
            return signals

    engine = BacktestEngine()
    configs = [(5, 0.015), (10, 0.025), (20, 0.03), (30, 0.05), (60, 0.08)]

    print(f"基金: {profile.name}  周期: 250天\n")
    print(f"{'配置':<30}{'总收益%':>10}{'年化%':>10}{'回撤%':>10}{'夏普':>8}")
    print("-" * 70)

    for window, threshold in configs:
        strategy = VariableMomentum(window, threshold)
        r = engine.run(profile, strategy)
        print(f"{strategy.name:<30}{r.total_return:>+10.2f}{r.annual_return:>+10.2f}"
              f"{r.max_drawdown:>10.2f}{r.sharpe_ratio:>8.2f}")

    return profile


def example_4_full_system():
    """示例 4：调用完整分析系统（模拟真实使用场景）"""
    print("\n" + "=" * 70)
    print("【示例 4】完整分析系统 (含持仓诊断 + 资产配置)")
    print("=" * 70)

    # 模拟用户持仓
    sample_holdings = {
        "161725": {"name": "招商中证白酒", "position": 15.0, "cost": 1.25},
        "005827": {"name": "易方达蓝筹精选", "position": 20.0, "cost": 2.80},
        "159919": {"name": "沪深300ETF", "position": 10.0, "cost": 3.10},
    }

    analyzer = AdvancedFundAnalyzer(user_holdings=sample_holdings)
    analyzer.load_and_analyze()

    print("\n" + analyzer.format_top_picks(top_n=3))
    print("\n" + analyzer.format_holding_diagnosis())
    print("\n" + analyzer.format_portfolio_advice(risk_level="平衡"))

    # JSON 导出
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "example4_export.json")
    filepath = analyzer.export_json(output_file)
    print(f"\n📁 JSON 数据文件已导出至: {filepath}")

    return analyzer


def example_5_risk_level_comparison():
    """示例 5：不同风险偏好下的资产配置对比"""
    print("\n" + "=" * 70)
    print("【示例 5】不同风险偏好的资产配置对比")
    print("=" * 70)

    analyzer = AdvancedFundAnalyzer()
    analyzer.load_and_analyze()

    for level in ["保守", "稳健", "平衡", "进取", "激进"]:
        print(analyzer.format_portfolio_advice(risk_level=level))
        print("\n" + "·" * 70 + "\n")


if __name__ == "__main__":
    print("基金分析系统 - 增强版示例\n")

    example_1_technical_indicators()
    example_2_multi_strategy_backtest()
    example_3_custom_backtest()
    example_4_full_system()
    example_5_risk_level_comparison()

    print("\n" + "=" * 70)
    print("✅ 所有示例执行完毕")
    print("=" * 70)
