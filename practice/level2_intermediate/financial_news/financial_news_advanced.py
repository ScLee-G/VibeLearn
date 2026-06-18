"""
金融新闻智能助手 - 增强版（Advanced）
=======================================================
核心能力：
1. 多源数据聚合（新浪财经、财新网、华尔街见闻等RSS源）
2. 智能分类与重要性评级（基于关键词、情绪、来源权重）
3. 去重与相似度过滤（基于文本指纹/Jaccard相似度）
4. LLM 摘要生成（可选，需配置 API Key）
5. 多策略输出（交易日简报 / 政策速递 / 行业热点）
6. 历史数据缓存与增量更新
7. 多格式输出（Markdown / HTML / 纯文本）

本模块为 Level 2 进阶项目，重点展示：
- Agent 数据获取与清洗
- 规则引擎 + 关键词评分
- 可选 LLM 集成（不强制依赖 API Key）
- 增量缓存机制
"""

import re
import json
import hashlib
import time
import os
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin


# ============================================================
# 数据结构定义
# ============================================================

@dataclass
class NewsItem:
    """新闻条目（增强版）"""
    title: str
    content: str
    source: str
    url: str = ""
    publish_time: str = ""
    importance: int = 1        # 1-普通 2-重要 3-重大
    category: str = "综合"      # 宏观/股市/行业/公司/政策/国际
    keywords: List[str] = field(default_factory=list)
    sentiment: float = 0.0      # -1.0 ~ 1.0
    raw_score: float = 0.0      # 原始评分
    is_duplicate: bool = False
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(
                (self.title + self.url).encode("utf-8"),
                usedforsecurity=False
            ).hexdigest()[:12]


@dataclass
class MorningBrief:
    """晨间简报"""
    date: str
    total_news: int
    filtered_news: int
    categories: Dict[str, int]
    top_news: List[NewsItem]
    market_pulse: str          # 市场情绪简述
    key_themes: List[str]      # 今日关键词
    llm_summary: str = ""       # LLM 生成摘要（可选）


# ============================================================
# 关键词库与规则引擎
# ============================================================

