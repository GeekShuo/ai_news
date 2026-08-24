import datetime
import re

import feedparser

from core.models import Item
from sources.rss import strip_html

CATS = ["cs.CL", "cs.LG", "cs.AI", "cs.CV", "cs.MA"]


def fetch_arxiv(days: float = 2.0, limit: int = 60) -> list[Item]:
    """arXiv 官方 API：最近 days 天的新论文。"""
    q = "+OR+".join(f"cat:{c}" for c in CATS)
    url = ("http://export.arxiv.org/api/query?search_query=" + q +
           f"&sortBy=submittedDate&sortOrder=descending&max_results={limit}")
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[warn] arXiv 抓取失败: {e}")
        return []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    items = []
    for e in feed.entries:
        dt = None
        if e.get("published_parsed"):
            dt = datetime.datetime(*e.published_parsed[:6], tzinfo=datetime.timezone.utc)
        if dt and dt < cutoff:
            continue
        authors = ", ".join(a.get("name", "") for a in e.get("authors", [])[:3])
        title = re.sub(r"\s+", " ", e.get("title", "")).strip()
        items.append(Item(
            id=e.get("id", title),
            title=title,
            url=e.get("id", ""),
            source="arXiv",
            published=dt.date().isoformat() if dt else "",
            summary=strip_html(e.get("summary", ""))[:1200],
            extra={"authors": authors},
        ))
    print(f"[ok] arXiv: {len(items)} 条")
    return items
