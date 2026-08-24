import datetime
import re

import feedparser

from core.models import Item

_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) daily_brief/1.0"}


def strip_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def fetch_feed(name: str, url: str, hours: float = 36, limit: int = 40) -> list[Item]:
    """抓一个 RSS 源，只保留最近 hours 小时的条目。失败返回空列表。"""
    try:
        feed = feedparser.parse(url, request_headers=_UA)
    except Exception as e:
        print(f"[warn] RSS 抓取失败 {name}: {e}")
        return []
    if feed.bozo and not feed.entries:
        print(f"[warn] RSS 解析失败 {name}: {url}")
        return []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    items = []
    for e in feed.entries[:limit]:
        dt = None
        for k in ("published_parsed", "updated_parsed"):
            if e.get(k):
                dt = datetime.datetime(*e[k][:6], tzinfo=datetime.timezone.utc)
                break
        if dt and dt < cutoff:
            continue
        items.append(Item(
            id=e.get("link") or e.get("id") or e.get("title", ""),
            title=e.get("title", "").strip(),
            url=e.get("link", ""),
            source=name,
            published=dt.date().isoformat() if dt else "",
            summary=strip_html(e.get("summary", ""))[:500],
        ))
    print(f"[ok] {name}: {len(items)} 条")
    return items
