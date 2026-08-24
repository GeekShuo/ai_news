from __future__ import annotations

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def has_llm() -> bool:
    return bool(LLM_API_KEY)


def complete(prompt: str, system: str | None = None) -> str:
    """统一的文本生成接口（OpenAI 兼容协议）。"""
    if not LLM_API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，请检查 .env")
    from openai import OpenAI
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=0.3)
    return resp.choices[0].message.content
