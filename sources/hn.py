import time

import requests

from core.models import Item


def fetch_hn_ai(hours: float = 36, min_points: int = 30, limit: int = 15) -> list[Item]:
    """Hacker News 官方 Algolia API：最近 hours 小时、分数达标、与 AI 相关的热帖。"""
    cutoff = int(time.time() - hours * 3600)
    try:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": "AI", "tags": "story", "hitsPerPage": limit,
                    "numericFilters": f"points>{min_points},created_at_i>{cutoff}"},
            timeout=15).json()
    except Exception as e:
        print(f"[warn] HN 抓取失败: {e}")
        return []
    items = []
    for h in r.get("hits", [])[:limit]:
        oid = h.get("objectID", "")
        items.append(Item(
            id=f"hn_{oid}",
            title=h.get("title", ""),
            url=h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
            source="HN·AI热帖",
            published=time.strftime("%Y-%m-%d", time.localtime(h.get("created_at_i", 0))),
            summary=f"HN {h.get('points', 0)} 分 / {h.get('num_comments', 0)} 评论",
        ))
    print(f"[ok] HN·AI热帖: {len(items)} 条")
    return items
