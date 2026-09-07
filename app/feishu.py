import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageReactionRequest,
    CreateMessageReactionRequestBody,
    DeleteMessageReactionRequest,
    Emoji,
    P2ImMessageReceiveV1,
    ReplyMessageRequest,
    ReplyMessageRequestBody,
)

from app.config import Settings
from app.memory import SQLiteMemory
from app.messages import IncomingMessage, parse_text_content
from app.service import ChatService

logger = logging.getLogger(__name__)


class FeishuGateway:
    def __init__(self, settings: Settings, service: ChatService, memory: SQLiteMemory) -> None:
        self.settings = settings
        self.service = service
        self.memory = memory
        self.executor = ThreadPoolExecutor(
            max_workers=settings.agent_max_workers,
            thread_name_prefix="agent-worker",
        )
        self.api_client = (
            lark.Client.builder()
            .app_id(settings.feishu_app_id)
            .app_secret(settings.feishu_app_secret)
            .log_level(_lark_log_level(settings.log_level))
            .build()
        )

    def start(self) -> None:
        event_handler = (
            lark.EventDispatcherHandler.builder(
                self.settings.feishu_encrypt_key,
                self.settings.feishu_verification_token,
            )
            .register_p2_im_message_receive_v1(self._on_message)
            .build()
        )
        websocket_client = lark.ws.Client(
            self.settings.feishu_app_id,
            self.settings.feishu_app_secret,
            event_handler=event_handler,
            log_level=_lark_log_level(self.settings.log_level),
        )
        logger.info("Starting Feishu WebSocket connection")
        websocket_client.start()

    def _on_message(self, data: P2ImMessageReceiveV1) -> None:
        message = _to_incoming_message(data)
        if message is None:
            return
        if not self.memory.claim_event(message.message_id):
            logger.info("Ignoring duplicate message_id=%s", message.message_id)
            return
        self.executor.submit(self._process_and_reply, message)

    def _process_and_reply(self, message: IncomingMessage) -> None:
        thinking_reaction_id = None
        if self.service.needs_thinking_status(message):
            thinking_reaction_id = self.add_thinking_reaction(message.message_id)

        answer = self.service.handle(message)
        if answer:
            self.reply(message.message_id, answer)
        if thinking_reaction_id:
            self.remove_reaction(message.message_id, thinking_reaction_id)

    def reply(self, message_id: str, text: str) -> str | None:
        card = {
            "schema": "2.0",
            "body": {
                "direction": "vertical",
                "elements": [{"tag": "markdown", "content": text}],
            },
        }
        request = (
            ReplyMessageRequest.builder()
            .message_id(message_id)
            .request_body(
                ReplyMessageRequestBody.builder()
                .msg_type("interactive")
                .content(json.dumps(card, ensure_ascii=False))
                .build()
            )
            .build()
        )
        response = self.api_client.im.v1.message.reply(request)
        if not response.success():
            logger.error(
                "Feishu reply failed: code=%s msg=%s log_id=%s",
                response.code,
                response.msg,
                response.get_log_id(),
            )
            return None
        return getattr(getattr(response, "data", None), "message_id", None)

    def add_thinking_reaction(self, message_id: str) -> str | None:
        try:
            request = (
                CreateMessageReactionRequest.builder()
                .message_id(message_id)
                .request_body(
                    CreateMessageReactionRequestBody.builder()
                    .reaction_type(Emoji.builder().emoji_type("THINKING").build())
                    .build()
                )
                .build()
            )
            response = self.api_client.im.v1.message_reaction.create(request)
        except Exception:
            logger.exception("Failed to add Feishu thinking reaction")
            return None
        if not response.success():
            logger.error(
                "Feishu thinking reaction failed: code=%s msg=%s log_id=%s",
                response.code,
                response.msg,
                response.get_log_id(),
            )
            return None
        return getattr(getattr(response, "data", None), "reaction_id", None)

    def remove_reaction(self, message_id: str, reaction_id: str) -> None:
        try:
            request = (
                DeleteMessageReactionRequest.builder()
                .message_id(message_id)
                .reaction_id(reaction_id)
                .build()
            )
            response = self.api_client.im.v1.message_reaction.delete(request)
        except Exception:
            logger.exception("Failed to remove Feishu thinking reaction")
            return
        if not response.success():
            logger.warning(
                "Feishu thinking reaction cleanup failed: code=%s msg=%s log_id=%s",
                response.code,
                response.msg,
                response.get_log_id(),
            )


def _to_incoming_message(data: P2ImMessageReceiveV1) -> IncomingMessage | None:
    event: Any = getattr(data, "event", None)
    message: Any = getattr(event, "message", None)
    sender: Any = getattr(event, "sender", None)
    sender_id: Any = getattr(sender, "sender_id", None)

    if message is None or getattr(message, "message_type", "") != "text":
        return None

    message_id = getattr(message, "message_id", "")
    open_id = getattr(sender_id, "open_id", "")
    if not message_id or not open_id:
        logger.warning("Ignoring malformed Feishu message event")
        return None

    mentions = getattr(message, "mentions", None) or []
    return IncomingMessage(
        message_id=message_id,
        chat_id=getattr(message, "chat_id", ""),
        chat_type=getattr(message, "chat_type", ""),
        sender_id=open_id,
        text=parse_text_content(getattr(message, "content", "")),
        has_mentions=bool(mentions),
    )


def _lark_log_level(level: str) -> lark.LogLevel:
    return getattr(lark.LogLevel, level.upper(), lark.LogLevel.INFO)
