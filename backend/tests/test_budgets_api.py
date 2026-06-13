"""Tests for Budget API endpoints.

Test scenarios:
- Create budget
- List budgets
- Get budget details
- Update budget
- Delete budget
- Add category to budget
- Get budget tracking
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.app.server import create_app
from backend.db.session import get_db
from backend.db.base import Base, engine


@pytest.fixture
def client():
    """Create a test client with fresh database."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    app = create_app()
    client = TestClient(app)

    yield client

    # Cleanup
    Base.metadata.drop_all(bind=engine)


def test_create_budget(client):
    """Test creating a new budget."""
    response = client.post(
        "/v1/budgets/",
        json={
            "name": "Monthly Budget",
            "currency": "CAD",
            "description": "My monthly spending plan",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Monthly Budget"
    assert data["currency"] == "CAD"
    assert data["description"] == "My monthly spending plan"
    assert data["is_active"] is True
    assert "id" in data


def test_list_budgets(client):
    """Test listing all budgets."""
    # Create a budget first
    create_response = client.post(
        "/v1/budgets/",
        json={
            "name": "Test Budget",
            "currency": "CAD",
        },
    )
    assert create_response.status_code == 201

    # List budgets
    response = client.get("/v1/budgets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Budget"


def test_get_budget(client):
    """Test getting a specific budget."""
    # Create a budget
    create_response = client.post(
        "/v1/budgets/",
        json={
            "name": "Get Test Budget",
            "currency": "USD",
            "description": "Testing get endpoint",
        },
    )
    budget_id = create_response.json()["id"]

    # Get the budget
    response = client.get(f"/v1/budgets/{budget_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == budget_id
    assert data["name"] == "Get Test Budget"
    assert data["currency"] == "USD"


def test_get_nonexistent_budget(client):
    """Test getting a nonexistent budget returns 404."""
    response = client.get("/v1/budgets/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_budget(client):
    """Test updating a budget."""
    # Create a budget
    create_response = client.post(
        "/v1/budgets/",
        json={"name": "Original Name", "currency": "CAD"},
    )
    budget_id = create_response.json()["id"]

    # Update the budget
    response = client.put(
        f"/v1/budgets/{budget_id}",
        json={
            "name": "Updated Name",
            "description": "New description",
            "is_active": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"
    assert data["is_active"] is False


def test_delete_budget(client):
    """Test deleting a budget."""
    # Create a budget
    create_response = client.post(
        "/v1/budgets/",
        json={"name": "To Delete", "currency": "CAD"},
    )
    budget_id = create_response.json()["id"]

    # Delete the budget
    response = client.delete(f"/v1/budgets/{budget_id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = client.get(f"/v1/budgets/{budget_id}")
    assert response.status_code == 404


def test_add_category_to_budget(client):
    """Test adding a category to a budget."""
    # Create a budget
    create_response = client.post(
        "/v1/budgets/",
        json={"name": "Budget with Categories", "currency": "CAD"},
    )
    budget_id = create_response.json()["id"]

    # Add a category
    response = client.post(
        f"/v1/budgets/{budget_id}/categories",
        json={
            "category_name": "Groceries",
            "limit_amount": 500.00,
            "period_type": "monthly",
            "rollover_excess": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category_name"] == "Groceries"
    assert float(data["limit_amount"]) == 500.00
    assert data["period_type"] == "monthly"


def test_add_category_invalid_period(client):
    """Test adding a category with invalid period type."""
    # Create a budget
    create_response = client.post(
        "/v1/budgets/",
        json={"name": "Test Budget", "currency": "CAD"},
    )
    budget_id = create_response.json()["id"]

    # Try to add category with invalid period
    response = client.post(
        f"/v1/budgets/{budget_id}/categories",
        json={
            "category_name": "Food",
            "limit_amount": 500.00,
            "period_type": "invalid_period",
        },
    )
    assert response.status_code == 400


def test_get_budget_tracking(client):
    """Test getting budget tracking for a date range."""
    # Create a budget
    create_response = client.post(
        "/v1/budgets/",
        json={"name": "Tracking Budget", "currency": "CAD"},
    )
    budget_id = create_response.json()["id"]

    # Get tracking (should default to current month)
    response = client.get(f"/v1/budgets/{budget_id}/tracking")
    assert response.status_code == 200
    data = response.json()
    assert data["budget"]["id"] == budget_id
    assert data["budget"]["name"] == "Tracking Budget"
    assert "period_start" in data
    assert "period_end" in data
    assert "categories" in data
    assert "summary" in data


def test_list_budgets_active_only(client):
    """Test listing only active budgets."""
    # Create two budgets
    active_response = client.post(
        "/v1/budgets/",
        json={"name": "Active Budget", "currency": "CAD"},
    )
    active_id = active_response.json()["id"]

    inactive_response = client.post(
        "/v1/budgets/",
        json={"name": "Inactive Budget", "currency": "CAD"},
    )
    inactive_id = inactive_response.json()["id"]

    # Deactivate the second budget
    client.put(f"/v1/budgets/{inactive_id}", json={"is_active": False})

    # List only active
    response = client.get("/v1/budgets/?active_only=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Active Budget"
