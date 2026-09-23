from dataclasses import dataclass
from datetime import datetime


@dataclass
class Settlement:
    id: str
    merchant_id: str
    amount_minor: int
    currency: str
    idempotency_key: str
    status: str
    created_at: datetime
    updated_at: datetime