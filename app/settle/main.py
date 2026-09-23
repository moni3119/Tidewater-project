from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, status

from .db import check_database
from .repository import (
    create_settlement,
    get_settlement,
    get_settlement_by_idempotency_key,
)
from .schemas import SettlementCreate, SettlementResponse


app = FastAPI(title="Tidewater Settlement API")


@app.get("/healthz")
def healthz():
    # Liveness only checks whether the API process is alive.
    # It does not depend on PostgreSQL.
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    # Readiness checks PostgreSQL availability.
    # A database problem removes the pod from traffic
    # instead of causing a container restart.
    if not check_database():
        raise HTTPException(
            status_code=503,
            detail="database unavailable",
        )

    return {"status": "ready"}


@app.get("/")
def root():
    return {"service": "settle-api"}


@app.post(
    "/settlements",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_settlement(
    request: SettlementCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    existing = get_settlement_by_idempotency_key(idempotency_key)

    if existing:
        same_request = (
            existing["merchant_id"] == request.merchant_id
            and existing["amount_minor"] == request.amount_minor
            and existing["currency"] == request.currency
        )

        if not same_request:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key was already used with different data",
            )

        return existing

    settlement_id = uuid4()

    settlement = create_settlement(
        settlement_id=settlement_id,
        merchant_id=request.merchant_id,
        amount_minor=request.amount_minor,
        currency=request.currency,
        idempotency_key=idempotency_key,
    )

    return settlement


@app.get(
    "/settlements/{settlement_id}",
    response_model=SettlementResponse,
)
def get_settlement_by_id(settlement_id: UUID):
    settlement = get_settlement(settlement_id)

    if not settlement:
        raise HTTPException(
            status_code=404,
            detail="Settlement not found",
        )

    return settlement