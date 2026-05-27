"""
A2A Server 启动入口

这个文件做三件事：
1. 定义 Agent Card（Agent 的名片）
2. 把 Agent Card + Agent Executor 组装成 A2A 请求处理器
3. 启动 HTTP 服务
"""

import uvicorn
from starlette.applications import Starlette

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

from agent_executor import MyAgentExecutor


# ── 第 1 步：定义 Agent Skill（Agent 能做什么）──────────
my_skill = AgentSkill(
    id="hello_world",
    name="Hello World 机器人",
    description="一个简单的示例 Agent，能接收消息并回复",
    input_modes=["text/plain"],
    output_modes=["text/plain"],
    tags=["demo", "hello-world", "a2a"],
    examples=["你好", "hello", "测试一下"],
)


# ── 第 2 步：定义 Agent Card（Agent 的完整名片）─────────
agent_card = AgentCard(
    name="我的第一个 A2A Agent",
    description="学习 A2A 协议的 Hello World 示例 Agent",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(
        streaming=True,           # 支持流式响应
        push_notifications=False,  # 暂不支持推送通知
    ),
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url="http://127.0.0.1:9999",
        )
    ],
    skills=[my_skill],
)


# ── 第 3 步：组装请求处理器 ─────────────────────────
request_handler = DefaultRequestHandler(
    agent_executor=MyAgentExecutor(),
    task_store=InMemoryTaskStore(),  # 内存存储（重启丢失，生产环境要换数据库）
    agent_card=agent_card,
)


# ── 第 4 步：创建 Starlette 应用 ────────────────────
routes = []
# 自动注册 /.well-known/a2a.json 路由（Agent Card 发现端点）
routes.extend(create_agent_card_routes(agent_card))
# 自动注册 JSON-RPC 路由（A2A 通信端点）
routes.extend(create_jsonrpc_routes(request_handler, "/"))

app = Starlette(routes=routes)


# ── 第 5 步：启动服务 ─────────────────────────────
if __name__ == "__main__":
    print("🚀 A2A Agent 启动中...")
    print(f"📋 Agent Card: http://127.0.0.1:9999/.well-known/a2a.json")
    print(f"📡 JSON-RPC 端点: http://127.0.0.1:9999/")
    uvicorn.run(app, host="127.0.0.1", port=9999)
