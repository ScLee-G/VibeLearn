"""
金融新闻智能助手 - 自动获取并分析最新金融新闻
"""

from datetime import datetime, date
from typing import List, Dict, Optional
import json
import os


class NewsItem:
    """新闻条目"""
    def __init__(
        self,
        title: str,
        content: str,
        impact: str,
        source: str,
        time: str,
        importance: int = 2
    ):
        self.title = title
        self.content = content
        self.impact = impact
        self.source = source
        self.time = time
        self.importance = importance
    
    @property
    def importance_stars(self) -> str:
        stars = ['⭐', '⭐⭐', '⭐⭐⭐']
        return stars[min(self.importance - 1, 2)]


class FinancialNewsFetcher:
    """金融新闻获取器"""
    
    def __init__(self):
        self.news_items: List[NewsItem] = []
    
    def fetch_news(self) -> List[NewsItem]:
        """获取金融新闻"""
        print("正在获取最新金融新闻...")
        
        # 这里模拟获取新闻的逻辑
        # 实际应用中应该调用真实的新闻API
        self._fetch_simulated_news()
        
        # 按重要性排序
        self.news_items.sort(key=lambda x: (-x.importance, x.time))
        return self.news_items
    
    def _fetch_simulated_news(self) -> None:
        """模拟获取新闻（用于演示）"""
        self.news_items = [
            NewsItem(
                title="央行宣布下调存款准备金率 0.5 个百分点",
                content="为支持实体经济发展，中国人民银行决定下调金融机构存款准备金率 0.5 个百分点，释放长期资金约 1 万亿元。",
                impact="预计对股市和债市产生积极影响，尤其是金融、地产等板块可能受益。",
                source="央行官网",
                time=f"{date.today()} 07:30",
                importance=3
            ),
            NewsItem(
                title="A股三大指数集体高开，科技板块领涨",
                content="受海外市场利好消息影响，今日A股三大指数集体高开，创业板指涨逾 2%。科技、新能源板块表现活跃。",
                impact="短期市场情绪乐观，但需关注成交量变化。",
                source="财新网",
                time=f"{date.today()} 08:15",
                importance=2
            ),
            NewsItem(
                title="油价突破 80 美元，创年内新高",
                content="受OPEC+减产决定影响，国际油价突破 80 美元/桶，创年内新高。",
                impact="利好石油相关板块，但可能加剧通胀预期。",
                source="华尔街见闻",
                time=f"{date.today()} 07:00",
                importance=2
            ),
            NewsItem(
                title="大型科技公司公布财报，营收超预期",
                content="多家头部科技公司公布最新财报，营收均超市场预期。",
                impact="对科技板块有积极影响。",
                source="新浪财经",
                time=f"{date.today()} 06:45",
                importance=1
            )
        ]


class BriefFormatter:
    """晨报格式化"""
    
    @staticmethod
    def format_brief(news_items: List[NewsItem]) -> str:
        """格式化晨报"""
        today = date.today().strftime('%Y-%m-%d')
        
        lines = [
            f"【金融晨报】{today}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        for i, item in enumerate(news_items[:10], 1):
            lines.extend([
                f"{i}. [{item.importance_stars}] {item.title}",
                f"   内容：{item.content}",
                f"   影响：{item.impact}",
                f"   来源：{item.source} | {item.time}",
                ""
            ])
        
        if not news_items:
            lines.extend([
                "今日暂无重要金融新闻。",
                ""
            ])
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "市场有风险，投资需谨慎。",
            ""
        ])
        
        return '\n'.join(lines)


def get_morning_brief() -> str:
    """获取晨间简报（主入口）"""
    print(f"===== 【金融晨报】{date.today()} =====")
    print()
    
    fetcher = FinancialNewsFetcher()
    news_items = fetcher.fetch_news()
    
    formatter = BriefFormatter()
    brief = formatter.format_brief(news_items)
    
    print(brief)
    return brief


def save_brief_to_file(brief: str, directory: str = ".") -> str:
    """保存简报到文件"""
    today = date.today().strftime('%Y-%m-%d')
    filename = f"{directory}/financial_brief_{today}.txt"
    
    os.makedirs(directory, exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(brief)
    
    print(f"简报已保存至：{filename}")
    return filename


if __name__ == "__main__":
    brief = get_morning_brief()
    save_brief_to_file(brief, "./financial_briefs")