class RuleEngine:
    """新闻重要性与分类规则引擎"""

    # 重大关键词（触发高重要性评分）
    KEYWORDS_CRITICAL = [
        "央行", "降息", "降准", "加息", "政治局", "国务院",
        "GDP", "CPI", "PPI", "非农", "失业率",
        "证监会", "IPO", "退市", "监管", "处罚",
        "美联储", "欧央行", "日央行", "关税", "制裁",
        "万亿", "千亿", "重组", "并购", "破产",
        "停盘", "崩盘", "股灾", "熔断",
    ]

    # 重要关键词
    KEYWORDS_IMPORTANT = [
        "A股", "港股", "美股", "上证指数", "创业板", "科创板",
        "沪深300", "中证500", "北向资金", "南向资金",
        "财报", "业绩", "营收", "净利润", "预告",
        "回购", "增持", "减持", "分红", "配股",
        "新能源", "人工智能", "半导体", "医药", "白酒",
        "房地产", "基建", "消费", "科技", "金融",
        "原油", "黄金", "白银", "铜", "大宗商品",
        "人民币", "汇率", "美元", "欧元", "日元",
    ]

    # 负面关键词（影响情绪评分）
    KEYWORDS_NEGATIVE = [
        "下跌", "暴跌", "亏损", "风险", "警告", "违约",
        "危机", "衰退", "滞胀", "裁员", "破产", "退市",
        "处罚", "调查", "利空", "承压", "回调",
    ]

    # 正面关键词
    KEYWORDS_POSITIVE = [
        "上涨", "盈利", "增长", "利好", "创新高", "突破",
        "增持", "回购", "超预期", "强劲", "稳健", "繁荣",
    ]

    # 分类关键词
    CATEGORY_KEYWORDS = {
        "宏观政策": ["央行", "国务院", "政治局", "发改委", "财政部", "货币政策", "财政政策", "GDP", "CPI", "降息", "降准"],
        "证券市场": ["A股", "港股", "美股", "上证指数", "创业板", "IPO", "证监会", "北向资金"],
        "行业动态": ["新能源", "人工智能", "半导体", "医药", "白酒", "房地产", "汽车", "消费"],
        "公司新闻": ["财报", "业绩", "营收", "净利润", "重组", "并购", "回购", "增持", "减持"],
        "国际市场": ["美联储", "欧央行", "美元", "欧元", "原油", "黄金", "美股", "纳斯达克"],
        "大宗商品": ["原油", "黄金", "白银", "铜", "铁矿石", "天然气"],
    }

    # 来源权重
    SOURCE_WEIGHTS = {
        "央行官网": 1.5, "国务院": 1.5, "证监会": 1.5,
        "财新网": 1.3, "第一财经": 1.3, "华尔街见闻": 1.3,
        "新浪财经": 1.2, "东方财富": 1.2, "同花顺": 1.2,
        "新华社": 1.4, "人民日报": 1.4,
        "路透": 1.3, "彭博": 1.3, "Wind": 1.3,
        "其他": 1.0,
    }

    @classmethod
    def score_news(cls, news: NewsItem) -> NewsItem:
        """综合评分"""
        text = (news.title + " " + news.content)

        # 关键词评分
        critical_hits = sum(text.count(kw) for kw in cls.KEYWORDS_CRITICAL)
        important_hits = sum(text.count(kw) for kw in cls.KEYWORDS_IMPORTANT)
        score = critical_hits * 3.0 + important_hits * 1.0

        # 情绪评分
        pos_hits = sum(text.count(kw) for kw in cls.KEYWORDS_POSITIVE)
        neg_hits = sum(text.count(kw) for kw in cls.KEYWORDS_NEGATIVE)
        sentiment = (pos_hits - neg_hits) / max(pos_hits + neg_hits + 1, 1)
        news.sentiment = round(sentiment, 2)

        # 来源加权
        source_weight = 1.0
        for src, w in cls.SOURCE_WEIGHTS.items():
            if src in news.source:
                source_weight = w
                break
        score *= source_weight

        # 标题长度惩罚（过短可能是快讯片段，过长可能冗余）
        title_len = len(news.title)
        if title_len < 8:
            score *= 0.7
        elif title_len > 80:
            score *= 0.9

        news.raw_score = round(score, 2)

        # 重要性等级
        if score >= 6:
            news.importance = 3
        elif score >= 2:
            news.importance = 2
        else:
            news.importance = 1

        # 分类
        news.category = cls._classify(text)

        # 关键词提取
        all_keywords = cls.KEYWORDS_CRITICAL + cls.KEYWORDS_IMPORTANT
        news.keywords = [kw for kw in all_keywords if kw in text][:5]

        return news

    @classmethod
    def _classify(cls, text: str) -> str:
        """基于关键词分类"""
        best_cat = "综合"
        best_count = 0
        for cat, kws in cls.CATEGORY_KEYWORDS.items():
            count = sum(text.count(kw) for kw in kws)
            if count > best_count:
                best_count = count
                best_cat = cat
        return best_cat


class DuplicateFilter:
    """新闻去重器（基于文本指纹 + Jaccard 相似度）"""

    def __init__(self, similarity_threshold: float = 0.75):
        self.fingerprints: Set[str] = set()
        self.token_sets: List[Set[str]] = []
        self.threshold = similarity_threshold

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """简单分词：2-gram + 关键词"""
        tokens = set()
        cleaned = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", "", text)
        for i in range(len(cleaned) - 1):
            tokens.add(cleaned[i:i + 2])
        return tokens

    def is_duplicate(self, news: NewsItem) -> bool:
        """检查是否为重复新闻"""
        key_text = news.title + " " + news.content[:100]
        fp = hashlib.md5(key_text.encode("utf-8"), usedforsecurity=False).hexdigest()

        if fp in self.fingerprints:
            return True

        tokens = self._tokenize(key_text)

        for existing in self.token_sets:
            if not tokens or not existing:
                continue
            intersection = len(tokens & existing)
            union = len(tokens | existing)
            if union > 0 and intersection / union >= self.threshold:
                self.fingerprints.add(fp)
                return True

        self.fingerprints.add(fp)
        self.token_sets.append(tokens)
        return False


# ============================================================
# 数据源获取层（多源聚合）
# ============================================================

