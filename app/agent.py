from collections.abc import Sequence
from typing import Protocol

from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import Settings
from app.memory import ConversationMessage, SQLiteMemory
from app.prompts import SYSTEM_PROMPT


class AgentResponder(Protocol):
    def respond(self, session_id: str, user_text: str) -> str: ...


class PydanticAgentResponder:
    def __init__(self, settings: Settings, memory: SQLiteMemory, memory_limit: int = 12) -> None:
        self.memory = memory
        self.memory_limit = memory_limit
        self.agent = Agent(build_model(settings), system_prompt=SYSTEM_PROMPT)

    def respond(self, session_id: str, user_text: str) -> str:
        history = self.memory.recent(session_id, self.memory_limit)
        prompt = _build_prompt(history, user_text)
        result = self.agent.run_sync(prompt)

        # PydanticAI 1.x exposes output; this fallback keeps 0.x upgrades painless.
        answer = getattr(result, "output", None)
        if answer is None:
            answer = getattr(result, "data", None)
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The model returned an empty or unsupported response")

        answer = answer.strip()
        self.memory.add(session_id, "user", user_text)
        self.memory.add(session_id, "assistant", answer)
        return answer


def build_model(settings: Settings) -> OpenAIChatModel | OpenAIResponsesModel:
    model_kind, separator, model_name = settings.agent_model.partition(":")
    if not separator or not model_name:
        raise ValueError("AGENT_MODEL must use the format '<provider>:<model-name>'")
    if model_kind not in {"openai-chat", "openai-responses"}:
        raise ValueError(
            "Water Pipe requires AGENT_MODEL to start with 'openai-chat:' "
            "or 'openai-responses:'"
        )

    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if not api_key:
        raise ValueError("OPENAI_API_KEY must contain your Water Pipe wp-v1 API key")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=settings.openai_base_url,
        default_headers={"X-WP-Title": settings.water_pipe_title},
    )
    provider = OpenAIProvider(openai_client=client)
    if model_kind == "openai-responses":
        return OpenAIResponsesModel(model_name, provider=provider)
    return OpenAIChatModel(model_name, provider=provider)


def _build_prompt(history: Sequence[ConversationMessage], user_text: str) -> str:
    if not history:
        return user_text

    rendered_history = "\n".join(
        f"{'用户' if item.role == 'user' else '助手'}：{item.content}" for item in history
    )
    return f"以下是当前会话最近的对话：\n{rendered_history}\n\n用户的新消息：{user_text}"
