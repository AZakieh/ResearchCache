import hashlib
from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from researchcache.pipeline.stage0_receive import InvalidSchemeError, normalise


def test_normalise_lowercases_and_sorts_query_params():
    a = normalise("HTTPS://Example.COM/Path?b=2&a=1", client_ip="1.2.3.4")
    b = normalise("https://example.com/path?a=1&b=2", client_ip="1.2.3.4")
    assert a.canonical_url == b.canonical_url
    assert a.object_id == b.object_id


def test_normalise_strips_fragment():
    result = normalise("https://example.com/path#section", client_ip="1.2.3.4")
    assert "#" not in result.canonical_url


def test_normalise_rejects_non_https_scheme():
    with pytest.raises(InvalidSchemeError):
        normalise("http://example.com/path", client_ip="1.2.3.4")


def test_normalise_rejects_missing_scheme():
    with pytest.raises(InvalidSchemeError):
        normalise("example.com/path", client_ip="1.2.3.4")


def test_normalise_generates_unique_request_id_and_utc_timestamp():
    a = normalise("https://example.com/path", client_ip="1.2.3.4")
    b = normalise("https://example.com/path", client_ip="1.2.3.4")
    assert a.request_id != b.request_id
    assert isinstance(a.timestamp, datetime)
    assert a.timestamp.tzinfo is not None


def test_normalise_prefers_x_forwarded_for_over_client_ip():
    via_xff = normalise("https://example.com/path", client_ip="9.9.9.9", x_forwarded_for="1.2.3.4")
    direct = normalise("https://example.com/path", client_ip="1.2.3.4")
    assert via_xff.ip_hash == direct.ip_hash


def test_normalise_x_forwarded_for_uses_first_entry_in_chain():
    result = normalise(
        "https://example.com/path",
        client_ip="9.9.9.9",
        x_forwarded_for="1.2.3.4, 5.6.7.8",
    )
    direct = normalise("https://example.com/path", client_ip="1.2.3.4")
    assert result.ip_hash == direct.ip_hash


def test_normalise_object_id_is_sha256_of_canonical_url():
    result = normalise("https://example.com/path", client_ip="1.2.3.4")
    assert result.object_id == hashlib.sha256(result.canonical_url.encode()).hexdigest()


def test_normalise_is_frozen():
    result = normalise("https://example.com/path", client_ip="1.2.3.4")
    with pytest.raises(FrozenInstanceError):
        result.canonical_url = "changed"
