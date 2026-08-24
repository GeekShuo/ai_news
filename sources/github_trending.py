import requests
from bs4 import BeautifulSoup

from core.models import Item


def fetch_github_trending(limit: int = 15) -> list[Item]:
    """GitHub Trending（日榜）。"""
    try:
        html = requests.get("https://github.com/trending?since=daily", timeout=30,
                            headers={"User-Agent": "Mozilla/5.0"}).text
    except Exception as e:
        print(f"[warn] GitHub Trending 抓取失败: {e}")
        return []
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for row in soup.select("article.Box-row")[:limit]:
        a = row.select_one("h2 a")
        if not a:
            continue
        repo = a.get("href", "").strip("/")
        desc = row.select_one("p")
        lang = row.select_one('[itemprop="programmingLanguage"]')
        stars = row.select_one("span.d-inline-block.float-sm-right")
        items.append(Item(
            id=repo,
            title=repo,
            url=f"https://github.com/{repo}",
            source="GitHub Trending",
            summary=desc.get_text(strip=True) if desc else "",
            extra={"language": lang.get_text(strip=True) if lang else "",
                   "stars_today": stars.get_text(strip=True) if stars else ""},
        ))
    print(f"[ok] GitHub Trending: {len(items)} 条")
    return items
