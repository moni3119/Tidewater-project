from uuid import UUID

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel


DATABASE_URL = (
    "postgresql://settle:settle_dev_password@postgres:5432/settle"
)

app = FastAPI(title="Mock Bank")


class PayoutRequest(BaseModel):
    settlement_id: UUID
    merchant_id: str
    amount_minor: int
    currency: str
    idempotency_key: UUID


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/payouts")
def create_payout(request: PayoutRequest):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM bank_payouts
                WHERE idempotency_key = %s
                """,
                (request.idempotency_key,),
            )

            existing = cur.fetchone()

            if existing:
                return {
                    "status": "already_processed",
                    "settlement_id": str(existing[2]),
                }

            cur.execute(
                """
                INSERT INTO bank_payouts (
                    idempotency_key,
                    settlement_id,
                    merchant_id,
                    amount_minor,
                    currency
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    request.idempotency_key,
                    request.settlement_id,
                    request.merchant_id,
                    request.amount_minor,
                    request.currency,
                ),
            )

            payout_id = cur.fetchone()[0]

            conn.commit()

            return {
                "status": "processed",
                "payout_id": payout_id,
                "settlement_id": str(request.settlement_id),
            }