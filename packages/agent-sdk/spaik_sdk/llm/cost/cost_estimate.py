from dataclasses import dataclass


@dataclass
class CostEstimate:
    cost: float
    currency: str
    is_estimate: bool
