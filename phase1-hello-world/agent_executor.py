"""
A2A Agent Executor — Agent 的核心逻辑

你需要实现 AgentExecutor 接口的两个方法：
- execute(): 处理用户发来的消息
- cancel(): 取消正在执行的任务

这是你写 Agent "大脑" 的地方
"""

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
    new_text_artifact,
)
from a2a.types import TaskState


# ── 你的 Agent 业务逻辑 ─────────────────────────────
class MyAgent:
    """你的 Agent 核心逻辑，这里可以接入 LLM、工具调用等"""

    async def invoke(self, user_message: str) -> str:
        # 目前先做一个简单的回声 + 解释，后续可以接入智谱 GLM
        return (
            f"👋 你好！我是你的第一个 A2A Agent。\n"
            f"你发送的消息是：「{user_message}」\n"
            f"我已经成功收到了！这是 Phase 2 的 Hello World 响应。"
        )


# ── A2A 框架对接层 ─────────────────────────────────
class MyAgentExecutor(AgentExecutor):
    """
    AgentExecutor 是 A2A SDK 要求你实现的接口。
    它负责把框架的请求翻译成你的 Agent 能理解的调用，
    然后把结果翻译回 A2A 协议格式。
    """

    def __init__(self):
        self.agent = MyAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        核心执行流程（5 步）：
        1. 获取或创建 Task
        2. 更新状态为 WORKING
        3. 调用你的 Agent 逻辑
        4. 把结果作为 Artifact 添加
        5. 更新状态为 COMPLETED
        """

        # 第 1 步：获取已有 Task，或从用户消息创建新 Task
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        # 创建 TaskUpdater，用于更新 Task 状态和添加产物
        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        # 第 2 步：标记为"处理中"
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("正在处理你的请求..."),
        )

        # 第 3 步：调用 Agent 获取结果
        user_text = get_message_text(context.message)
        if user_text:
            result = await self.agent.invoke(user_text)
        else:
            result = "没有收到文本内容，请发送文本消息。"

        # 第 4 步：把结果添加为 Artifact（Task 的交付物）
        await updater.add_artifact(
            parts=[new_text_part(text=result, media_type="text/plain")]
        )

        # 第 5 步：标记为"已完成"
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("请求处理完成！"),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """取消任务 — 目前不支持"""
        raise NotImplementedError("暂不支持取消任务")
