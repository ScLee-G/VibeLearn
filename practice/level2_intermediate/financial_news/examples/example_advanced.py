"""
金融新闻增强版 - 使用示例
================================================
本文件演示增强版系统的多种用法。
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from financial_news_advanced import (
    get_morning_brief_advanced,
    get_strategic_brief,
    save_brief_to_file,
    NewsDataProvider,
    BriefBuilder,
    RuleEngine,
    NewsItem,
)


def example_1_basic_text():
    """示例 1：基础纯文本简报（兼容旧接口）"""
    print("=" * 60)
    print("【示例 1】基础文本简报")
    print("=" * 60)
    brief = get_morning_brief_advanced(output_format="text")
    print(brief[:800], "..." if len(brief) > 800 else "")
    return brief


def example_2_markdown_report():
    """示例 2：Markdown 格式的完整报告"""
    print("\n" + "=" * 60)
    print("【示例 2】Markdown 格式报告")
    print("=" * 60)
    brief = get_morning_brief_advanced(output_format="markdown")
    save_brief_to_file(brief, "./outputs")
    print("已生成 Markdown 报告，文件位于 outputs/ 目录")
    return brief


def example_3_rule_engine_demo():
    """示例 3：规则引擎打分演示（单条新闻的处理流程）"""
    print("\n" + "=" * 60)
    print("【示例 3】规则引擎 - 单条新闻评分演示")
    print("=" * 60)

    sample = NewsItem(
        title="央行宣布下调存款准备金率0.5个百分点",
        content="为支持实体经济发展，中国人民银行决定下调金融机构存款准备金率 0.5 个百分点，释放长期资金约 1 万亿元。",
        source="央行官网",
        publish_time="2026-06-18 09:00",
    )
    scored = RuleEngine.score_news(sample)

    print(f"标题：{scored.title}")
    print(f"重要性：{'⭐' * scored.importance} ({scored.importance}/3)")
    print(f"原始评分：{scored.raw_score}")
    print(f"情绪：{scored.sentiment:+.2f}")
    print(f"分类：{scored.category}")
    print(f"关键词：{', '.join(scored.keywords)}")
    return scored


def example_4_custom_data_source():
    """示例 4：使用自定义新闻源（不依赖网络）"""
    print("\n" + "=" * 60)
    print("【示例 4】自定义数据源")
    print("=" * 60)

    my_news = [
        NewsItem(
            title="宁德时代发布最新一代麒麟电池",
            content="宁德时代正式发布最新一代麒麟电池，能量密度提升25%，充电速度提升50%。",
            source="第一财经",
            publish_time="2026-06-18 10:00",
        ),
        NewsItem(
            title="国内AI大模型市场规模预计突破3000亿元",
            content="根据最新行业报告，国内AI大模型市场规模预计在2026年突破3000亿元，带动算力需求持续增长。",
            source="新浪财经",
            publish_time="2026-06-18 11:00",
        ),
    ]

    # 对自定义数据应用规则引擎
    scored = [RuleEngine.score_news(n) for n in my_news]

    # 构建简报
    builder = BriefBuilder()
    brief = builder.build_morning_brief(scored, max_items=5)
    print(builder.format_text(brief))
    return brief


def example_5_try_real_data():
    """示例 5：尝试真实数据源（如无网络自动回退到模拟数据）"""
    print("\n" + "=" * 60)
    print("【示例 5】尝试真实 RSS 数据源")
    print("=" * 60)
    print("提示：如果没有网络连接，系统将自动回退到模拟数据。\n")

    brief = get_morning_brief_advanced(
        use_real_data=True,
        use_llm=False,
        output_format="text",
        max_items=6,
    )
    print(brief)
    return brief


def example_6_multi_strategy_comparison():
    """示例 6：多种策略对比 - 展示不同过滤视角"""
    print("\n" + "=" * 60)
    print("【示例 6】策略对比 - 不同过滤视角")
    print("=" * 60)

    # 先生成完整新闻池
    provider = NewsDataProvider(use_real_data=False)
    news_pool = provider.fetch_all()

    strategies = {
        "重大新闻": lambda n: n.importance == 3,
        "宏观政策": lambda n: n.category == "宏观政策",
        "积极情绪": lambda n: n.sentiment > 0,
        "行业动态": lambda n: n.category == "行业动态",
    }

    for name, filter_fn in strategies.items():
        filtered = [n for n in news_pool if filter_fn(n)]
        print(f"\n--- {name} ({len(filtered)} 条) ---")
        for n in filtered[:3]:
            stars = "⭐" * n.importance
            print(f"  {stars} {n.title}")


if __name__ == "__main__":
    print("金融新闻智能助手 - 增强版示例\n")

    # 执行所有示例
    example_1_basic_text()
    example_2_markdown_report()
    example_3_rule_engine_demo()
    example_4_custom_data_source()
    example_5_try_real_data()
    example_6_multi_strategy_comparison()

    print("\n" + "=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)
