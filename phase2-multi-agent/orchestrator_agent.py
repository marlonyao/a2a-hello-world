"""
Agent 3: Orchestrator Agent — 调度员
端口: 10003

这是核心！它作为 A2A Client 调用 Greeter 和 Translator，
同时作为 A2A Server 接受用户的请求。

数据流：用户 → Orchestrator → Greeter / Translator → Orchestrator → 用户
"""
import uvicorn, asyncio
import httpx
from starlette.applications import Starlette
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.helpers import (
    get_message_text, new_task_from_user_message,
    new_text_message, new_text_part,
    get_stream_response_text,
)
from a2a.types import (
    AgentCapabilities, AgentCard, AgentInterface, AgentSkill, TaskState,
    Role, SendMessageRequest,
)
from a2a.client import A2ACardResolver, ClientConfig, create_client


# 要调用的下游 Agent 地址
AGENT_URLS = {
    "greeter": "http://127.0.0.1:10001",
    "translator": "http://127.0.0.1:10002",
}


class OrchestratorAgent:
    """调度员 Agent：根据用户意图，决定调用哪个下游 Agent"""

    def _parse_intent(self, text: str) -> list[str]:
        """简单意图识别（后续可接入 LLM）"""
        agents = []
        if any(kw in text for kw in ["翻译", "translate", "英文", "中文", "英语"]):
            agents.append("translator")
        if not agents:
            agents.append("greeter")
        return agents

    async def invoke(self, text: str) -> str:
        intent_agents = self._parse_intent(text)
        results = []

        async with httpx.AsyncClient() as httpx_client:
            for agent_name in intent_agents:
                agent_url = AGENT_URLS[agent_name]

                # ① 发现 Agent：读取 Agent Card
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
                card = await resolver.get_agent_card()

                # ② 创建 A2A Client
                config = ClientConfig(streaming=False)
                client = await create_client(agent=card, client_config=config)

                # ③ 构造消息并发送
                message = new_text_message(text, role=Role.ROLE_USER)
                request = SendMessageRequest(message=message)

                # ④ 接收响应
                response_text = ""
                async for chunk in client.send_message(request):
                    chunk_text = get_stream_response_text(chunk)
                    if chunk_text:
                        response_text = chunk_text

                await client.close()
                results.append(f"【{card.name} 的回复】\n{response_text}")

        header = f"📡 Orchestrator 收到你的请求：「{text}」\n"
        header += f"🔍 分析意图后，调用了：{', '.join(intent_agents)}\n"
        header += "─" * 40
        return header + "\n\n" + "\n\n".join(results)


class OrchestratorExecutor(AgentExecutor):
    def __init__(self):
        self.agent = OrchestratorAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue=event_queue, task_id=task.id, context_id=task.context_id)
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("正在分析意图并调度 Agent..."),
        )

        text = get_message_text(context.message) or ""
        result = await self.agent.invoke(text)

        await updater.add_artifact(parts=[new_text_part(text=result, media_type="text/plain")])
        await updater.update_status(state=TaskState.TASK_STATE_COMPLETED)

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise NotImplementedError("cancel not supported")


card = AgentCard(
    name="Orchestrator Agent",
    description="调度员 Agent，根据用户意图分发给 Greeter 或 Translator",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False, push_notifications=False),
    supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url="http://127.0.0.1:10003")],
    skills=[AgentSkill(
        id="orchestrate", name="智能调度", description="根据意图调用合适的 Agent",
        input_modes=["text/plain"], output_modes=["text/plain"],
        tags=["orchestrator", "router"], examples=["你好", "帮我翻译 hello"],
    )],
)

handler = DefaultRequestHandler(
    agent_executor=OrchestratorExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=card,
)

routes = []
routes.extend(create_agent_card_routes(card))
routes.extend(create_jsonrpc_routes(handler, "/"))
app = Starlette(routes=routes)

if __name__ == "__main__":
    print("🟣 Orchestrator Agent 启动在 :10003")
    uvicorn.run(app, host="127.0.0.1", port=10003)