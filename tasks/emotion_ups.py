"""④ 情感 UP 主日报：监控清单内 UP 主的新视频，转写口播并总结要点。"""
import datetime

import llm
from config import UP_LIST_FILE
from core.models import Item
from core.report import deliver
from core.state import State
from sources.bilibili import (get_recent_videos, get_recent_videos_rsshub,
                              resolve_uid)


def read_up_list() -> list[str]:
    """data/up_list.txt：每行一个 UP 主昵称；也支持 `uid:123456` 直接指定（跳过搜索）。

    # 开头为注释。B站搜索接口风控严格，昵称解析失败时建议改用 uid 形式。
    """
    try:
        lines = open(UP_LIST_FILE, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        print(f"[warn] 未找到 {UP_LIST_FILE}")
        return []
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


VIDEO_PROMPT = """下面是情感博主「{up}」最新视频《{title}》的口播文字稿（可能有少量识别错误）。
请输出 Markdown：
## 《{title}》—— {up}
- 链接：{url} | 发布：{published} | 时长：{duration}
- **核心观点**：3-5 条，分条列出
- **金句**：原文引用 1-3 句（有代表性的）
- **可执行建议**：普通人能照着做的 2-3 条

文字稿：
{transcript}"""


def summarize_video(up_name: str, v: Item) -> str:
    """单个视频：下载 -> 转写 -> LLM 总结；失败则降级为简介。"""
    from media.transcribe import download_audio, transcribe
    head = f"## 《{v.title}》—— {up_name}\n- 链接：{v.url} | 发布：{v.published} | 时长：{v.extra.get('duration', '')}\n"
    try:
        audio = download_audio(v.id)
        if not audio:
            raise RuntimeError("音频下载失败")
        text = transcribe(audio)
    except Exception as e:
        print(f"[warn] 转写失败 {v.id}: {e}，降级为简介")
        return head + f"- **转写失败，仅提供简介**：{v.summary[:300] or '（无简介）'}\n"
    return llm.complete(VIDEO_PROMPT.format(
        up=up_name, title=v.title, url=v.url, published=v.published,
        duration=v.extra.get("duration", ""), transcript=text[:12000])) + "\n"


def run(dry_run: bool = False, no_push: bool = False, days: float = 3.0):
    date = datetime.date.today().isoformat()
    ups = read_up_list()
    print(f"[ok] UP主清单: {ups}")
    uid_state = State("up_uid_cache", keep_days=365)
    state = State("emotion_ups", keep_days=30)

    # 1. 收集所有 UP 主的新视频
    new_videos: list[tuple[str, Item]] = []
    import time as _time
    cutoff = _time.time() - days * 86400
    for name in ups:
        uid = None
        if name.lower().startswith("uid:"):
            try:
                uid = int(name.split(":", 1)[1].strip())
            except ValueError:
                print(f"[warn] uid 格式错误: {name}")
        else:
            cached = uid_state.data.get(name, {})
            uid = cached.get("uid")
            if not uid:
                uid, uname = resolve_uid(name)
                if uid:
                    uid_state.mark(name, {"uid": uid, "uname": uname})
        if not uid:
            continue
        videos = get_recent_videos(uid, limit=5)
        if not videos:  # 接口被风控时走 RSSHub 兜底
            videos = get_recent_videos_rsshub(uid, limit=5)
        print(f"[ok] {name}: 最近 {len(videos)} 个视频")
        for v in videos:
            if state.seen(v.id):
                continue
            ts = _time.mktime(_time.strptime(v.published, "%Y-%m-%d")) if v.published else 0
            if ts < cutoff:
                continue
            new_videos.append((name, v))
    uid_state.save()
    print(f"[ok] 新视频 {len(new_videos)} 个")

    if dry_run:
        for name, v in new_videos:
            print(f"- [{name}] {v.title} {v.url} ({v.published})")
        return

    # 2. 转写 + 总结
    sections = []
    for name, v in new_videos:
        print(f"[..] 处理 {name}: {v.title}")
        sections.append(summarize_video(name, v))
        state.mark(v.id, {"title": v.title, "up": name})
    state.save()

    # 3. 汇总报告
    if not sections:
        md = f"# 情感 UP 主日报 {date}\n\n清单内 UP 主今日无更新。"
    else:
        md = (f"# 情感 UP 主日报 {date}\n\n"
              f"今日 {len(sections)} 个新视频：\n\n" + "\n---\n\n".join(sections))
    deliver("emotion_ups", md, push=not no_push)
