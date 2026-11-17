"""Route-level check that the import preview names defaulted accounts (#144)."""

from __future__ import annotations

HEADER = "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags\n"


def test_preview_lists_labels_imported_as_cash_by_name(client) -> None:
    body = HEADER + "2026-10-08,Some Store,Electronics,Wallet CA,SOME STORE,,-29.92,\n"
    resp = client.post(
        "/v1/monarch-import/preview",
        files=[("files", ("monarch-transactions-oct.csv", body.encode(), "text/csv"))],
    )
    assert resp.status_code == 200, resp.text
    tx = resp.json()["transactions"]
    assert tx["would_import"] == 1
    report = tx["files"][0]
    assert report["skipped_unknown_account"] == 0
    assert report["skipped_account_labels"] == []
    assert report["defaulted_account_labels"] == ["Wallet CA"]
