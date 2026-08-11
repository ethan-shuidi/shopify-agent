import logging

from pydantic import ValidationError

from app.agent import PydanticAgentResponder
from app.config import get_settings
from app.feishu import FeishuGateway
from app.memory import SQLiteMemory
from app.service import ChatService


def main() -> None:
    try:
        settings = get_settings()
    except ValidationError as exc:
        raise SystemExit(f"配置错误，请检查 .env：\n{exc}") from exc

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    memory = SQLiteMemory(settings.database_path)
    memory.initialize()
    responder = PydanticAgentResponder(
        settings=settings,
        memory=memory,
        memory_limit=settings.memory_message_limit,
    )
    service = ChatService(responder=responder, memory=memory)
    gateway = FeishuGateway(settings=settings, service=service, memory=memory)
    gateway.start()


if __name__ == "__main__":
    main()
