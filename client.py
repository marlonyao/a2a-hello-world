"""
A2A Client 测试脚本

演示如何作为 Client 与 A2A Agent 通信：
1. 发现 Agent（读取 Agent Card）
2. 发送消息
3. 接收响应
"""

import asyncio
import httpx

from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import new_text_message, get_stream_response_text
from a2a.types import Role, SendMessageRequest, TaskState


AGENT_URL = "http://127.0.0.1:9999"


async def main():
    print("=" * 50)
    print("📡 A2A Client 启动")
    print("=" * 50)

    # 第 1 步：发现 Agent — 读取 Agent Card
    print("\n🔍 正在发现 Agent...")
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=AGENT_URL,
        )
        card = await resolver.get_agent_card()

    print(f"   名称: {card.name}")
    print(f"   描述: {card.description}")
    print(f"   版本: {card.version}")
    print(f"   技能: {[s.name for s in card.skills]}")

    # 第 2 步：创建 A2A Client
    config = ClientConfig(streaming=False)
    client = await create_client(agent=card, client_config=config)

    # 第 3 步：发送消息
    test_messages = [
        "你好，我是 A2A 的学习者！",
        "帮我解释一下 A2A 协议",
    ]

    for msg_text in test_messages:
        print(f"\n{'─' * 40}")
        print(f"👤 发送: {msg_text}")

        message = new_text_message(msg_text, role=Role.ROLE_USER)
        request = SendMessageRequest(message=message)

        # 接收响应
        response_text = ""
        async for chunk in client.send_message(request):
            if hasattr(chunk, "status") and chunk.status:
                state = chunk.status.state
                state_name = TaskState(state).name if isinstance(state, int) else state
                print(f"   状态: {state_name}")

            # 尝试提取文本
            text = get_stream_response_text(chunk)
            if text:
                response_text = text

        print(f"🤖 回复: {response_text}")

    # 第 4 步：清理
    await client.close()
    print(f"\n{'=' * 50}")
    print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
