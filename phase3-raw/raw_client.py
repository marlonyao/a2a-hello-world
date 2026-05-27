"""
原生 A2A Client — 不依赖 a2a-sdk，仅用 Python 标准库 + httpx

完全符合 A2A v1.0 JSON-RPC 协议，可以和 SDK Server 互通。
"""

import json
import uuid
import asyncio
import httpx


async def discover_agent(base_url: str) -> dict:
    """第 1 步：发现 Agent — 读取 Agent Card"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{base_url}/.well-known/agent-card.json")
        resp.raise_for_status()
        card = resp.json()
        print(f"📋 发现 Agent: {card['name']}")
        print(f"   描述: {card.get('description', '')}")
        print(f"   版本: {card.get('version', '')}")
        print(f"   技能: {[s['name'] for s in card.get('skills', [])]}")
        return card


async def send_message(base_url: str, text: str) -> dict:
    """第 2 步：发送消息 — 构造 JSON-RPC 请求"""
    request_body = {
        "jsonrpc": "2.0",
        "method": "SendMessage",
        "id": 1,
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "ROLE_USER",
                "parts": [{"text": text}],
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "A2A-Version": "1.0",           # ← 关键！A2A v1.0 必须带这个 Header
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/", json=request_body, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    # 处理 JSON-RPC 错误
    if "error" in result:
        raise Exception(f"JSON-RPC Error: {result['error']}")

    return result


def extract_artifact_text(response: dict) -> str:
    """从响应中提取 Artifact 文本"""
    task = response.get("result", {}).get("task", {})
    artifacts = task.get("artifacts", [])
    texts = []
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if "text" in part:
                texts.append(part["text"])
    return "\n".join(texts)


async def main():
    print("=" * 50)
    print("📡 原生 A2A Client (无 SDK)")
    print("=" * 50)

    # 测试目标：可以是 SDK Server 或原生 Server
    targets = [
        ("SDK Greeter Agent", "http://127.0.0.1:10001"),
        ("原生 Agent", "http://127.0.0.1:10010"),
    ]

    test_message = "你好，我是原生 Client 发来的消息！"

    for name, url in targets:
        print(f"\n{'─' * 40}")
        print(f"🎯 测试目标: {name} ({url})")

        try:
            # 发现
            card = await discover_agent(url)

            # 发消息
            print(f"\n👤 发送: {test_message}")
            resp = await send_message(url, test_message)

            # 提取回复
            reply = extract_artifact_text(resp)
            print(f"🤖 回复: {reply}")

        except Exception as e:
            print(f"❌ 失败: {e}")

    print(f"\n{'=' * 50}")
    print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())