# 🤖 A2A Hello World

学习 [A2A (Agent-to-Agent) 协议](https://a2a-protocol.org/) 的 Hello World 示例项目。

通过构建一个最简单的 A2A Agent 来学习协议核心概念。

## 📖 项目结构

```
a2a-hello-world/
├── server.py            # A2A Server 启动入口 + Agent Card 定义
├── agent_executor.py    # Agent 核心逻辑（处理消息、返回结果）
├── client.py            # A2A Client 测试脚本
└── README.md
```

## 🚀 快速开始

### 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install a2a-sdk httpx starlette uvicorn sse-starlette
```

### 启动 Server

```bash
python server.py
```

Server 启动后会监听在 `http://127.0.0.1:9999`

- Agent Card（名片）: `http://127.0.0.1:9999/.well-known/agent-card.json`
- JSON-RPC 端点: `http://127.0.0.1:9999/`

### 运行 Client 测试

新开一个终端：

```bash
source venv/bin/activate
python client.py
```

## 🧠 核心概念

这个项目演示了 A2A 协议的核心流程：

1. **Agent Card（名片）** — Agent 在 `/.well-known/agent-card.json` 发布自己的能力描述
2. **Agent Discovery（发现）** — Client 读取 Agent Card 来了解 Agent 的能力
3. **SendMessage（发送消息）** — Client 通过 JSON-RPC 向 Agent 发送消息
4. **Task Lifecycle（任务生命周期）** — SUBMITTED → WORKING → COMPLETED
5. **Artifact（产物）** — Agent 处理完成后返回的交付物

## 📚 学习路线

- [x] Phase 1：理解 A2A 核心概念
- [x] Phase 2：搭建最小 A2A Server + Client
- [ ] Phase 3：接入 LLM（智谱 GLM）让 Agent 真正智能
- [ ] Phase 4：多 Agent 协作
- [ ] Phase 5：流式响应、推送通知等进阶功能

## 📄 License

MIT
