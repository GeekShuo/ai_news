from dataclasses import dataclass, field


@dataclass
class Item:
    """一条信息（新闻/论文/帖子/视频）。"""
    id: str                      # 唯一标识（url / bvid / arxiv id）
    title: str
    url: str
    source: str                  # 来源名，如 机器之心 / arXiv / B站·某UP
    published: str = ""          # 日期 YYYY-MM-DD
    summary: str = ""            # 摘要/正文片段
    extra: dict = field(default_factory=dict)
