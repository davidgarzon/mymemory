"""
Contract tests for /api/v1/inbox endpoint.

These tests ensure that the inbox contract is never broken,
regardless of LLM or prompt changes.

IMPORTANT: These tests mock parse_with_llm to test backend logic only.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db(monkeypatch):
    """Ensure each test starts with a clean state"""
    # Note: In a real test suite, you'd reset the database here
    # For now, we rely on unique content to avoid conflicts
    yield


def test_list_item_default_shopping():
    """
    TEST 1 - LIST_ITEM → shopping por defecto
    
    When LLM returns LIST_ITEM with list_name=null,
    backend should normalize to list_name="shopping"
    """
    mock_llm_response = {
        "intent": "create_memory",
        "person": None,
        "items": [
            {"type": "LIST_ITEM", "content": "test_arroz_contract_123", "list_name": None},
            {"type": "LIST_ITEM", "content": "test_plátanos_contract_456", "list_name": None}
        ]
    }
    
    with patch("app.api.routes_inbox.parse_with_llm", return_value=mock_llm_response):
        response = client.post(
            "/api/v1/inbox",
            json={"text": "añade arroz y plátanos"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert data["intent"] == "create_memory"
    assert (data["created_count"] + data["reused_count"]) == 2  # Total items (created or reused)
    
    memory_items = data.get("memory_items", [])
    assert len(memory_items) == 2
    
    # Validate contract: LIST_ITEM must have list_name="shopping"
    for item in memory_items:
        assert item["type"] == "LIST_ITEM"
        assert item["list_name"] == "shopping"


def test_task_overrides_list_item():
    """
    TEST 2 - TASK manda sobre LIST_ITEM
    
    When LLM returns LIST_ITEM with list_name="tasks",
    backend should normalize type to TASK
    """
    mock_llm_response = {
        "intent": "create_memory",
        "person": None,
        "items": [
            {"type": "LIST_ITEM", "content": "test_limpiar_ventanas_contract_789", "list_name": "tasks"}
        ]
    }
    
    with patch("app.api.routes_inbox.parse_with_llm", return_value=mock_llm_response):
        response = client.post(
            "/api/v1/inbox",
            json={"text": "añade limpiar ventanas a la lista de tareas"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert (data["created_count"] + data["reused_count"]) == 1  # Total items (created or reused)
    
    # Validate contract: list_name="tasks" must normalize type to TASK
    memory_item = data.get("memory_item") or data.get("memory_items", [])[0]
    assert memory_item["type"] == "TASK"
    assert memory_item["list_name"] == "tasks"


def test_reminder_never_has_list_name():
    """
    TEST 3 - REMINDER nunca tiene list_name
    
    When LLM returns REMINDER with list_name set,
    backend should normalize to list_name=null
    """
    mock_llm_response = {
        "intent": "create_memory",
        "person": None,
        "items": [
            {"type": "REMINDER", "content": "test_reminder_limpiar_ventanas_contract_012", "list_name": "shopping"}
        ]
    }
    
    with patch("app.api.routes_inbox.parse_with_llm", return_value=mock_llm_response):
        response = client.post(
            "/api/v1/inbox",
            json={"text": "recuerdame limpiar ventanas"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert (data["created_count"] + data["reused_count"]) == 1  # Total items (created or reused)
    
    # Validate contract: REMINDER must have list_name=None
    memory_item = data.get("memory_item") or data.get("memory_items", [])[0]
    assert memory_item["type"] == "REMINDER"
    assert memory_item["list_name"] is None


def test_idea_never_has_list_name():
    """
    TEST 4 - IDEA nunca tiene list_name
    
    When LLM returns IDEA with list_name set,
    backend should normalize to list_name=null
    """
    mock_llm_response = {
        "intent": "create_memory",
        "person": None,
        "items": [
            {"type": "IDEA", "content": f"test_idea_unique_{uuid.uuid4().hex[:12]}_finanzas", "list_name": "shopping"}
        ]
    }
    
    with patch("app.api.routes_inbox.parse_with_llm", return_value=mock_llm_response):
        response = client.post(
            "/api/v1/inbox",
            json={"text": "he tenido una idea sobre una app de finanzas"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert (data["created_count"] + data["reused_count"]) == 1  # Total items (created or reused)
    
    # Validate contract: IDEA must have list_name=None
    memory_item = data.get("memory_item") or data.get("memory_items", [])[0]
    assert memory_item["type"] == "IDEA"
    assert memory_item["list_name"] is None


def test_multiple_reminders_with_person():
    """
    TEST 5 - Múltiples REMINDER con persona
    
    When LLM returns multiple REMINDER items with a person,
    backend should assign same person_id to all items
    """
    mock_llm_response = {
        "intent": "create_memory",
        "person": "Andrés",
        "items": [
            {"type": "REMINDER", "content": "test_hablar_salario_contract_345", "list_name": None},
            {"type": "REMINDER", "content": "test_hablar_bonus_contract_678", "list_name": None}
        ]
    }
    
    with patch("app.api.routes_inbox.parse_with_llm", return_value=mock_llm_response):
        response = client.post(
            "/api/v1/inbox",
            json={"text": "hablar con andrés de salario y bonus"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert (data["created_count"] + data["reused_count"]) == 2  # Total items (created or reused)
    
    memory_items = data.get("memory_items", [])
    assert len(memory_items) == 2
    
    # Validate contract: All items should be REMINDER with no list_name, same person_id
    person_ids = []
    for item in memory_items:
        assert item["type"] == "REMINDER"
        assert item["list_name"] is None
        if item.get("related_person_id"):
            person_ids.append(item["related_person_id"])
    
    # Both items should have the same person_id (if person was created)
    if person_ids:
        assert len(set(person_ids)) == 1, "All items should have the same person_id"


def test_empty_items_becomes_unknown():
    """
    TEST 6 - Items vacíos → unknown
    
    When LLM returns empty items array,
    backend should normalize to intent="unknown"
    """
    mock_llm_response = {
        "intent": "create_memory",
        "person": None,
        "items": []
    }
    
    with patch("app.api.routes_inbox.parse_with_llm", return_value=mock_llm_response):
        response = client.post(
            "/api/v1/inbox",
            json={"text": "mensaje que no genera items"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is False
    assert data["intent"] == "unknown"
    assert data["created_count"] == 0
    assert data["reused_count"] == 0