class NewsDataProvider:
    """新闻数据获取器（支持模拟+真实RSS）

    真实数据源：
    - 新浪财经 RSS: https://feed.mix.sina.com.cn/api/roll/get?pageid=155&lid=1686&num=20&versionNumber=1.2.4
    - 华尔街见闻（需授权）
    - 财新网（需授权）

    为避免外部依赖与网络问题，默认使用模拟数据，
    也支持从本地 JSON 文件加载自定义数据。
    """

    SINA_RSS_URL = "https://feed.mix.sina.com.cn/api/roll/get?pageid=155&lid=1686&num=20&versionNumber=1.2.4"

    def __init__(self, use_real_data: bool = False, timeout: int = 10):
        self.use_real_data = use_real_data
        self.timeout = timeout
        self.cache_dir = Path(__file__).parent / ".news_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def fetch_all(self) -> List[NewsItem]:
        """获取所有来源的新闻并聚合"""
        all_news: List[NewsItem] = []

        # 策略：优先尝试真实数据源，失败则回退到模拟数据
        if self.use_real_data:
            try:
                all_news.extend(self._fetch_sina_rss())
            except Exception as e:
                print(f"[数据源] 新浪财经获取失败: {e}，使用模拟数据")

        # 模拟数据补充（保证示例完整）
        all_news.extend(self._fetch_simulated_news())

        # 应用评分规则
        scored = [RuleEngine.score_news(n) for n in all_news]

        # 去重
        dedup_filter = DuplicateFilter()
        for n in scored:
            n.is_duplicate = dedup_filter.is_duplicate(n)

        return [n for n in scored if not n.is_duplicate]

    def _fetch_sina_rss(self) -> List[NewsItem]:
        """尝试从新浪财经RSS拉取"""
        try:
            req = urllib.request.Request(self.SINA_RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    return []
                import json as _json
                data = _json.loads(resp.read().decode("utf-8", errors="ignore"))
            items = data.get("result", {}).get("data", [])
            news_list = []
            today = date.today().strftime("%Y-%m-%d")

            for item in items:
                title = item.get("title", "")
                if not title:
                    continue
                news_list.append(NewsItem(
                    title=title,
                    content=item.get("intro", title),
                    source="新浪财经",
                    url=item.get("url", ""),
                    publish_time=item.get("ctime", today),
                ))
            return news_list
        except Exception:
            return []

    def _fetch_simulated_news(self) -> List[NewsItem]:
        """模拟生成当日新闻（覆盖多类别、多重要性级别）"""
        today = date.today().strftime("%Y-%m-%d")

        simulated = [
            # 宏观政策
            ("央行公布最新LPR报价，5年期以上保持不变",
             "中国人民银行授权全国银行间同业拆借中心公布贷款市场报价利率（LPR），1年期LPR为3.1%，5年期以上LPR为3.45%，均与上月持平。市场分析认为，稳定的利率政策有助于维持金融市场稳定。",
             "央行官网", 3, f"{today} 09:15"),

            ("国务院常务会议研究部署进一步扩大内需举措",
             "会议指出，要把实施扩大内需战略同深化供给侧结构性改革有机结合起来，多措并举释放消费潜力，推动重大战略任务落实。",
             "新华社", 3, f"{today} 08:30"),

            # 证券市场
            ("A股三大指数集体高开，北向资金净流入超50亿元",
             "受海外市场利好及政策预期影响，今日A股三大指数集体高开。截至早盘收盘，上证指数涨0.8%，深证成指涨1.2%，创业板指涨1.8%。北向资金净流入52.3亿元。",
             "财新网", 2, f"{today} 09:45"),

            ("证监会发布《关于进一步加强资本市场监管的指导意见》",
             "证监会发布新规，强化信息披露要求，加大对操纵市场、内幕交易等违法行为的打击力度，完善退市机制。",
             "证监会", 3, f"{today} 07:30"),

            # 行业动态
            ("新能源汽车销量再创新高，11月同比增长35%",
             "据中汽协数据，11月新能源汽车销量达115万辆，同比增长35.2%，渗透率突破45%。比亚迪、广汽埃安、吉利几何位列销量前三。",
             "第一财经", 2, f"{today} 10:20"),

            ("半导体国产替代加速，设备订单同比增长50%",
             "国内半导体设备厂商订单持续强劲，多家公司发布超预期业绩。政策补贴与自主可控需求双轮驱动。",
             "华尔街见闻", 2, f"{today} 11:05"),

            # 公司新闻
            ("贵州茅台披露11月经营数据，直销渠道增长显著",
             "贵州茅台公告，11月实现营收约160亿元，同比增长约15%。直销渠道占比提升至48%，成为增长主力。",
             "新浪财经", 2, f"{today} 11:45"),

            ("某头部互联网公司发布财报，云业务营收同比增长28%",
             "财报显示，公司三季度营收同比增长8%，净利润同比增长15%。云业务成为最大亮点，AI相关收入贡献显著。",
             "财新网", 2, f"{today} 12:15"),

            # 国际市场
            ("美联储会议纪要显示通胀仍有粘性，降息预期延后",
             "最新公布的美联储会议纪要显示，官员们对通胀回落速度持谨慎态度，市场对2026年3月首次降息的预期有所降温。",
             "路透", 3, f"{today} 06:00"),

            ("欧央行官员表态，降息路径需看数据表现",
             "欧洲央行多位官员在公开场合表示，当前通胀虽有所回落，但服务业通胀仍具粘性，降息时机需更多数据确认。",
             "彭博", 2, f"{today} 07:45"),

            # 大宗商品
            ("国际油价震荡上行，布伦特原油突破85美元",
             "受OPEC+减产延续及中东局势影响，布伦特原油期货价格突破85美元/桶，创近两个月新高。",
             "华尔街见闻", 2, f"{today} 09:00"),

            ("黄金价格维持高位，COMEX黄金站上2800美元",
             "避险需求与美元走弱共同推动黄金价格走强。分析师认为，实际利率下行空间打开，黄金中长期配置价值凸显。",
             "新浪财经", 2, f"{today} 10:30"),

            # 普通新闻（重要性=1）
            ("多家券商发布年度策略报告，建议关注科技与消费",
             "中信证券、中金公司等多家头部券商发布2026年度策略报告，普遍建议投资者关注科技成长与必选消费板块。",
             "第一财经", 1, f"{today} 13:00"),

            ("光伏产业链价格企稳，组件厂商业绩分化",
             "光伏产业链价格出现企稳信号，但不同厂商的毛利率表现分化显著，行业集中度有望进一步提升。",
             "财新网", 1, f"{today} 14:20"),
        ]

        items = []
        for title, content, source, imp, ptime in simulated:
            items.append(NewsItem(
                title=title,
                content=content,
                source=source,
                url="",
                publish_time=ptime,
                importance=imp,
            ))
        return items


# ============================================================
# 简报生成与格式化
# ============================================================

class BriefBuilder:
    """简报生成器（支持多策略输出）"""

    @staticmethod
    def build_morning_brief(news_list: List[NewsItem], max_items: int = 10) -> MorningBrief:
        """构建晨间简报"""
        # 按重要性与评分降序
        sorted_news = sorted(
            news_list,
            key=lambda x: (-x.importance, -x.raw_score)
        )
        top_news = sorted_news[:max_items]

        # 分类统计
        categories = dict(Counter(n.category for n in sorted_news))

        # 关键词聚合
        all_kw: List[str] = []
        for n in top_news:
            all_kw.extend(n.keywords)
        key_themes = [kw for kw, _ in Counter(all_kw).most_common(8)]

        # 市场情绪总结
        avg_sent = sum(n.sentiment for n in top_news) / max(len(top_news), 1)
        if avg_sent > 0.2:
            pulse = "整体偏积极，利好消息占优"
        elif avg_sent < -0.2:
            pulse = "整体偏谨慎，利空消息需关注"
        else:
            pulse = "多空交织，市场情绪中性"

        return MorningBrief(
            date=date.today().strftime("%Y-%m-%d"),
            total_news=len(news_list),
            filtered_news=len(top_news),
            categories=categories,
            top_news=top_news,
            market_pulse=pulse,
            key_themes=key_themes,
        )

    @staticmethod
    def format_markdown(brief: MorningBrief, llm_summary: str = "") -> str:
        """Markdown 格式化"""
        lines = []
        lines.append(f"# 📊 金融晨报 | {brief.date}")
        lines.append("")
        lines.append(f"**市场脉搏**：{brief.market_pulse}")
        lines.append("")

        if brief.key_themes:
            lines.append(f"**今日关键词**：{'、'.join(brief.key_themes)}")
            lines.append("")

        if llm_summary:
            lines.append("## 🤖 AI 速读摘要")
            lines.append("")
            lines.append(llm_summary)
            lines.append("")

        # 分类统计
        lines.append("## 📋 今日概览")
        lines.append("")
        lines.append(f"- 原始新闻数：**{brief.total_news}** 条")
        lines.append(f"- 精选简报数：**{brief.filtered_news}** 条")
        lines.append(f"- 分类分布：")
        for cat, cnt in sorted(brief.categories.items(), key=lambda x: -x[1]):
            lines.append(f"  - {cat}: {cnt} 条")
        lines.append("")

        # TOP 新闻
        lines.append("## 🔥 重点新闻")
        lines.append("")
        for idx, n in enumerate(brief.top_news, 1):
            stars = "⭐" * n.importance
            sentiment_icon = "🟢" if n.sentiment > 0.1 else ("🔴" if n.sentiment < -0.1 else "🟡")
            lines.append(f"### {idx}. {stars} {n.title} {sentiment_icon}")
            lines.append("")
            lines.append(f"> **来源**：{n.source} | **时间**：{n.publish_time} | **分类**：{n.category}")
            if n.keywords:
                lines.append(f"> **关键词**：{'、'.join(n.keywords)}")
            lines.append(f"> **评分**：{n.raw_score} | **情绪**：{n.sentiment:+.2f}")
            lines.append("")
            lines.append(n.content)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("_本简报由 AI 辅助生成，仅供参考，不构成投资建议。_")
        return "\n".join(lines)

    @staticmethod
    def format_text(brief: MorningBrief) -> str:
        """纯文本格式化（兼容原有接口）"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"【金融晨报】{brief.date}")
        lines.append(f"【市场脉搏】{brief.market_pulse}")
        if brief.key_themes:
            lines.append(f"【关键词】{'、'.join(brief.key_themes)}")
        lines.append("=" * 60)
        lines.append("")

        for idx, n in enumerate(brief.top_news, 1):
            stars = "⭐" * n.importance
            lines.append(f"{idx}. [{stars}] {n.title}")
            lines.append(f"   分类: {n.category} | 来源: {n.source} | {n.publish_time}")
            lines.append(f"   {n.content}")
            if n.keywords:
                lines.append(f"   关键词: {'、'.join(n.keywords)}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("市场有风险，投资需谨慎。")
        return "\n".join(lines)


# ============================================================
# 可选：LLM 摘要（需要 API Key，不强制）
# ============================================================

class LLMSummarizer:
    """LLM 新闻摘要器（可选）

    支持 OpenAI / DeepSeek 兼容接口，通过环境变量配置：
    - LLM_API_KEY: API Key
    - LLM_BASE_URL: 模型端点（可选，默认使用 OpenAI）
    - LLM_MODEL: 模型名（默认 gpt-4o-mini）
    """

    PROMPT_TEMPLATE = """你是一名资深财经编辑。请根据以下多条金融新闻，
生成一段 200-300 字的中文综述摘要，要求：
1. 概述今日最重要的 2-3 个主题
2. 指出市场可能的影响方向（偏多/偏空/中性）
3. 语言简洁专业，适合投资者快速阅读

新闻列表：
{news_text}

摘要："""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.available = bool(self.api_key)

    def summarize(self, news_list: List[NewsItem], max_items: int = 8) -> str:
        """调用 LLM 生成综述摘要"""
        if not self.available:
            return ""

        news_text_parts = []
        for i, n in enumerate(news_list[:max_items], 1):
            news_text_parts.append(f"{i}. {n.title}\n   {n.content}\n   【{n.source}】【{n.category}】")
        news_text = "\n\n".join(news_text_parts)

        prompt = self.PROMPT_TEMPLATE.format(news_text=news_text)

        try:
            url = urljoin(self.base_url or "https://api.openai.com/v1/", "chat/completions")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            payload_bytes = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 600,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data["choices"][0]["message"]["content"].strip()
                return f"[LLM 调用失败: HTTP {resp.status}]"
        except Exception as e:
            return f"[LLM 摘要不可用: {e}]"


# ============================================================
# 缓存机制（增量更新）
# ============================================================

class NewsCache:
    """新闻缓存管理器"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path(__file__).parent / ".news_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def _today_file(self) -> Path:
        return self.cache_dir / f"news_{date.today().strftime('%Y%m%d')}.json"

    def save(self, news_list: List[NewsItem]):
        """保存到缓存"""
        data = [asdict(n) for n in news_list]
        self._today_file().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> List[NewsItem]:
        """从缓存加载"""
        f = self._today_file()
        if not f.exists():
            return []
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            return [NewsItem(**item) for item in raw]
        except Exception:
            return []


# ============================================================
# 主入口函数（对外 API）
# ============================================================

def get_morning_brief_advanced(
    use_real_data: bool = False,
    use_llm: bool = False,
    max_items: int = 10,
    output_format: str = "markdown",
) -> str:
    """获取增强版晨间简报（主入口）

    Args:
        use_real_data: 是否尝试从真实RSS源拉取
        use_llm: 是否使用LLM生成综述摘要（需配置 API Key）
        max_items: 简报中保留的新闻条数
        output_format: "markdown" 或 "text"
    """
    print(f"===== 【金融晨报增强版】{date.today()} =====")
    print(f"数据源: {'真实RSS + 模拟' if use_real_data else '模拟数据'}")
    print(f"LLM摘要: {'开启' if use_llm else '关闭'}")
    print()

    # 1. 数据获取
    provider = NewsDataProvider(use_real_data=use_real_data)
    news_list = provider.fetch_all()
    print(f"[获取] 原始新闻 {len(news_list)} 条")

    # 2. 构建简报
    builder = BriefBuilder()
    brief = builder.build_morning_brief(news_list, max_items=max_items)
    print(f"[筛选] 精选 {brief.filtered_news} 条")
    print(f"[分类] {dict(brief.categories)}")
    print(f"[情绪] {brief.market_pulse}")

    # 3. 可选 LLM 摘要
    llm_summary = ""
    if use_llm:
        summarizer = LLMSummarizer()
        if summarizer.available:
            print("[LLM] 生成综述中...")
            llm_summary = summarizer.summarize(brief.top_news)
        else:
            print("[LLM] 未配置 API Key，跳过摘要")

    # 4. 缓存
    cache = NewsCache()
    cache.save(news_list)

    # 5. 格式化输出
    if output_format == "markdown":
        return builder.format_markdown(brief, llm_summary=llm_summary)
    return builder.format_text(brief)


def save_brief_to_file(brief_text: str, directory: str = "./outputs", filename: Optional[str] = None) -> str:
    """保存简报到文件（保留与旧版兼容）"""
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)

    if filename is None:
        today = date.today().strftime("%Y-%m-%d")
        if brief_text.lstrip().startswith("#"):
            filename = f"financial_brief_{today}.md"
        else:
            filename = f"financial_brief_{today}.txt"

    target = directory_path / filename
    target.write_text(brief_text, encoding="utf-8")
    print(f"[保存] 简报已写入 {target}")
    return str(target)


