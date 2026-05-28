# 🤖 A2A Protocol 学习项目

通过构建来学习 A2A (Agent-to-Agent) 协议。从最简单的 Hello World 到多 Agent 协作，再到不用 SDK 的原生实现。

---

## 📂 项目结构

```
a2a-learning/
│
├── 📁 phase1-hello-world/          第一阶段：最小 A2A Agent
│   ├── server.py                     Server + Agent Card
│   ├── agent_executor.py             Agent 逻辑
│   └── client.py                     Client 测试
│
├── 📁 phase2-multi-agent/          第二阶段：多 Agent 协作
│   ├── greeter_agent.py              Agent 1: 打招呼 (:10001)
│   ├── translator_agent.py           Agent 2: 翻译 (:10002)
│   ├── orchestrator_agent.py         Agent 3: 调度员 (:10003)
│   └── test_multi_agent.py           协作测试脚本
│
├── 📁 phase3-raw/                  第三阶段：不依赖 SDK 的原生实现
│   ├── raw_server.py                 原生 Server (:10010)
│   └── raw_client.py                 原生 Client
│
└── README.md
```

## 🚀 快速开始

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> 🔑 API Key 已内置于 `llm_client.py`，也可通过环境变量 `DEEPSEEK_API_KEY` 覆盖。

---

## Phase 1：Hello World

最简单的 A2A Agent，一个 Server + 一个 Client。

```
python phase1-hello-world/server.py   # 启动 Server (:9999)
python phase1-hello-world/client.py   # 另一个终端跑 Client
```

## Phase 2：多 Agent 协作

三个 Agent 互相通信。Orchestrator 根据用户意图，自动路由到 Greeter 或 Translator。

```
# 三个终端分别启动
python phase2-multi-agent/greeter_agent.py       # :10001
python phase2-multi-agent/translator_agent.py     # :10002
python phase2-multi-agent/orchestrator_agent.py   # :10003

# 第四个终端测试
python phase2-multi-agent/test_multi_agent.py
```

数据流：用户 → Orchestrator → Greeter / Translator → Orchestrator → 用户

## Phase 3：原生实现（不依赖 a2a-sdk）

纯 Python + httpx 手写 A2A 协议，和 SDK 版本完全互通。

```
# 先启动一个 SDK Agent 作为对比
python phase2-multi-agent/greeter_agent.py   # SDK Server :10001

# 再启动原生 Server
python phase3-raw/raw_server.py               # 原生 Server :10010

# 用原生 Client 同时测试两个
python phase3-raw/raw_client.py
```

也可以用 curl 手动测试：

```
curl -s -X POST http://127.0.0.1:10010/ \
  -H "Content-Type: application/json" \
  -H "A2A-Version: 1.0" \
  -d '{
    "jsonrpc": "2.0",
    "method": "SendMessage",
    "id": 1,
    "params": {
      "message": {
        "messageId": "test-001",
        "role": "ROLE_USER",
        "parts": [{"text": "你好"}]
      }
    }
  }'
```

---

## 📡 A2A JSON-RPC 协议要点

Agent Card 端点：GET /.well-known/agent-card.json
JSON-RPC 端点：POST /
必须 Header：A2A-Version: 1.0
方法名大驼峰：SendMessage, GetTask, CancelTask
Role 枚举：ROLE_USER, ROLE_AGENT
Part 格式：{"text": "xxx"}（无 type 字段）

---

## 🔗 互通性验证

SDK Client → SDK Server — 通过
SDK Client → 原生 Server — 通过
原生 Client → SDK Server — 通过
原生 Client → 原生 Server — 通过

## 📄 License

MIT
