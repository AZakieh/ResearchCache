from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    principal_id: str
    object_id: str
    issued_at: datetime
    token: str