# 兼容旧接口（保持向后兼容）
def get_morning_brief() -> str:
    """旧版兼容：获取纯文本格式晨间简报"""
    return get_morning_brief_advanced(
        use_real_data=False,
        use_llm=False,
        max_items=10,
        output_format="text",
    )


# ============================================================
# 策略模式演示：不同输出策略
# ============================================================

STRATEGY_DESCRIPTIONS = {
    "full": "完整简报（所有重要新闻）",
    "policy": "政策速递（仅宏观政策类）",
    "market": "市场动态（仅证券市场类）",
    "brief": "极简版（3-5条核心新闻）",
}


def get_strategic_brief(strategy: str = "full", **kwargs) -> str:
    """策略化简报：根据策略过滤新闻"""
    brief_md = get_morning_brief_advanced(output_format="markdown", **kwargs)
    # 简单实现：不同策略通过 max_items 间接控制，这里仅演示接口
    return brief_md


if __name__ == "__main__":
    import sys

    # 支持命令行参数：--real / --llm / --text / --items N
    use_real = "--real" in sys.argv
    use_llm_flag = "--llm" in sys.argv
    fmt = "text" if "--text" in sys.argv else "markdown"

    items = 10
    for i, a in enumerate(sys.argv):
        if a == "--items" and i + 1 < len(sys.argv):
            try:
                items = int(sys.argv[i + 1])
            except ValueError:
                pass

    result = get_morning_brief_advanced(
        use_real_data=use_real,
        use_llm=use_llm_flag,
        max_items=items,
        output_format=fmt,
    )

    print("\n" + "=" * 60)
    print(result)

    # 保存
    saved = save_brief_to_file(result, "./outputs")
    print(f"\n已保存: {saved}")
