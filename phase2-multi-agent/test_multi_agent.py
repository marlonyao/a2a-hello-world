"""
测试脚本：启动三个 Agent，然后通过 Orchestrator 测试多 Agent 协作
"""
import asyncio, subprocess, time, sys, httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import new_text_message, get_stream_response_text
from a2a.types import Role, SendMessageRequest

ORCHESTRATOR_URL = "http://127.0.0.1:10003"


def start_agents():
    """后台启动三个 Agent"""
    procs = []
    for script in ["greeter_agent.py", "translator_agent.py", "orchestrator_agent.py"]:
        p = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        procs.append(p)
        print(f"  启动 {script} (PID={p.pid})")
    print("等待 Agent 就绪...")
    time.sleep(3)
    return procs


def stop_agents(procs):
    for p in procs:
        p.terminate()
    print("所有 Agent 已停止")


async def test_orchestrator():
    print("\n" + "=" * 50)
    print("📡 测试多 Agent 协作")
    print("=" * 50)

    async with httpx.AsyncClient() as httpx_client:
        # 发现 Orchestrator
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=ORCHESTRATOR_URL)
        card = await resolver.get_agent_card()
        print(f"\n发现 Agent: {card.name}")
        print(f"技能: {[s.name for s in card.skills]}")

        # 创建 Client
        config = ClientConfig(streaming=False)
        client = await create_client(agent=card, client_config=config)

        # 测试场景 1：打招呼 → 应该路由到 Greeter
        print(f"\n{'─' * 40}")
        print("测试 1：打招呼场景（预期路由到 Greeter）")
        msg = new_text_message("你好呀！", role=Role.ROLE_USER)
        req = SendMessageRequest(message=msg)
        async for chunk in client.send_message(req):
            text = get_stream_response_text(chunk)
            if text:
                print(f"🤖 回复:\n{text}")

        # 测试场景 2：翻译 → 应该路由到 Translator
        print(f"\n{'─' * 40}")
        print("测试 2：翻译场景（预期路由到 Translator）")
        msg = new_text_message("帮我翻译一下 Hello World", role=Role.ROLE_USER)
        req = SendMessageRequest(message=msg)
        async for chunk in client.send_message(req):
            text = get_stream_response_text(chunk)
            if text:
                print(f"🤖 回复:\n{text}")

        await client.close()

    print(f"\n{'=' * 50}")
    print("✅ 多 Agent 协作测试完成！")


if __name__ == "__main__":
    procs = start_agents()
    try:
        asyncio.run(test_orchestrator())
    finally:
        stop_agents(procs)