from dataclasses import dataclass
from typing import Literal
from datetime import datetime

@dataclass(frozen=True)
class Policy:
    object_id: str
    licence: str
    access_tier: Literal['open', 'restricted', 'embargoed']
    embargo_until: datetime | None
    captured_at: datetime