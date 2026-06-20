from .policy import Policy
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CacheEntry:
    object_id: str
    origin_url: str
    content_hash: str
    size_bytes: int
    content_type: str
    cached_at: datetime
    last_accessed: datetime
    ttl_seconds: int
    policy: Policy
