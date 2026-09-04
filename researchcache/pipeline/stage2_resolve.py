from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

from researchcache.config import get_settings
from researchcache.pipeline.stage0_receive import NormalisedRequest


class OriginNotAllowedError(Exception):
    """Raised when the target origin host is not on the allow-list."""


@dataclass(frozen=True)
class ResolvedObject:
    object_id: str
    origin_url: str
    origin_host: str


@lru_cache
def load_allowlist() -> frozenset[str]:
    path = Path(get_settings().ALLOWED_ORIGINS_PATH)
    data = yaml.safe_load(path.read_text()) or {}
    return frozenset(entry["host"].lower() for entry in data.get("origins", []))


def resolve_object(normalised: NormalisedRequest) -> ResolvedObject:
    host = (urlparse(normalised.canonical_url).hostname or "").lower()
    if host not in load_allowlist():
        raise OriginNotAllowedError("Origin is not on the allow-list")

    return ResolvedObject(
        object_id=normalised.object_id,
        origin_url=normalised.canonical_url,
        origin_host=host,
    )
