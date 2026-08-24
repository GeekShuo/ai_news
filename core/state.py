from __future__ import annotations

import json
import os
import time

from config import STATE_DIR


class State:
    """跨日去重状态：记录已处理过的条目 id，默认保留 14 天。"""

    def __init__(self, task: str, keep_days: int = 14):
        self.path = os.path.join(STATE_DIR, f"{task}.json")
        self.keep = keep_days * 86400
        self.data: dict = {}
        if os.path.exists(self.path):
            try:
                self.data = json.load(open(self.path, encoding="utf-8"))
            except Exception:
                self.data = {}

    def seen(self, _id: str) -> bool:
        return _id in self.data

    def mark(self, _id: str, info: dict | None = None):
        self.data[_id] = {"ts": time.time(), **(info or {})}

    def filter_new(self, items):
        return [it for it in items if not self.seen(it.id)]

    def save(self):
        now = time.time()
        self.data = {k: v for k, v in self.data.items()
                     if now - v.get("ts", now) < self.keep}
        json.dump(self.data, open(self.path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
