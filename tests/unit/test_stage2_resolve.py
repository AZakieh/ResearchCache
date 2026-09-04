from datetime import datetime, timezone

import pytest

from researchcache.pipeline.stage0_receive import NormalisedRequest, normalise
from researchcache.pipeline.stage2_resolve import (
    OriginNotAllowedError,
    load_allowlist,
    resolve_object,
)


def _normalised(canonical_url: str, object_id: str = "test-object-id") -> NormalisedRequest:
    return NormalisedRequest(
        canonical_url=canonical_url,
        object_id=object_id,
        request_id="test-request-id",
        timestamp=datetime.now(timezone.utc),
        ip_hash="test-ip-hash",
    )


def test_load_allowlist_contains_expected_hosts():
    allowlist = load_allowlist()
    assert "zenodo.org" in allowlist
    assert "ftp.ebi.ac.uk" in allowlist
    assert "ftp.ensembl.org" in allowlist
    assert "ftp.ncbi.nlm.nih.gov" in allowlist
    assert "cds.climate.copernicus.eu" in allowlist
    assert "openneuro.org" in allowlist
    assert "data.mendeley.com" in allowlist


def test_load_allowlist_is_cached():
    assert load_allowlist() is load_allowlist()


def test_resolve_object_returns_resolved_object_for_allowlisted_host():
    normalised = normalise("https://zenodo.org/record/12345/files/data.zip", client_ip="1.2.3.4")
    resolved = resolve_object(normalised)
    assert resolved.origin_host == "zenodo.org"
    assert resolved.origin_url == normalised.canonical_url
    assert resolved.object_id == normalised.object_id


def test_resolve_object_rejects_unlisted_host():
    normalised = normalise("https://evil.example.com/payload", client_ip="1.2.3.4")
    with pytest.raises(OriginNotAllowedError):
        resolve_object(normalised)


def test_resolve_object_is_case_insensitive_regardless_of_upstream_normalisation():
    normalised = _normalised("https://ZENODO.org/record/1")
    resolved = resolve_object(normalised)
    assert resolved.origin_host == "zenodo.org"


def test_resolve_object_rejects_without_any_network_call():
    # No httpx/network client is imported or used by this stage at all, so an
    # unlisted host is rejected purely from the in-memory allow-list.
    normalised = _normalised("https://not-on-the-list.example.org/file")
    with pytest.raises(OriginNotAllowedError):
        resolve_object(normalised)
