"""/v1/exchange: CRUD, validation, any-ISO currencies, benchmark and summary math."""

from datetime import date
from decimal import Decimal

from backend.db.models.asset import Asset, AssetType
from backend.db.models.fx_rate import FxRate
from backend.db.models.transaction import Transaction

CAD_BRL = {
    "date": "2026-10-01",
    "provider": "remitly",
    "from_currency": "CAD",
    "from_amount": 1000,
    "to_currency": "BRL",
    "to_amount": 3900,
    "fee_amount": 3.99,
    "from_label": "Bank CAD",
    "to_label": "Example BRL account",
}
CAD_USD = {
    "date": "2026-10-02",
    "provider": "wise",
    "from_currency": "cad",  # normalised to upper case
    "from_amount": 1350,
    "to_currency": "USD",
    "to_amount": 990,
    "fee_amount": 4.5,
    "fee_currency": "CAD",
}


def create(client, payload):
    response = client.post("/v1/exchange/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def rate(r) -> Decimal:
    return Decimal(str(r)).quantize(Decimal("0.0001"))


def test_crud_round_trip_accepts_brl(client):
    ex = create(client, CAD_BRL)
    assert (ex["from_currency"], ex["to_currency"]) == ("CAD", "BRL")
    assert ex["to_amount"] == 3900.0
    assert rate(ex["effective_rate"]) == Decimal("3.9000")
    assert ex["fee_currency"] == "CAD"  # defaults to the source currency
    assert ex["benchmark"] is None  # no reference rate outside CAD<->USD
    assert ex["source"] == "manual"

    updated = client.put(f"/v1/exchange/{ex['id']}", json={"to_amount": 3950, "notes": "better rate"}).json()
    assert updated["to_amount"] == 3950.0
    assert rate(updated["effective_rate"]) == Decimal("3.9500")

    assert client.get(f"/v1/exchange/{ex['id']}").json()["notes"] == "better rate"
    assert client.delete(f"/v1/exchange/{ex['id']}").status_code == 204
    assert client.get("/v1/exchange/").json() == []


def test_validation(client):
    assert client.post("/v1/exchange/", json={**CAD_BRL, "to_currency": "CAD"}).status_code == 422
    assert client.post("/v1/exchange/", json={**CAD_BRL, "from_currency": "CA"}).status_code == 422
    assert client.post("/v1/exchange/", json={**CAD_BRL, "from_currency": "C4D"}).status_code == 422
    assert client.post("/v1/exchange/", json={**CAD_BRL, "from_amount": 0}).status_code == 422
    assert client.post("/v1/exchange/", json={**CAD_BRL, "from_amount": 1.005}).status_code == 422
    assert client.post("/v1/exchange/", json={**CAD_BRL, "provider": "paypal"}).status_code == 422
    assert client.post("/v1/exchange/", json={**CAD_BRL, "from_asset_id": 999}).status_code == 422

    ex = create(client, CAD_BRL)
    # Merged record must still have distinct currencies.
    assert client.put(f"/v1/exchange/{ex['id']}", json={"to_currency": "CAD"}).status_code == 422
    assert client.put(f"/v1/exchange/{ex['id']}", json={"from_amount": None}).status_code == 422
    assert client.put(f"/v1/exchange/{ex['id']}", json={"fee_amount": None}).status_code == 200
    assert client.get(f"/v1/exchange/{ex['id']}").json()["to_currency"] == "BRL"

    assert client.get("/v1/exchange/999").status_code == 404
    assert client.put("/v1/exchange/999", json={"notes": "x"}).status_code == 404
    assert client.delete("/v1/exchange/999").status_code == 404
    assert client.get("/v1/exchange/", params={"date_from": "2026-12-01", "date_to": "2026-01-01"}).status_code == 400


def test_asset_links(client, db):
    asset = Asset(symbol="WISE_CAD", name="Wise CAD", asset_type=AssetType.CASH, currency="CAD")
    db.add(asset)
    db.commit()
    ex = create(client, {**CAD_USD, "from_asset_id": asset.id})
    assert ex["from_asset_id"] == asset.id


def test_filters_newest_first(client):
    brl = create(client, CAD_BRL)
    usd = create(client, CAD_USD)
    assert [e["id"] for e in client.get("/v1/exchange/").json()] == [usd["id"], brl["id"]]
    assert [e["id"] for e in client.get("/v1/exchange/", params={"currency": "brl"}).json()] == [brl["id"]]
    assert [e["id"] for e in client.get("/v1/exchange/", params={"provider": "wise"}).json()] == [usd["id"]]
    assert client.get("/v1/exchange/", params={"date_to": "2026-09-30"}).json() == []


def test_benchmark_for_cad_usd(client, db):
    # 1 USD = 1.35 CAD  ->  1 CAD = 0.740740.. USD; effective 990/1350 = 0.7333..
    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 10, 1), rate=Decimal("1.35"), source="bank_of_canada"))
    db.commit()
    ex = create(client, CAD_USD)
    bench = ex["benchmark"]
    assert bench["as_of"] == "2026-10-01"  # most recent prior observation
    assert rate(bench["rate"]) == Decimal("0.7407")
    assert round(bench["spread_pct"], 2) == 1.00

    reverse = create(
        client, {**CAD_USD, "from_currency": "USD", "from_amount": 1000, "to_currency": "CAD", "to_amount": 1336.5}
    )
    assert rate(reverse["benchmark"]["rate"]) == Decimal("1.3500")
    assert round(reverse["benchmark"]["spread_pct"], 2) == 1.00


def test_summary_per_pair(client, db):
    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 10, 2), rate=Decimal("1.35"), source="bank_of_canada"))
    db.commit()
    create(client, CAD_BRL)
    create(client, {**CAD_BRL, "date": "2026-10-15", "from_amount": 500, "to_amount": 2000, "fee_amount": None})
    create(client, CAD_USD)

    summary = client.get("/v1/exchange/summary").json()
    assert summary["count"] == 3
    pairs = {(p["from_currency"], p["to_currency"]): p for p in summary["pairs"]}

    brl = pairs[("CAD", "BRL")]
    assert (brl["count"], brl["total_from"], brl["total_to"]) == (2, 1500.0, 5900.0)
    assert rate(brl["average_rate"]) == Decimal("3.9333")
    assert brl["fees"] == {"CAD": 3.99}
    assert (brl["benchmark_coverage"], brl["spread_cost"], brl["spread_pct"]) == (0, None, None)

    usd = pairs[("CAD", "USD")]
    assert usd["benchmark_coverage"] == 1
    assert usd["spread_cost"] == 10.0  # 1350 / 1.35 = 1000 USD reference vs 990 received
    assert round(usd["spread_pct"], 2) == 1.00


def test_exchanges_do_not_touch_cash_flow(client, db):
    create(client, CAD_BRL)
    assert db.query(Transaction).count() == 0
