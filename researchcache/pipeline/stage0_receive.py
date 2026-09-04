import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from researchcache.config import get_settings


class InvalidSchemeError(ValueError):
    """Raised when the target URL's scheme is not https."""


@dataclass(frozen=True)
class NormalisedRequest:
    canonical_url: str
    object_id: str
    request_id: str
    timestamp: datetime
    ip_hash: str


def _canonicalise_url(url: str) -> str:
    parsed = urlparse(url.lower())
    if parsed.scheme != "https":
        raise InvalidSchemeError(f"URL scheme must be https, got '{parsed.scheme or 'none'}'")
    sorted_query = urlencode(sorted(parse_qsl(parsed.query)))
    return urlunparse(parsed._replace(query=sorted_query, fragment=""))


def _daily_salt() -> str:
    # Rotates every 24h so events can be correlated within a day without
    # retaining long-term IP-linkable state (see security requirements 5.7).
    today = datetime.now(timezone.utc).date().isoformat()
    secret = get_settings().DECISION_HMAC_SECRET
    return hashlib.sha256(f"{secret}:{today}".encode()).hexdigest()


def _hash_ip(client_ip: str) -> str:
    return hashlib.sha256(f"{client_ip}{_daily_salt()}".encode()).hexdigest()


def normalise(url: str, client_ip: str, x_forwarded_for: str | None = None) -> NormalisedRequest:
    canonical_url = _canonicalise_url(url)
    object_id = hashlib.sha256(canonical_url.encode()).hexdigest()
    effective_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else client_ip

    return NormalisedRequest(
        canonical_url=canonical_url,
        object_id=object_id,
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        ip_hash=_hash_ip(effective_ip),
    )
