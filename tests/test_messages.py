from app.messages import (
    IncomingMessage,
    normalize_user_text,
    parse_text_content,
    should_handle,
)


def make_message(**overrides: object) -> IncomingMessage:
    values = {
        "message_id": "om_1",
        "chat_id": "oc_1",
        "chat_type": "p2p",
        "sender_id": "ou_1",
        "text": "hello",
        "has_mentions": False,
    }
    values.update(overrides)
    return IncomingMessage(**values)  # type: ignore[arg-type]


def test_parse_text_content() -> None:
    assert parse_text_content('{"text":"你好"}') == "你好"
    assert parse_text_content("not-json") == ""


def test_normalize_removes_feishu_mentions() -> None:
    assert normalize_user_text("@_user_1   帮我总结") == "帮我总结"


def test_private_message_is_handled_without_mention() -> None:
    assert should_handle(make_message()) is True


def test_group_message_requires_mention() -> None:
    assert should_handle(make_message(chat_type="group", has_mentions=False)) is False
    assert should_handle(make_message(chat_type="group", has_mentions=True)) is True


def test_session_is_isolated_by_user_or_chat() -> None:
    assert make_message().session_id == "user:ou_1"
    assert make_message(chat_type="group").session_id == "chat:oc_1"

