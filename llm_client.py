"""
公共 LLM 客户端 — 调用 DeepSeek V4 Flash

所有 Agent 共享，通过 OpenAI 兼容接口调用。
"""

import os
from openai import AsyncOpenAI

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "REDACTED")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """获取或创建 AsyncOpenAI 单例"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


async def chat(system_prompt: str, user_message: str) -> str:
    """
    发送一条消息并获取回复。

    Args:
        system_prompt: 系统提示词，定义 Agent 角色
        user_message: 用户输入

    Returns:
        LLM 的回复文本
    """
    client = get_client()
    response = await client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""
