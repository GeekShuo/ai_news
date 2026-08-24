import requests

from core.models import Item


def fetch_hf_papers(limit: int = 10) -> list[Item]:
    """HuggingFace Daily Papers：社区投票筛出的有影响力论文。"""
    try:
        r = requests.get("https://huggingface.co/api/daily_papers", timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[warn] HF Daily Papers 抓取失败: {e}")
        return []
    items = []
    for p in data[:limit]:
        paper = p.get("paper", p)
        pid = paper.get("id", "")
        items.append(Item(
            id=pid,
            title=(paper.get("title") or "").strip(),
            url=f"https://huggingface.co/papers/{pid}",
            source="HF Daily Papers",
            published=(paper.get("publishedAt") or "")[:10],
            summary=(paper.get("summary") or "")[:1200],
            extra={"upvotes": p.get("upvotes") or paper.get("upvotes") or 0},
        ))
    print(f"[ok] HF Daily Papers: {len(items)} 条")
    return items
