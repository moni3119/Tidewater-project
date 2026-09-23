from uuid import UUID

from psycopg.types.json import Jsonb

from .db import get_connection


def create_settlement(
    settlement_id: UUID,
    merchant_id: str,
    amount_minor: int,
    currency: str,
    idempotency_key: str,
):
    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO settlements (
                        id,
                        merchant_id,
                        amount_minor,
                        currency,
                        idempotency_key,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, 'PENDING')
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING *
                    """,
                    (
                        settlement_id,
                        merchant_id,
                        amount_minor,
                        currency,
                        idempotency_key,
                    ),
                )

                settlement = cur.fetchone()

                if settlement is None:
                    cur.execute(
                        """
                        SELECT *
                        FROM settlements
                        WHERE idempotency_key = %s
                        """,
                        (idempotency_key,),
                    )

                    settlement = cur.fetchone()

                    if (
                        settlement["merchant_id"] != merchant_id
                        or settlement["amount_minor"] != amount_minor
                        or settlement["currency"] != currency
                    ):
                        raise ValueError(
                            "Idempotency key was already used with different data"
                        )

                    return settlement

                cur.execute(
                    """
                    INSERT INTO outbox_events (
                        event_type,
                        aggregate_id,
                        payload
                    )
                    VALUES (
                        'settlement.created',
                        %s,
                        %s
                    )
                    """,
                    (
                        settlement_id,
                        Jsonb(
                            {
                                "settlement_id": str(settlement_id),
                                "merchant_id": merchant_id,
                                "amount_minor": amount_minor,
                                "currency": currency,
                            }
                        ),
                    ),
                )

                return settlement


def get_settlement_by_idempotency_key(idempotency_key: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM settlements
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )

            return cur.fetchone()


def get_settlement(settlement_id: UUID):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM settlements
                WHERE id = %s
                """,
                (settlement_id,),
            )

            return cur.fetchone()