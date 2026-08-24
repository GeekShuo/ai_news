"""B站公开接口：UP主解析 / UP主近期视频 / 视频搜索（免登录，WBI 签名）。"""
from __future__ import annotations

import hashlib
import re
import time
import urllib.parse

import requests

from config import BILI_SESSDATA
from core.models import Item

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

_MIXIN_TABLE = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
                27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
                37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
                22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]

_session = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Referer": "https://www.bilibili.com"})
        if BILI_SESSDATA:
            s.cookies.set("SESSDATA", BILI_SESSDATA, domain=".bilibili.com")
        _session = s
    return _session


def _wbi_keys(sess) -> tuple[str, str]:
    r = sess.get("https://api.bilibili.com/x/web-interface/nav", timeout=15).json()
    wbi = r["data"]["wbi_img"]
    img = wbi["img_url"].rsplit("/", 1)[1].split(".")[0]
    sub = wbi["sub_url"].rsplit("/", 1)[1].split(".")[0]
    return img, sub


def _sign(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_src = img_key + sub_key
    mixin = "".join(mixin_src[i] for i in _MIXIN_TABLE)[:32]
    p = dict(params)
    p["wts"] = int(time.time())
    p = {k: "".join(c for c in str(v) if c not in "!'()*")
         for k, v in sorted(p.items())}
    query = urllib.parse.urlencode(p)
    p["w_rid"] = hashlib.md5((query + mixin).encode()).hexdigest()
    return p


def resolve_uid(name: str) -> tuple[int | None, str | None]:
    """昵称 -> (uid, 官方昵称)。找不到返回 (None, None)。"""
    sess = get_session()
    try:
        r = sess.get("https://api.bilibili.com/x/web-interface/search/type",
                     params={"search_type": "bili_user", "keyword": name},
                     timeout=15).json()
    except Exception as e:
        print(f"[warn] UP主搜索失败 {name}: {e}")
        return None, None
    for u in (r.get("data") or {}).get("result") or []:
        uname = re.sub(r"<[^>]+>", "", u.get("uname", ""))
        return u.get("mid"), uname
    print(f"[warn] 未找到 UP主: {name}")
    return None, None


def get_recent_videos(uid: int, limit: int = 5) -> list[Item]:
    """UP 主近期视频（空间接口，需 WBI 签名）。"""
    sess = get_session()
    try:
        img, sub = _wbi_keys(sess)
        params = _sign({"mid": uid, "ps": limit, "pn": 1, "order": "pubdate"},
                       img, sub)
        r = sess.get("https://api.bilibili.com/x/space/wbi/arc/search",
                     params=params, timeout=15).json()
    except Exception as e:
        print(f"[warn] 获取 UP主视频失败 mid={uid}: {e}")
        return []
    if r.get("code") != 0:
        print(f"[warn] B站接口返回 code={r.get('code')} mid={uid}: {r.get('message')}")
        return []
    vlist = ((r.get("data") or {}).get("list") or {}).get("vlist") or []
    out = []
    for v in vlist[:limit]:
        out.append(Item(
            id=v["bvid"],
            title=v.get("title", ""),
            url=f"https://www.bilibili.com/video/{v['bvid']}",
            source="bilibili",
            published=time.strftime("%Y-%m-%d", time.localtime(v.get("created", 0))),
            summary=(v.get("description") or "")[:500],
            extra={"duration": v.get("length", ""), "mid": uid},
        ))
    return out


def get_recent_videos_rsshub(uid: int, limit: int = 5) -> list[Item]:
    """兜底：通过自建 RSSHub 获取 UP 主近期视频（B站接口风控严格时用）。"""
    from config import RSSHUB_BASE
    if not RSSHUB_BASE:
        return []
    from sources.rss import fetch_feed
    return fetch_feed(f"B站·uid{uid}", f"{RSSHUB_BASE}/bilibili/user/video/{uid}",
                      hours=24 * 30, limit=limit)


def search_videos(keyword: str, limit: int = 15, days: float = 3.0) -> list[Item]:
    """B站视频搜索（按发布时间倒序），用于求职/面经类内容。"""
    sess = get_session()
    try:
        r = sess.get("https://api.bilibili.com/x/web-interface/search/type",
                     params={"search_type": "video", "keyword": keyword,
                             "order": "pubdate"}, timeout=15).json()
    except Exception as e:
        print(f"[warn] B站搜索失败 {keyword}: {e}")
        return []
    cutoff = time.time() - days * 86400
    out = []
    for v in ((r.get("data") or {}).get("result") or [])[:limit]:
        if v.get("pubdate", 0) < cutoff:
            continue
        title = re.sub(r"<[^>]+>", "", v.get("title", ""))
        out.append(Item(
            id=v.get("bvid", ""),
            title=title,
            url=f"https://www.bilibili.com/video/{v.get('bvid', '')}",
            source=f"B站·{v.get('author', '')}",
            published=time.strftime("%Y-%m-%d", time.localtime(v.get("pubdate", 0))),
            summary=(v.get("description") or "")[:300],
        ))
    return out
