"""② AI 科研日报：有影响力的新论文 + 创新点/影响解读。"""
import datetime
import json

import llm
from core.models import Item
from core.report import deliver
from core.state import State
from sources.arxiv_src import fetch_arxiv
from sources.hf_papers import fetch_hf_papers


def collect() -> list[Item]:
    items = fetch_hf_papers(limit=10)          # 社区精选（影响力）
    items += fetch_arxiv(days=4.0, limit=60)   # 最新投稿（时效性，覆盖周末空档）
    return items


PROMPT = """你是 AI 研究方向的科研助手。下面是今天的候选论文（JSON 列表：HF Daily Papers 社区精选 + arXiv 最新投稿，含 title/authors/summary/upvotes）。
读者：互联网大厂算法岗实习生，想了解最近有什么有影响力的工作。

请挑出最有影响力的 5-8 篇（优先 HF Daily Papers 中高票数的，arXiv 里只选真正有分量的），输出 Markdown：
# AI 科研日报 {date}
对每篇论文：
## 中文标题（原文标题）
- 链接 | 作者前几位 | 来源
- **一句话**：这篇论文讲了什么
- **创新点**：方法上最关键的新东西，1-2 句
- **影响**：对工业界或学术界的意义，1 句

最后加一节：
## 趋势观察
这批论文反映出当前的研究热点是什么，3-5 句。

要求：中文输出；看不懂的论文不要硬写；不要编造链接。

论文列表：
{items}"""


def build(items: list[Item]) -> str:
    date = datetime.date.today().isoformat()
    if not items:
        return f"# AI 科研日报 {date}\n\n今日无新增论文。"
    hf = [it for it in items if it.source == "HF Daily Papers"]
    ax = [it for it in items if it.source == "arXiv"][:30]
    payload = [{"title": it.title, "authors": it.extra.get("authors", ""),
                "source": it.source, "url": it.url, "published": it.published,
                "upvotes": it.extra.get("upvotes", 0), "summary": it.summary[:600]}
               for it in hf + ax]
    return llm.complete(PROMPT.format(date=date,
                                      items=json.dumps(payload, ensure_ascii=False)))


def run(dry_run: bool = False, no_push: bool = False):
    items = collect()
    state = State("ai_research")
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
    deliver("ai_research", md, push=not no_push)
