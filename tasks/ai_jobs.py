"""③ 求职情报日报：校招/实习开放动态、面经与求职建议、大厂内幕讨论。"""
import datetime
import json

import llm
from config import BILI_SESSDATA, RSSHUB_BASE
from core.models import Item
from core.report import deliver
from core.state import State
from sources.bilibili import search_videos
from sources.rss import fetch_feed

_BILI_KEYWORDS = ["校招", "秋招 面经", "大厂 实习", "算法岗 面试"]


def collect() -> list[Item]:
    items: list[Item] = []
    items += fetch_feed("V2EX·求职", "https://www.v2ex.com/feed/cv.xml", hours=72)
    if RSSHUB_BASE:
        items += fetch_feed("知乎热榜", f"{RSSHUB_BASE}/zhihu/hotlist", hours=36)
        items += fetch_feed("牛客讨论区", f"{RSSHUB_BASE}/nowcoder/discuss", hours=72)
    if BILI_SESSDATA:
        # B站搜索接口风控较严，需登录 Cookie（.env 配置 BILI_SESSDATA）
        for kw in _BILI_KEYWORDS:
            got = search_videos(kw, limit=12, days=3.0)
            print(f"[ok] B站搜索[{kw}]: {len(got)} 条")
            items += got
    else:
        print("[skip] 未配置 BILI_SESSDATA，跳过 B站面经搜索")
    return items


PROMPT = """你是求职情报编辑。下面是过去两三天抓取的求职相关帖子/视频/热榜（JSON 列表）。
读者：互联网大厂算法岗实习生，关注校招与实习机会、面试经验、大厂内幕。

请输出 Markdown 日报：
# 求职情报日报 {date}
## 校招/实习开放动态
有新公司开放校招、实习、补录的信息；没有明确新动态就写"今日无明确新开招聘信息"。
## 面经与求职建议
有价值的面试经验、简历建议、准备路线，提炼要点（不要只列标题），附链接。
## 大厂内幕与讨论
组织架构、hc 变化、裁员/扩招、氛围待遇等讨论，标注"可信度存疑，仅供参考"，附链接。

要求：只保留与互联网求职（尤其算法/技术岗）相关的内容；娱乐八卦直接丢弃；中文输出；不要编造链接。

条目列表：
{items}"""


def build(items: list[Item]) -> str:
    date = datetime.date.today().isoformat()
    if not items:
        return f"# 求职情报日报 {date}\n\n今日无新增内容。"
    payload = [{"title": it.title, "source": it.source, "url": it.url,
                "published": it.published, "summary": it.summary} for it in items]
    return llm.complete(PROMPT.format(date=date,
                                      items=json.dumps(payload, ensure_ascii=False)))


def run(dry_run: bool = False, no_push: bool = False):
    items = collect()
    state = State("ai_jobs")
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
    deliver("ai_jobs", md, push=not no_push)
