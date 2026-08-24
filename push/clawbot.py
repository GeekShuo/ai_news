"""ClawBot 微信推送（兼容 WeClawBot-API 协议）。

POST {CLAWBOT_API_URL}/bots/{CLAWBOT_BOT_ID}/messages
Header: Authorization: Bearer {CLAWBOT_TOKEN}
Body:   {"text": "..."}
"""
import time

import requests

from config import CLAWBOT_API_URL, CLAWBOT_BOT_ID, CLAWBOT_TOKEN, PUSH_ENABLED

CHUNK = 1800  # 微信单条消息长度有限，长报告分段推送


def _chunks(text: str, size: int):
    """按段落切块，尽量不截断句子。"""
    buf = ""
    for para in text.split("\n"):
        if len(buf) + len(para) + 1 > size and buf:
            yield buf
            buf = ""
        if len(para) > size:  # 超长单段硬切
            if buf:
                yield buf
                buf = ""
            for i in range(0, len(para), size):
                yield para[i:i + size]
            continue
        buf += para + "\n"
    if buf.strip():
        yield buf


def _send(text: str) -> bool:
    url = f"{CLAWBOT_API_URL}/bots/{CLAWBOT_BOT_ID}/messages"
    try:
        r = requests.post(url, json={"text": text},
                          headers={"Authorization": f"Bearer {CLAWBOT_TOKEN}"},
                          timeout=15)
        if r.status_code != 200:
            print(f"[err] ClawBot 返回 {r.status_code}: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"[err] ClawBot 推送失败: {e}")
        return False


def push_text(text: str) -> bool:
    if not PUSH_ENABLED:
        print("[skip] PUSH_ENABLED=false，跳过推送")
        return False
    if not (CLAWBOT_API_URL and CLAWBOT_BOT_ID and CLAWBOT_TOKEN):
        print("[warn] 未配置 ClawBot（CLAWBOT_API_URL/BOT_ID/TOKEN），跳过推送")
        return False
    ok = True
    for part in _chunks(text, CHUNK):
        ok = _send(part) and ok
        time.sleep(1)
    if ok:
        print("[ok] 已推送到微信")
    return ok
