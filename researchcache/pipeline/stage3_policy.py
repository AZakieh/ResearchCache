import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from researchcache.models.policy import Policy
from researchcache.store.db import PolicyORM

# Metadata fetches get their own short timeout, separate from the much longer
# origin-file-fetch timeouts used in stage6 — a slow licence lookup must not
# hold up the request.
METADATA_FETCH_TIMEOUT = httpx.Timeout(5.0)

_ZENODO_RECORD_RE = re.compile(r"/records?/(\d+)")


async def _fetch_zenodo_licence(origin_url: str) -> str | None:
    match = _ZENODO_RECORD_RE.search(urlparse(origin_url).path)
    if match is None:
        return None

    record_id = match.group(1)
    try:
        async with httpx.AsyncClient(timeout=METADATA_FETCH_TIMEOUT) as client:
            response = await client.get(f"https://zenodo.org/api/records/{record_id}")
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    return data.get("metadata", {}).get("license", {}).get("id") or None


# Only origins with a known, concrete metadata API get a fetcher. Anything
# else (including EBI, which has no single documented metadata endpoint)
# falls through to the 'unknown' default below.
_LICENCE_FETCHERS = {
    "zenodo.org": _fetch_zenodo_licence,
}


async def lookup_policy(object_id: str, origin_url: str, session: AsyncSession) -> Policy:
    host = urlparse(origin_url).hostname or ""
    fetcher = _LICENCE_FETCHERS.get(host)
    licence = await fetcher(origin_url) if fetcher else None

    policy = Policy(
        object_id=object_id,
        licence=licence or "unknown",
        access_tier="open",
        embargo_until=None,
        captured_at=datetime.now(timezone.utc),
    )

    await _store_policy(policy, origin_url, session)
    return policy


async def _store_policy(policy: Policy, origin_url: str, session: AsyncSession) -> None:
    stmt = insert(PolicyORM).values(
        object_id=policy.object_id,
        licence=policy.licence,
        access_tier=policy.access_tier,
        embargo_until=policy.embargo_until,
        captured_at=policy.captured_at,
        origin_url=origin_url,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[PolicyORM.object_id],
        set_={
            "licence": stmt.excluded.licence,
            "access_tier": stmt.excluded.access_tier,
            "embargo_until": stmt.excluded.embargo_until,
            "captured_at": stmt.excluded.captured_at,
            "origin_url": stmt.excluded.origin_url,
        },
    )
    await session.execute(stmt)
    await session.commit()
