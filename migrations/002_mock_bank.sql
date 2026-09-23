CREATE TABLE IF NOT EXISTS bank_payouts (
    id BIGSERIAL PRIMARY KEY,
    idempotency_key UUID NOT NULL UNIQUE,
    settlement_id UUID NOT NULL,
    merchant_id TEXT NOT NULL,
    amount_minor BIGINT NOT NULL,
    currency CHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);