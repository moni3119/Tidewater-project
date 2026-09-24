import json
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

from .db import check_database
from .repository import (
    create_settlement,
    get_settlement,
    get_settlement_by_idempotency_key,
)
from .schemas import SettlementCreate, SettlementResponse


app = FastAPI(title="Tidewater Settlement API")


# -----------------------------
# Prometheus metrics
# -----------------------------

HTTP_REQUESTS_TOTAL = Counter(
    "tidewater_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "tidewater_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

SETTLEMENTS_CREATED_TOTAL = Counter(
    "tidewater_settlements_created_total",
    "Total number of new settlements created",
)

SETTLEMENTS_IDEMPOTENT_TOTAL = Counter(
    "tidewater_settlements_idempotent_total",
    "Total number of idempotent settlement requests",
)

SETTLEMENT_ERRORS_TOTAL = Counter(
    "tidewater_settlement_errors_total",
    "Total number of settlement errors",
    ["error_type"],
)


# -----------------------------
# Structured JSON logging
# -----------------------------

def log_event(event, **fields):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "settle-api",
        "event": event,
    }

    record.update(fields)

    print(json.dumps(record), flush=True)


# -----------------------------
# Request metrics + correlation
# -----------------------------

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    request.state.request_id = request_id

    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

    finally:
        duration = time.perf_counter() - start_time

        route = request.scope.get("route")

        if route is not None:
            path = route.path
        else:
            path = request.url.path

        status_code = 500

        if "response" in locals():
            status_code = response.status_code

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(duration)

        log_event(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=path,
            status=status_code,
            duration_ms=round(duration * 1000, 2),
        )


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# -----------------------------
# Health checks
# -----------------------------

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if not check_database():
        raise HTTPException(
            status_code=503,
            detail="database unavailable",
        )

    return {"status": "ready"}


# -----------------------------
# API endpoints
# -----------------------------

@app.get("/")
def root():
    return {"service": "settle-api"}


@app.post(
    "/settlements",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_settlement(
    request: Request,
    settlement_request: SettlementCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    request_id = request.state.request_id

    try:
        existing = get_settlement_by_idempotency_key(idempotency_key)

        if existing:
            same_request = (
                existing["merchant_id"] == settlement_request.merchant_id
                and existing["amount_minor"] == settlement_request.amount_minor
                and existing["currency"] == settlement_request.currency
            )

            if not same_request:
                SETTLEMENT_ERRORS_TOTAL.labels(
                    error_type="idempotency_conflict"
                ).inc()

                log_event(
                    "idempotency_conflict",
                    request_id=request_id,
                )

                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key was already used with different data",
                )

            SETTLEMENTS_IDEMPOTENT_TOTAL.inc()

            log_event(
                "settlement_idempotent",
                request_id=request_id,
                settlement_id=str(existing["id"]),
            )

            return existing

        settlement_id = uuid4()

        settlement = create_settlement(
            settlement_id=settlement_id,
            merchant_id=settlement_request.merchant_id,
            amount_minor=settlement_request.amount_minor,
            currency=settlement_request.currency,
            idempotency_key=idempotency_key,
            correlation_id=request_id,
        )

        SETTLEMENTS_CREATED_TOTAL.inc()

        log_event(
            "settlement_created",
            request_id=request_id,
            settlement_id=str(settlement_id),
        )

        return settlement

    except HTTPException:
        raise

    except Exception as exc:
        SETTLEMENT_ERRORS_TOTAL.labels(
            error_type="settlement_creation_error"
        ).inc()

        log_event(
            "settlement_creation_error",
            request_id=request_id,
            error_type=type(exc).__name__,
            error=str(exc),
        )

        raise


@app.get(
    "/settlements/{settlement_id}",
    response_model=SettlementResponse,
)
def get_settlement_by_id(
    settlement_id: UUID,
    request: Request,
):
    settlement = get_settlement(settlement_id)

    if not settlement:
        SETTLEMENT_ERRORS_TOTAL.labels(
            error_type="settlement_not_found"
        ).inc()

        log_event(
            "settlement_not_found",
            request_id=request.state.request_id,
            settlement_id=str(settlement_id),
        )

        raise HTTPException(
            status_code=404,
            detail="Settlement not found",
        )

    return settlement