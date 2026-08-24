import os
from dotenv import load_dotenv

load_dotenv()

# ---------- LLM（OpenAI 兼容协议：DeepSeek / Kimi / 通义 / Gemini 均可） ----------
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ---------- ClawBot 微信推送（WeClawBot-API 协议） ----------
CLAWBOT_API_URL = os.getenv("CLAWBOT_API_URL", "").rstrip("/")   # 如 http://127.0.0.1:26322
CLAWBOT_BOT_ID = os.getenv("CLAWBOT_BOT_ID", "")                 # 如 xxx@im.bot
CLAWBOT_TOKEN = os.getenv("CLAWBOT_TOKEN", "")
PUSH_ENABLED = os.getenv("PUSH_ENABLED", "true").lower() == "true"

# ---------- 可选：自建 RSSHub（用于牛客等无官方 RSS 的源，不配置则自动跳过） ----------
RSSHUB_BASE = os.getenv("RSSHUB_BASE", "").rstrip("/")

# ---------- B站（情感UP主任务） ----------
BILI_SESSDATA = os.getenv("BILI_SESSDATA", "")   # 可选，提高视频下载成功率
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")  # 服务器 CPU 建议 small/base，有 GPU 可 medium

# ---------- 目录 ----------
WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
REPORT_DIR = os.path.join(WORK_DIR, "reports")
STATE_DIR = os.path.join(WORK_DIR, "state")
UP_LIST_FILE = os.path.join(WORK_DIR, "up_list.txt")

for _d in (WORK_DIR, REPORT_DIR, STATE_DIR):
    os.makedirs(_d, exist_ok=True)
