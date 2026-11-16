"""/v1/budgets through the real application: CRUD, categories, status, error mapping, N+1 guard."""

from datetime import datetime
from decimal import Decimal

from backend.db.models.transaction import Transaction as TransactionModel

PAYLOAD = {
    "name": "Household",
    "amount": 2000,
    "period": "monthly",
    "categories": [
        {"category_name": "Groceries", "amount_limit": 600},
        {"category_name": "Dining", "amount_limit": 200},
    ],
}


def create(client, payload=PAYLOAD):
    response = client.post("/v1/budgets/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_crud_round_trip(client):
    budget = create(client)
    assert budget["amount"] == 2000.0
    assert budget["currency"] == "CAD"
    assert [c["category_name"] for c in budget["categories"]] == ["Groceries", "Dining"]

    assert client.get(f"/v1/budgets/{budget['id']}").json()["name"] == "Household"

    updated = client.put(f"/v1/budgets/{budget['id']}", json={"name": "Home", "amount": 2500.5}).json()
    assert (updated["name"], updated["amount"]) == ("Home", 2500.5)

    assert client.delete(f"/v1/budgets/{budget['id']}").status_code == 204
    assert client.get("/v1/budgets/").json() == []
    assert [b["id"] for b in client.get("/v1/budgets/", params={"active_only": "false"}).json()] == [budget["id"]]


def test_not_found_and_validation(client):
    assert client.get("/v1/budgets/999").status_code == 404
    assert client.put("/v1/budgets/999", json={"name": "x"}).status_code == 404
    assert client.delete("/v1/budgets/999").status_code == 404
    assert client.get("/v1/budgets/999/status").status_code == 404
    assert client.post("/v1/budgets/", json={**PAYLOAD, "amount": 0}).status_code == 422
    assert client.post("/v1/budgets/", json={**PAYLOAD, "amount": 10.005}).status_code == 422
    assert client.post("/v1/budgets/", json={**PAYLOAD, "period": "quarterly"}).status_code == 422


def test_category_routes(client):
    budget = create(client)
    bid = budget["id"]

    dup = client.post(f"/v1/budgets/{bid}/categories", json={"category_name": "Groceries", "amount_limit": 1})
    assert dup.status_code == 409

    added = client.post(f"/v1/budgets/{bid}/categories", json={"category_name": "Fuel", "amount_limit": 150})
    assert added.status_code == 201
    cid = added.json()["id"]

    renamed = client.put(
        f"/v1/budgets/{bid}/categories/{cid}", json={"category_name": "Transport", "amount_limit": 175}
    )
    assert renamed.status_code == 200
    assert (renamed.json()["category_name"], renamed.json()["amount_limit"]) == ("Transport", 175.0)
    assert client.put(f"/v1/budgets/{bid}/categories/{cid}", json={"category_name": "Dining"}).status_code == 409

    assert client.delete(f"/v1/budgets/{bid}/categories/{cid}").status_code == 204
    assert client.delete(f"/v1/budgets/{bid}/categories/{cid}").status_code == 404
    assert [c["category_name"] for c in client.get(f"/v1/budgets/{bid}").json()["categories"]] == [
        "Groceries",
        "Dining",
    ]


def test_status_for_month(client, db):
    budget = create(client)
    db.add(
        TransactionModel(
            description="groceries",
            amount=Decimal("-150.00"),
            currency="CAD",
            type="expense",
            date=datetime(2026, 2, 28, 23, 0),
            category="Groceries",
        )
    )
    db.commit()

    response = client.get(f"/v1/budgets/{budget['id']}/status", params={"month": "2026-02"})

    assert response.status_code == 200
    body = response.json()
    assert (body["period_start"], body["period_end"]) == ("2026-02-01", "2026-02-28")
    assert body["total_spent"] == 150.0
    assert body["remaining"] == 1850.0
    assert body["status"] == "under"
    assert body["fx_complete"] is True
    groceries = next(c for c in body["categories"] if c["category_name"] == "Groceries")
    assert (groceries["actual_spent"], groceries["remaining"], groceries["status"]) == (150.0, 450.0, "under")
    assert groceries["percentage_used"] == 25.0

    assert client.get(f"/v1/budgets/{budget['id']}/status", params={"month": "02-2026"}).status_code == 400
    assert client.get(f"/v1/budgets/{budget['id']}/status").status_code == 200  # defaults to today's month


def test_list_does_not_issue_one_query_per_budget(client, query_counter):
    for i in range(5):
        create(client, {**PAYLOAD, "name": f"Budget {i}"})

    query_counter["statements"] = 0
    budgets = client.get("/v1/budgets/").json()

    assert len(budgets) == 5
    assert all(len(b["categories"]) == 2 for b in budgets)
    # budgets + one selectin load for categories; without selectinload this would be 6+.
    assert query_counter["statements"] <= 2, query_counter
