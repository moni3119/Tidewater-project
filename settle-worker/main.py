import json
import os
import time
from datetime import datetime, timezone

import httpx
import psycopg
import redis
from prometheus_client import Counter, Gauge, start_http_server


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

METRICS_PORT = int(os.getenv("METRICS_PORT", "8001"))

STREAM_NAME = "settlements"
GROUP_NAME = "settle-workers"
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "worker-1")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
PENDING_CLAIM_IDLE_MS = 30000
CLAIM_COUNT = 10


# -----------------------------
# Prometheus metrics
# -----------------------------

WORKER_MESSAGES_PROCESSED_TOTAL = Counter(
    "tidewater_worker_messages_processed_total",
    "Total settlement messages successfully processed",
)

WORKER_MESSAGES_FAILED_TOTAL = Counter(
    "tidewater_worker_messages_failed_total",
    "Total settlement messages that failed after all retries",
)

WORKER_MESSAGE_RETRIES_TOTAL = Counter(
    "tidewater_worker_message_retries_total",
    "Total worker retry attempts",
)

WORKER_MESSAGES_RECOVERED_TOTAL = Counter(
    "tidewater_worker_messages_recovered_total",
    "Total pending messages recovered with XAUTOCLAIM",
)

WORKER_ERRORS_TOTAL = Counter(
    "tidewater_worker_errors_total",
    "Total worker-level errors",
)

WORKER_ACTIVE = Gauge(
    "tidewater_worker_active",
    "Whether the worker process is running",
)

SETTLEMENT_PENDING_AGE_SECONDS = Gauge(
    "tidewater_settlement_pending_age_seconds",
    "Age in seconds of the oldest pending settlement",
)


# -----------------------------
# Structured JSON logging
# -----------------------------

def log_event(event, **fields):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "settle-worker",
        "event": event,
    }

    record.update(fields)

    print(json.dumps(record), flush=True)


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


def update_pending_age_metric():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXTRACT(
                        EPOCH FROM (NOW() - MIN(created_at))
                    )
                    FROM settlements
                    WHERE status = 'PENDING'
                    """
                )

                result = cur.fetchone()

                if result and result[0] is not None:
                    SETTLEMENT_PENDING_AGE_SECONDS.set(float(result[0]))
                else:
                    SETTLEMENT_PENDING_AGE_SECONDS.set(0)

    except Exception as exc:
        WORKER_ERRORS_TOTAL.inc()

        log_event(
            "pending_age_metric_error",
            error=str(exc),
        )


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
                correlation_id = None

                if payload:
                    correlation_id = payload.get("correlation_id")

                message_fields = {
                    "event_id": str(event_id),
                    "settlement_id": str(aggregate_id),
                }

                if correlation_id:
                    message_fields["correlation_id"] = correlation_id

                r.xadd(
                    STREAM_NAME,
                    message_fields,
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


def recover_pending_messages(r):
    try:
        result = r.xautoclaim(
            STREAM_NAME,
            GROUP_NAME,
            CONSUMER_NAME,
            min_idle_time=PENDING_CLAIM_IDLE_MS,
            start_id="0-0",
            count=CLAIM_COUNT,
        )

        messages = result[1]

        for message_id, fields in messages:
            WORKER_MESSAGES_RECOVERED_TOTAL.inc()

            log_event(
                "message_recovered",
                message_id=message_id,
                settlement_id=fields.get("settlement_id"),
                correlation_id=fields.get("correlation_id"),
            )

            process_message(
                r,
                message_id,
                fields,
            )

    except redis.exceptions.ResponseError as exc:
        WORKER_ERRORS_TOTAL.inc()

        log_event(
            "pending_message_recovery_error",
            error=str(exc),
        )


def process_message(r, message_id, fields):
    settlement_id = fields["settlement_id"]
    correlation_id = fields.get("correlation_id")

    base_log_fields = {
        "message_id": message_id,
        "settlement_id": settlement_id,
        "correlation_id": correlation_id,
    }

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
        WORKER_ERRORS_TOTAL.inc()

        log_event(
            "settlement_not_found",
            **base_log_fields,
        )

        r.xack(
            STREAM_NAME,
            GROUP_NAME,
            message_id,
        )

        return

    (
        settlement_id,
        merchant_id,
        amount_minor,
        currency,
        current_status,
    ) = settlement

    if current_status == "COMPLETED":
        WORKER_MESSAGES_PROCESSED_TOTAL.inc()

        r.xack(
            STREAM_NAME,
            GROUP_NAME,
            message_id,
        )

        log_event(
            "settlement_already_completed",
            **base_log_fields,
        )

        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log_event(
                "settlement_processing",
                **base_log_fields,
                attempt=attempt,
                max_attempts=MAX_RETRIES,
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

            r.xack(
                STREAM_NAME,
                GROUP_NAME,
                message_id,
            )

            WORKER_MESSAGES_PROCESSED_TOTAL.inc()

            log_event(
                "settlement_completed",
                **base_log_fields,
                attempt=attempt,
            )

            return

        except Exception as exc:
            WORKER_ERRORS_TOTAL.inc()

            log_event(
                "settlement_attempt_failed",
                **base_log_fields,
                attempt=attempt,
                error_type=type(exc).__name__,
                error=str(exc),
            )

            if attempt < MAX_RETRIES:
                WORKER_MESSAGE_RETRIES_TOTAL.inc()

                log_event(
                    "settlement_retry",
                    **base_log_fields,
                    next_attempt=attempt + 1,
                )

                time.sleep(RETRY_DELAY_SECONDS)

    WORKER_MESSAGES_FAILED_TOTAL.inc()

    log_event(
        "settlement_failed",
        **base_log_fields,
        attempts=MAX_RETRIES,
    )


def main():
    start_http_server(
        METRICS_PORT,
        addr="0.0.0.0",
    )

    WORKER_ACTIVE.set(1)

    r = connect_redis()

    ensure_consumer_group(r)

    log_event(
        "worker_started",
        metrics_port=METRICS_PORT,
        consumer=CONSUMER_NAME,
    )

    while True:
        try:
            publish_outbox_events(r)

            recover_pending_messages(r)

            update_pending_age_metric()

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
            WORKER_ERRORS_TOTAL.inc()

            log_event(
                "worker_error",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            time.sleep(2)


if __name__ == "__main__":
    main()