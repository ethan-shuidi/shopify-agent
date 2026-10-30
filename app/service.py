import logging

from app.agent import AgentResponder
from app.memory import SQLiteMemory
from app.messages import IncomingMessage, normalize_user_text, should_handle

logger = logging.getLogger(__name__)

HELP_TEXT = """\
我是本地 Agent，目前支持普通问答和短期会话记忆。

可用命令：
- /help：查看帮助
- /reset：清除当前私聊或群聊的会话记忆
"""


class ChatService:
    def __init__(self, responder: AgentResponder, memory: SQLiteMemory) -> None:
        self.responder = responder
        self.memory = memory

    def handle(self, message: IncomingMessage) -> str | None:
        if not should_handle(message):
            return None

        text = normalize_user_text(message.text)
        command = text.lower()

        if command in {"/help", "help", "帮助"}:
            return HELP_TEXT
        if command in {"/reset", "reset", "清空会话"}:
            self.memory.reset(message.session_id)
            return "当前会话记忆已清除。"
        if not text:
            return "请在 @我 后面写上你的问题。"

        try:
            return self.responder.respond(message.session_id, text, message.image_bytes)
        except Exception:
            logger.exception("Agent failed while handling message_id=%s", message.message_id)
            return "本地 Agent 暂时处理失败，请检查模型配置或稍后重试。"

    def needs_thinking_status(self, message: IncomingMessage) -> bool:
        """Whether handling the message will require a model request."""
        if not should_handle(message):
            return False

        text = normalize_user_text(message.text)
        return bool(text) and text.lower() not in {
            "/help",
            "help",
            "帮助",
            "/reset",
            "reset",
            "清空会话",
        }
