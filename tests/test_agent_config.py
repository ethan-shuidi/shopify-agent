from pydantic_ai.models.openai import OpenAIChatModel

from app.agent import build_model
from app.config import Settings


def test_builds_water_pipe_chat_model(monkeypatch) -> None:
    monkeypatch.setenv("FEISHU_APP_ID", "cli_test")
    monkeypatch.setenv("FEISHU_APP_SECRET", "secret")
    monkeypatch.setenv("AGENT_MODEL", "openai-chat:claude-sonnet-4.6")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://agent-api.shuiditech.com/api/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "wp-v1-test")
    monkeypatch.setenv("WATER_PIPE_TITLE", "feishu-shopify-agent")

    model = build_model(Settings(_env_file=None))

    assert isinstance(model, OpenAIChatModel)
    assert model.model_name == "claude-sonnet-4.6"
    assert str(model.base_url).rstrip("/") == "https://agent-api.shuiditech.com/api/v1"
    assert model.client.default_headers["X-WP-Title"] == "feishu-shopify-agent"
