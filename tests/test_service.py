from dataclasses import dataclass

from app.memory import SQLiteMemory
from app.messages import IncomingMessage
from app.service import ChatService


@dataclass
class FakeResponder:
    answer: str = "agent answer"

    def respond(self, session_id: str, user_text: str, image_bytes: bytes | None = None) -> str:
        return f"{self.answer}: {session_id}: {user_text}"


def message(text: str, *, chat_type: str = "p2p", has_mentions: bool = False):
    return IncomingMessage(
        message_id="om_1",
        chat_id="oc_1",
        chat_type=chat_type,
        sender_id="ou_1",
        text=text,
        has_mentions=has_mentions,
    )


def test_help_and_reset_commands(tmp_path) -> None:
    memory = SQLiteMemory(tmp_path / "agent.db")
    memory.initialize()
    memory.add("user:ou_1", "user", "old")
    service = ChatService(FakeResponder(), memory)

    assert "可用命令" in service.handle(message("/help"))
    assert service.handle(message("/reset")) == "当前会话记忆已清除。"
    assert memory.recent("user:ou_1", 5) == []


def test_message_reaches_responder(tmp_path) -> None:
    memory = SQLiteMemory(tmp_path / "agent.db")
    memory.initialize()
    service = ChatService(FakeResponder(), memory)
    assert service.handle(message("你好")) == "agent answer: user:ou_1: 你好"


def test_thinking_status_only_for_model_requests(tmp_path) -> None:
    memory = SQLiteMemory(tmp_path / "agent.db")
    memory.initialize()
    service = ChatService(FakeResponder(), memory)

    assert service.needs_thinking_status(message("你好")) is True
    assert service.needs_thinking_status(message("/help")) is False
    assert service.needs_thinking_status(message("/reset")) is False
    assert service.needs_thinking_status(message("你好", chat_type="group")) is False


def test_unmentioned_group_message_is_ignored(tmp_path) -> None:
    memory = SQLiteMemory(tmp_path / "agent.db")
    memory.initialize()
    service = ChatService(FakeResponder(), memory)
    assert service.handle(message("你好", chat_type="group")) is None
