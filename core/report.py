import datetime
import os

from config import REPORT_DIR
from push.clawbot import push_text


def deliver(task: str, md: str, push: bool = True) -> str:
    """报告落盘 + 推送。"""
    date = datetime.date.today().isoformat()
    path = os.path.join(REPORT_DIR, f"{task}_{date}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[ok] 报告已保存: {path}")
    if push:
        push_text(md)
    return path
