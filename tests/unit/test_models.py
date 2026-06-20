import pytest
from dataclasses import FrozenInstanceError
from datetime import datetime
from researchcache.models import Principal, Policy, Decision, CacheEntry, AuditEvent
from researchcache.models.principal import AnonymousPrincipal


def test_principal():
    principal = Principal(id='anon', type='anonymous', institution=None, api_key_id=None)
    assert principal.id == 'anon'
    assert principal.type == 'anonymous'
    assert principal.institution is None
    assert principal.api_key_id is None
    assert principal == AnonymousPrincipal
    with pytest.raises(FrozenInstanceError):
        principal.id = 'changed'

def test_policy():
    now = datetime.now()
    policy = Policy(object_id='abcdefghijklmnopqrstuvwxyz123456', licence='CC0', access_tier='open', embargo_until=None, captured_at=now)
    assert policy.object_id == 'abcdefghijklmnopqrstuvwxyz123456'
    assert policy.licence == 'CC0'
    assert policy.access_tier == 'open'
    assert policy.embargo_until is None
    assert policy.captured_at == now
    with pytest.raises(FrozenInstanceError):
        policy.licence = 'MIT'

def test_decision():
    now = datetime.now()
    decision = Decision(allowed=True, reason='policy is open', principal_id='anon', object_id='abcdefghijklmnopqrstuvwxyz123456', issued_at=now, token='fake-token-for-testing')
    assert decision.allowed
    assert decision.reason == 'policy is open'
    assert decision.principal_id == 'anon'
    assert decision.object_id == 'abcdefghijklmnopqrstuvwxyz123456'
    assert decision.issued_at == now
    assert decision.token == 'fake-token-for-testing'
    with pytest.raises(FrozenInstanceError):
        decision.allowed = False

def test_cache_entry():
    now = datetime.now()
    policy = Policy(object_id='abcdefghijklmnopqrstuvwxyz123456', licence='CC0', access_tier='open', embargo_until=None,captured_at=now)
    cache_entry = CacheEntry(object_id='abcdefghijklmnopqrstuvwxyz123456', origin_url='https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/GRCh38.fa.gz', content_hash='d4e5f6789012345678901234567890123456789012345678901234567890ab', size_bytes=3100000000, content_type='application/gzip', cached_at=now, last_accessed=now, ttl_seconds=86400, policy=policy)
    assert cache_entry.object_id == 'abcdefghijklmnopqrstuvwxyz123456'
    assert cache_entry.origin_url == 'https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/GRCh38.fa.gz'
    assert cache_entry.content_hash == 'd4e5f6789012345678901234567890123456789012345678901234567890ab'
    assert cache_entry.size_bytes == 3100000000
    assert cache_entry.content_type == 'application/gzip'
    assert cache_entry.cached_at == now
    assert cache_entry.last_accessed == now
    assert cache_entry.ttl_seconds == 86400
    assert cache_entry.policy == policy
    with pytest.raises(FrozenInstanceError):
        cache_entry.object_id = '10'

def test_audit_event():
    now = datetime.now()
    audit_event = AuditEvent(event_id='e1d2c3b4-5678-90ab-cdef-1234567890ab', request_id='f2e3d4c5-6789-01bc-def0-234567890abc', principal_id='anon', object_id='abcdefghijklmnopqrstuvwxyz123456', origin_url='https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/GRCh38.fa.gz', cache_result='miss', decision='allow', bytes_served=3100000000, duration_ms=480000, timestamp=now, client_ip_hash='9f8e7d6c5b4a39281706f5e4d3c2b1a0918f7e6d5c4b3a29180716f5e4d3c2b1')
    assert audit_event.event_id == 'e1d2c3b4-5678-90ab-cdef-1234567890ab'
    assert audit_event.request_id == 'f2e3d4c5-6789-01bc-def0-234567890abc'
    assert audit_event.principal_id == 'anon'
    assert audit_event.object_id == 'abcdefghijklmnopqrstuvwxyz123456'
    assert audit_event.origin_url == 'https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/GRCh38.fa.gz'
    assert audit_event.cache_result == 'miss'
    assert audit_event.decision == 'allow'
    assert audit_event.bytes_served == 3100000000
    assert audit_event.duration_ms == 480000
    assert audit_event.timestamp == now
    assert audit_event.client_ip_hash == '9f8e7d6c5b4a39281706f5e4d3c2b1a0918f7e6d5c4b3a29180716f5e4d3c2b1'
    with pytest.raises(FrozenInstanceError):
        audit_event.bytes_served = 10


