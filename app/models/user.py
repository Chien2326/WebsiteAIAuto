from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    # None for demo accounts, which have no credit balance.
    credits_balance: int | None = None
