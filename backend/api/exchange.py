"""Currency exchange ledger API (manual entry; imports live in a later slice)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status

from backend.db.models.exchange import Exchange
from backend.db.session import DbSession
from backend.models.exchange import (
    Benchmark,
    ExchangeCreate,
    ExchangeOut,
    ExchangeProvider,
    ExchangeSummary,
    ExchangeUpdate,
)
from backend.services.exchange_service import (
    BenchmarkRates,
    ExchangeNotFound,
    ExchangeService,
    Filters,
    InvalidExchange,
    benchmark_rate,
    spread_pct,
)

router = APIRouter(prefix="/v1/exchange", tags=["exchange"])


def _out(exchange: Exchange, rates: BenchmarkRates | None) -> ExchangeOut:
    out = ExchangeOut.model_validate(exchange)
    quote = benchmark_rate(exchange, rates) if rates is not None else None
    if quote is not None:
        out.benchmark = Benchmark(
            rate=quote.rate,
            as_of=quote.as_of,
            source=quote.source,
            spread_pct=spread_pct(exchange.effective_rate, quote.rate),
        )
    return out


def _with_benchmark(service: ExchangeService, exchange: Exchange) -> ExchangeOut:
    return _out(exchange, service.benchmark_rates([exchange]))


def _filters(date_from: date | None, date_to: date | None, provider: str | None, currency: str | None) -> Filters:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_from must be on or before date_to")
    return Filters(date_from=date_from, date_to=date_to, provider=provider, currency=currency)


@router.get("/", response_model=list[ExchangeOut])
def list_exchanges(
    db: DbSession,
    date_from: date | None = Query(None, description="Inclusive start date"),
    date_to: date | None = Query(None, description="Inclusive end date"),
    provider: ExchangeProvider | None = Query(None),
    currency: str | None = Query(None, min_length=3, max_length=3, description="Matches either leg"),
) -> list[ExchangeOut]:
    """Exchanges, newest first, each with its Bank of Canada benchmark when CAD<->USD."""
    service = ExchangeService(db)
    exchanges = service.list(_filters(date_from, date_to, provider, currency))
    rates = service.benchmark_rates(exchanges)
    return [_out(e, rates) for e in exchanges]


@router.get("/summary", response_model=ExchangeSummary)
def exchange_summary(
    db: DbSession,
    date_from: date | None = Query(None, description="Inclusive start date"),
    date_to: date | None = Query(None, description="Inclusive end date"),
    provider: ExchangeProvider | None = Query(None),
    currency: str | None = Query(None, min_length=3, max_length=3, description="Matches either leg"),
) -> ExchangeSummary:
    """Per-pair totals, weighted average rate, fees and spread vs the reference rate."""
    return ExchangeSummary(**ExchangeService(db).summary(_filters(date_from, date_to, provider, currency)))


@router.get("/{exchange_id}", response_model=ExchangeOut)
def get_exchange(exchange_id: int, db: DbSession) -> ExchangeOut:
    service = ExchangeService(db)
    try:
        return _with_benchmark(service, service.get(exchange_id))
    except ExchangeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/", response_model=ExchangeOut, status_code=status.HTTP_201_CREATED)
def create_exchange(data: ExchangeCreate, db: DbSession) -> ExchangeOut:
    service = ExchangeService(db)
    try:
        return _with_benchmark(service, service.create(data))
    except InvalidExchange as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{exchange_id}", response_model=ExchangeOut)
def update_exchange(exchange_id: int, data: ExchangeUpdate, db: DbSession) -> ExchangeOut:
    service = ExchangeService(db)
    try:
        return _with_benchmark(service, service.update(exchange_id, data))
    except ExchangeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidExchange as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{exchange_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exchange(exchange_id: int, db: DbSession) -> Response:
    try:
        ExchangeService(db).delete(exchange_id)
    except ExchangeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
