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
        decision.allowed = True


