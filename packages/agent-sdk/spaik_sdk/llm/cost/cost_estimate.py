from pydantic import BaseModel, Field


class CostEstimate(BaseModel):
    """A provider-reported charge, never a price-table estimate."""

    cost: float = Field(ge=0, allow_inf_nan=False)
    currency: str = "USD"
    is_estimate: bool = False
    complete: bool = True


class CostSummary(BaseModel):
    totals: dict[str, float]
    complete: bool
    unavailable_invocations: int
