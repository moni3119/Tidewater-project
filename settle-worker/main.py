import os
import time

import httpx
import psycopg
import redis


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://settle:settle_dev_password@postgres:5432/settle",
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)

BANK_URL = os.getenv(
    "BANK_URL",
    "http://mock-bank:8001",
)

STREAM_NAME = "settlements"
GROUP_NAME = "settle-workers"
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "worker-1")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def get_db_connection():
    return psycopg.connect(DATABASE_URL)


def connect_redis():
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )


def ensure_consumer_group(r):
    try:
        r.xgroup_create(
            STREAM_NAME,
            GROUP_NAME,
            id="0",
            mkstream=True,
        )
    except redis.exceptions.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def publish_outbox_events(r):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, aggregate_id, payload
                FROM outbox_events
                WHERE published_at IS NULL
                ORDER BY id
                LIMIT 100
                """
            )

            events = cur.fetchall()

            for event_id, aggregate_id, payload in events:
                r.xadd(
                    STREAM_NAME,
                    {
                        "event_id": str(event_id),
                        "settlement_id": str(aggregate_id),
                    },
                )

                cur.execute(
                    """
                    UPDATE outbox_events
                    SET published_at = NOW()
                    WHERE id = %s
                    """,
                    (event_id,),
                )

        conn.commit()


def process_message(r, message_id, fields):
    settlement_id = fields["settlement_id"]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    merchant_id,
                    amount_minor,
                    currency,
                    status
                FROM settlements
                WHERE id = %s
                """,
                (settlement_id,),
            )

            settlement = cur.fetchone()

    if not settlement:
        print(f"Settlement not found: {settlement_id}")
        r.xack(STREAM_NAME, GROUP_NAME, message_id)
        return

    settlement_id, merchant_id, amount_minor, currency, current_status = settlement

    if current_status == "COMPLETED":
        r.xack(STREAM_NAME, GROUP_NAME, message_id)
        print(f"Already completed: {settlement_id}")
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(
                f"Processing settlement {settlement_id}, "
                f"attempt {attempt}/{MAX_RETRIES}"
            )

            response = httpx.post(
                f"{BANK_URL}/payouts",
                json={
                    "settlement_id": str(settlement_id),
                    "merchant_id": merchant_id,
                    "amount_minor": amount_minor,
                    "currency": currency,
                    "idempotency_key": str(settlement_id),
                },
                timeout=5,
            )

            response.raise_for_status()

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE settlements
                        SET status = 'COMPLETED',
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (settlement_id,),
                    )

                conn.commit()

            r.xack(STREAM_NAME, GROUP_NAME, message_id)

            print(f"Settlement completed: {settlement_id}")
            return

        except Exception as exc:
            print(
                f"Attempt {attempt} failed for "
                f"{settlement_id}: {exc}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    print(
        f"Settlement failed after {MAX_RETRIES} attempts: "
        f"{settlement_id}"
    )


def main():
    r = connect_redis()

    ensure_consumer_group(r)

    print("settle-worker started")

    while True:
        try:
            publish_outbox_events(r)

            messages = r.xreadgroup(
                GROUP_NAME,
                CONSUMER_NAME,
                {STREAM_NAME: ">"},
                count=10,
                block=5000,
            )

            for _, entries in messages:
                for message_id, fields in entries:
                    process_message(
                        r,
                        message_id,
                        fields,
                    )

        except redis.exceptions.TimeoutError:
            continue

        except Exception as exc:
            print(f"Worker error: {exc}")
            time.sleep(2)


if __name__ == "__main__":
    main()