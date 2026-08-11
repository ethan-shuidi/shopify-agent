from app.memory import SQLiteMemory


def test_memory_round_trip_and_reset(tmp_path) -> None:
    memory = SQLiteMemory(tmp_path / "agent.db")
    memory.initialize()
    memory.add("user:1", "user", "hello")
    memory.add("user:1", "assistant", "hi")

    recent = memory.recent("user:1", 10)
    assert [(item.role, item.content) for item in recent] == [
        ("user", "hello"),
        ("assistant", "hi"),
    ]
    assert memory.reset("user:1") == 2
    assert memory.recent("user:1", 10) == []


def test_claim_event_only_once(tmp_path) -> None:
    memory = SQLiteMemory(tmp_path / "agent.db")
    memory.initialize()
    assert memory.claim_event("om_1") is True
    assert memory.claim_event("om_1") is False

