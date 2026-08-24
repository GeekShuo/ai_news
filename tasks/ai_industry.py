"""① AI 产业日报：科技大厂动态 / 战略活动 / AI 相关产品发布。"""
import datetime
import json

import llm
from config import RSSHUB_BASE
from core.models import Item
from core.report import deliver
from core.state import State
from sources.github_trending import fetch_github_trending
from sources.hn import fetch_hn_ai
from sources.rss import fetch_feed


def _feeds() -> list[tuple[str, str]]:
    feeds = [
        ("量子位", "https://www.qbitai.com/feed"),
        ("InfoQ中文", "https://www.infoq.cn/feed"),
        ("TechCrunch·AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("MIT科技评论·AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
    ]
    if RSSHUB_BASE:
        feeds += [
            ("36氪快讯", f"{RSSHUB_BASE}/36kr/newsflashes"),
            ("华尔街见闻", f"{RSSHUB_BASE}/wallstreetcn/news"),
            ("机器之心", f"{RSSHUB_BASE}/jiqizhixin"),
        ]
    return feeds


def collect(hours: float = 36) -> list[Item]:
    items: list[Item] = []
    for name, url in _feeds():
        items += fetch_feed(name, url, hours=hours)
    items += fetch_hn_ai(hours=hours)
    items += fetch_github_trending()
    return items


PROMPT = """你是 AI 产业情报分析师。下面是过去一天抓取的科技新闻与 GitHub 热门项目（JSON 列表，含 title/source/url/published/summary）。
读者：互联网大厂算法岗实习生，只关心 AI 相关的产业动态。

请输出 Markdown 日报，结构：
# AI 产业日报 {date}
## 头条
1-3 条最重要的事件，每条 2-3 句讲清发生了什么、为什么重要，附链接。
## 大厂动态
科技大厂（国内外）与 AI 相关的战略、组织、产品、模型发布。逐条：【公司】事件 —— 一句话点评，附链接。
## 技术与开源
值得关注的新模型 / 新工具 / GitHub 热门项目，逐条一句话点评，附链接。
## 风向一句话
今天产业界整体风向，一句话。

要求：只选 AI 相关内容，无关的消费/娱乐/社会新闻直接丢弃；中文输出；不要编造列表里没有的链接。

条目列表：
{items}"""


def build(items: list[Item]) -> str:
    date = datetime.date.today().isoformat()
    if not items:
        return f"# AI 产业日报 {date}\n\n今日无新增内容。"
    payload = [{"title": it.title, "source": it.source, "url": it.url,
                "published": it.published, "summary": it.summary,
                **({"language": it.extra.get("language"),
                    "stars_today": it.extra.get("stars_today")}
                   if it.source == "GitHub Trending" else {})}
               for it in items]
    return llm.complete(PROMPT.format(date=date,
                                      items=json.dumps(payload, ensure_ascii=False)))


def run(dry_run: bool = False, no_push: bool = False):
    items = collect()
    state = State("ai_industry")
    items = state.filter_new(items)
    print(f"[ok] 去重后剩余 {len(items)} 条")
    if dry_run:
        for it in items[:20]:
            print(f"- [{it.source}] {it.title} {it.url}")
        return
    md = build(items)
    for it in items:
        state.mark(it.id, {"title": it.title})
    state.save()
    deliver("ai_industry", md, push=not no_push)
