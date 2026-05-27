"""
Agent 2: Translator Agent — 翻译专家
端口: 10002
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


class TranslatorAgent:
    async def invoke(self, text: str) -> str:
        # 简单的模拟翻译（后续可接入智谱 GLM）
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
        if has_chinese:
            translated = f"[Simulated EN Translation] {text}"
            direction = "中 → 英"
        else:
            translated = f"[模拟中文翻译] {text}"
            direction = "英 → 中"

        return (
            f"🌐 我是 Translator Agent（翻译专家）。\n"
            f"翻译方向：{direction}\n"
            f"原文：{text}\n"
            f"译文：{translated}"
        )


class TranslatorExecutor(AgentExecutor):
    def __init__(self):
        self.agent = TranslatorAgent()

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
    name="Translator Agent",
    description="翻译专家，支持中英文互译",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False, push_notifications=False),
    supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url="http://127.0.0.1:10002")],
    skills=[AgentSkill(
        id="translate", name="翻译", description="中英文翻译",
        input_modes=["text/plain"], output_modes=["text/plain"],
        tags=["translate"], examples=["翻译一下 hello"],
    )],
)

handler = DefaultRequestHandler(
    agent_executor=TranslatorExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=card,
)

routes = []
routes.extend(create_agent_card_routes(card))
routes.extend(create_jsonrpc_routes(handler, "/"))
app = Starlette(routes=routes)

if __name__ == "__main__":
    print("🔵 Translator Agent 启动在 :10002")
    uvicorn.run(app, host="127.0.0.1", port=10002)