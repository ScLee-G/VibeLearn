"""
金融新闻智能助手 - 模块入口
"""

from .financial_news import (
    NewsItem,
    FinancialNewsFetcher,
    BriefFormatter,
    get_morning_brief,
    save_brief_to_file
)

__all__ = [
    "NewsItem",
    "FinancialNewsFetcher",
    "BriefFormatter",
    "get_morning_brief",
    "save_brief_to_file"
]
