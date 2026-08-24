"""音频下载 + 本地 Whisper 转写（复用 video_kb 的思路，仅 emotion_ups 任务使用）。"""
from __future__ import annotations

import glob
import os

from config import BILI_SESSDATA, WHISPER_MODEL, WORK_DIR
from sources.bilibili import UA

AUDIO_DIR = os.path.join(WORK_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


def download_audio(bvid: str) -> str | None:
    """yt-dlp 下载 B站视频音频（不转码，无需 ffmpeg）。"""
    existing = [f for f in glob.glob(os.path.join(AUDIO_DIR, f"{bvid}.*"))
                if not f.endswith(".part")]
    if existing:
        return existing[0]
    import yt_dlp
    headers = {"User-Agent": UA, "Referer": "https://www.bilibili.com"}
    if BILI_SESSDATA:
        headers["Cookie"] = f"SESSDATA={BILI_SESSDATA}"
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(AUDIO_DIR, f"{bvid}.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "http_headers": headers,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.bilibili.com/video/{bvid}"])
    files = [f for f in glob.glob(os.path.join(AUDIO_DIR, f"{bvid}.*"))
             if not f.endswith(".part")]
    return files[0] if files else None


_model = None


def transcribe(audio_path: str) -> str:
    """faster-whisper CPU 转写中文口播。"""
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(audio_path, language="zh", vad_filter=True)
    return "\n".join(s.text for s in segments)
