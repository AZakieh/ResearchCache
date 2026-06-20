from dataclasses import dataclass
from typing import Literal
from datetime import datetime

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    request_id: str
    principal_id: str
    object_id: str
    origin_url: str
    cache_result: Literal['hit', 'miss', 'error']
    decision: Literal['allow', 'deny']
    bytes_served: int
    duration_ms: int
    timestamp: datetime
    client_ip_hash: str