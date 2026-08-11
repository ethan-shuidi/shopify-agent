import json
import re
from dataclasses import dataclass

MENTION_PATTERN = re.compile(r"@_user_\d+\s*")


@dataclass(frozen=True, slots=True)
class IncomingMessage:
    message_id: str
    chat_id: str
    chat_type: str
    sender_id: str
    text: str
    has_mentions: bool = False

    @property
    def session_id(self) -> str:
        if self.chat_type == "p2p":
            return f"user:{self.sender_id}"
        return f"chat:{self.chat_id}"


def parse_text_content(raw_content: str) -> str:
    """Extract text from the JSON content used by Feishu text messages."""
    try:
        content = json.loads(raw_content)
    except (TypeError, json.JSONDecodeError):
        return ""
    text = content.get("text", "")
    return text if isinstance(text, str) else ""


def normalize_user_text(text: str) -> str:
    """Remove Feishu mention placeholders and surrounding whitespace."""
    return MENTION_PATTERN.sub("", text).strip()


def should_handle(message: IncomingMessage) -> bool:
    if message.chat_type == "p2p":
        return True
    return message.has_mentions

