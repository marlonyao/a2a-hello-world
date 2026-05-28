"""
Agent 1: Greeter Agent — 打招呼专家
端口: 10001
"""
import uvicorn
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
)
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, TaskState


class GreeterAgent:
    SYSTEM_PROMPT = "你是打招呼专家 Greeter Agent。热情友好地回复每条消息，可以聊天、介绍自己、回答简单问题。回复要简洁有趣。"

    async def invoke(self, text: str) -> str:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from llm_client import chat
        return await chat(self.SYSTEM_PROMPT, text)


class GreeterExecutor(AgentExecutor):
    def __init__(self):
        self.agent = GreeterAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue=event_queue, task_id=task.id, context_id=task.context_id)
        await updater.update_status(state=TaskState.TASK_STATE_WORKING)

        text = get_message_text(context.message) or ""
        result = await self.agent.invoke(text)

        await updater.add_artifact(parts=[new_text_part(text=result, media_type="text/plain")])
        await updater.update_status(state=TaskState.TASK_STATE_COMPLETED)

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise NotImplementedError("cancel not supported")


card = AgentCard(
    name="Greeter Agent",
    description="打招呼专家，热情地回复每一条消息",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False, push_notifications=False),
    supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url="http://127.0.0.1:10001")],
    skills=[AgentSkill(
        id="greet", name="打招呼", description="热情地回复消息",
        input_modes=["text/plain"], output_modes=["text/plain"],
        tags=["greet"], examples=["你好", "hello"],
    )],
)

handler = DefaultRequestHandler(
    agent_executor=GreeterExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=card,
)

routes = []
routes.extend(create_agent_card_routes(card))
routes.extend(create_jsonrpc_routes(handler, "/"))
app = Starlette(routes=routes)

if __name__ == "__main__":
    print("🟢 Greeter Agent 启动在 :10001")
    uvicorn.run(app, host="127.0.0.1", port=10001)