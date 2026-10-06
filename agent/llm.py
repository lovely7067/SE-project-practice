"""LLM 调用封装：统一的客户端管理 + 带重试机制的对话接口。"""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

MAX_RETRIES = 3   # 最大重试次数
RETRY_BASE_DELAY = 2  # 指数退避基础等待秒数

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """懒加载并复用 OpenAI 客户端（DeepSeek 兼容 OpenAI 协议）。"""
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError(
                "未检测到 LLM_API_KEY：请复制 .env.example 为 .env 并填入你的 API Key"
            )
        _client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return _client


def chat(messages: list, tools: list | None = None):
    """调用 LLM，失败时指数退避重试（网络抖动 / 限流 / 超时）。

    返回模型输出的 message 对象（含 content 与可能的 tool_calls）。
    """
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = get_client().chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools or None,
            )
            return resp.choices[0].message
        except Exception as e:  # 网络错误 / 429限流 / 超时等
            last_err = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_DELAY ** attempt
                print(f"[重试 {attempt}/{MAX_RETRIES}] LLM 调用失败：{e}，{wait} 秒后重试...")
                time.sleep(wait)
    raise RuntimeError(f"LLM 调用连续 {MAX_RETRIES} 次失败：{last_err}")
