"""
原生 A2A Server — 不依赖 a2a-sdk，仅用 Python 标准库 + Starlette

完全符合 A2A v1.0 JSON-RPC 协议，可以和 SDK Client 互通。

端口: 10010
"""

import uuid
from datetime import datetime, timezone
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse


# ── Agent Card（静态 JSON）────────────────────────────
AGENT_CARD = {
    "name": "原生 A2A Agent",
    "description": "不使用任何 A2A SDK 的纯原生实现",
    "version": "1.0.0",
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "capabilities": {"streaming": False, "pushNotifications": False},
    "supportedInterfaces": [
        {"protocolBinding": "JSONRPC", "url": "http://127.0.0.1:10010"}
    ],
    "skills": [
        {
            "id": "echo",
            "name": "Echo",
            "description": "原样返回你的消息",
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"],
            "tags": ["echo", "raw"],
            "examples": ["echo test"],
        }
    ],
    "preferredTransport": "JSONRPC",
    "protocolVersion": "1.0",
    "url": "http://127.0.0.1:10010",
}

# 内存 Task 存储
TASKS: dict[str, dict] = {}


# ── 路由 1: Agent Card 发现端点 ───────────────────────
async def get_agent_card(request: Request):
    """GET /.well-known/agent-card.json — 返回 Agent 名片"""
    return JSONResponse(AGENT_CARD)


# ── 路由 2: JSON-RPC 通信端点 ──────────────────────────
async def handle_jsonrpc(request: Request):
    """POST / — 处理所有 A2A JSON-RPC 请求"""

    # 检查 A2A-Version Header（v1.0 必须）
    version = request.headers.get("a2a-version", "")
    if version and version != "1.0":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32009, "message": f"A2A version '{version}' is not supported. Expected '1.0'."}
        }, status_code=200)

    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {})
    req_id = body.get("id")

    # 路由到对应的处理函数
    if method == "SendMessage":
        result = await handle_send_message(params)
    elif method == "GetTask":
        result = await handle_get_task(params)
    elif method == "CancelTask":
        return jsonrpc_error(req_id, -32002, "Task not cancelable")
    else:
        return jsonrpc_error(req_id, -32601, f"Method not found: {method}")

    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


# ── SendMessage 处理逻辑 ─────────────────────────────
async def handle_send_message(params: dict) -> dict:
    """
    处理 SendMessage 请求：
    1. 从 message 中提取用户文本
    2. 创建 Task
    3. 调用 Agent 逻辑生成回复
    4. 返回完整的 Task 对象
    """
    message = params.get("message", {})
    parts = message.get("parts", [])

    # 提取文本
    user_text = ""
    for part in parts:
        if "text" in part:
            user_text += part["text"]

    # 创建 Task
    task_id = str(uuid.uuid4())
    context_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Agent 逻辑（简单 echo + 装饰）
    agent_reply = (
        f"⚡ [原生Agent] 收到你的消息：「{user_text}」\n"
        f"这个 Agent 完全不用 a2a-sdk，纯手写 JSON-RPC！"
    )

    # 构造 Task 对象
    task = {
        "id": task_id,
        "contextId": context_id,
        "status": {
            "state": "TASK_STATE_COMPLETED",
            "timestamp": now,
        },
        "artifacts": [
            {
                "artifactId": str(uuid.uuid4()),
                "parts": [
                    {"text": agent_reply, "mediaType": "text/plain"}
                ],
            }
        ],
        "history": [
            {
                "messageId": message.get("messageId", str(uuid.uuid4())),
                "contextId": context_id,
                "taskId": task_id,
                "role": "ROLE_USER",
                "parts": parts,
            }
        ],
    }

    # 存储到内存
    TASKS[task_id] = task
    return {"task": task}


# ── GetTask 处理逻辑 ─────────────────────────────────
async def handle_get_task(params: dict) -> dict:
    """查询 Task 状态"""
    task_id = params.get("id", "")
    if task_id not in TASKS:
        return jsonrpc_error(None, -32001, f"Task not found: {task_id}")
    return {"task": TASKS[task_id]}


# ── 辅助函数 ─────────────────────────────────────────
def jsonrpc_error(req_id, code, message):
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    })


# ── 启动 ─────────────────────────────────────────────
app = Starlette(routes=[
    Route("/.well-known/agent-card.json", get_agent_card),
    Route("/", handle_jsonrpc, methods=["POST"]),
])

if __name__ == "__main__":
    import uvicorn
    print("⚡ 原生 A2A Agent (无 SDK) 启动在 :10010")
    uvicorn.run(app, host="127.0.0.1", port=10010)