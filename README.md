# Feishu Local Agent

一个运行在本地、通过飞书长连接接收消息的轻量 Agent 骨架。当前版本只提供对话、短期记忆和基础命令，为后续 Shopify 工具预留扩展位置。

## 当前能力

- 飞书私聊文本消息
- 群聊中仅在 @机器人 时响应
- PydanticAI 模型调用
- SQLite 会话记忆与飞书事件去重
- `/help` 与 `/reset` 命令
- 后台线程执行模型请求，避免阻塞飞书事件回调

## 1. 飞书开放平台配置

1. 在飞书开放平台创建“企业自建应用”。
2. 在“应用能力”中启用机器人。
3. 添加消息读取和机器人发消息所需权限，并完成管理员授权。
4. 在“事件与回调”中选择“使用长连接接收事件”。
5. 订阅事件 `im.message.receive_v1`。
6. 创建版本并发布应用，然后把机器人加入需要测试的群聊。
7. 从“凭证与基础信息”复制 App ID 和 App Secret。

飞书控制台的权限名称可能随版本调整；如果收不到消息，优先查看飞书控制台的权限与事件投递日志。

## 2. 本地运行

需要 Python 3.11 或更高版本。

```bash
cd /Users/shuidi/workspace/feishu-local-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

编辑 `.env`，至少填写：

```dotenv
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
AGENT_MODEL=openai-chat:claude-sonnet-4.6
OPENAI_BASE_URL=https://agent-api.shuiditech.com/api/v1
OPENAI_API_KEY=wp-v1-xxx
WATER_PIPE_TITLE=feishu-shopify-agent
```

启动：

```bash
feishu-local-agent
```

看到 `Starting Feishu WebSocket connection` 后，在飞书中私聊机器人，或在群聊中 @机器人。

## 3. Water Pipe 模型配置

当前默认通过 Water Pipe 的 OpenAI-compatible Chat Completions 接口调用 Sonnet 4.6：

```dotenv
AGENT_MODEL=openai-chat:claude-sonnet-4.6
OPENAI_BASE_URL=https://agent-api.shuiditech.com/api/v1
OPENAI_API_KEY=wp-v1-xxx
WATER_PIPE_TITLE=feishu-shopify-agent
```

请求会携带 `X-WP-Title: feishu-shopify-agent`，方便在 Water Pipe Activity 中识别调用来源。
如需更换模型，只修改 `AGENT_MODEL` 冒号后的模型 ID，并确认当前 API Key 有访问权限。

## 4. 测试与检查

```bash
pytest
ruff check .
```

## 5. 后续扩展 Shopify

后续工具建议放入 `app/tools/`，并按以下顺序扩展：

1. 只读：列出主题、读取文件、搜索主题文件。
2. 安全写入：在开发主题中生成修改并返回 diff。
3. 校验：运行 Theme Check，返回预览地址。
4. 审批：用户在飞书确认后才允许发布或写入生产主题。

不要把任意 Shell 或生产主题发布能力直接暴露给模型。
