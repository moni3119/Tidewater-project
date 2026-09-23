from uuid import UUID

from pydantic import BaseModel, Field, field_validator


SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "INR"}


class SettlementCreate(BaseModel):
    merchant_id: str = Field(min_length=1, max_length=100)
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper()

        if value not in SUPPORTED_CURRENCIES:
            raise ValueError("Unsupported currency")

        return value


class SettlementResponse(BaseModel):
    id: UUID
    merchant_id: str
    amount_minor: int
    currency: str
    status: str
    idempotency_key: str