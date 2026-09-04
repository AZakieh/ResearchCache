from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from researchcache.models.decision import Decision
from researchcache.models.policy import Policy
from researchcache.models.principal import Principal
from researchcache.pipeline.stage4_decision import (
    TOKEN_MAX_AGE_SECONDS,
    SecurityError,
    _sign,
    decide,
    verify_decision,
)

PRINCIPAL = Principal(id="anon", type="anonymous", institution=None, api_key_id=None)


def _policy(access_tier: str, object_id: str = "obj-1") -> Policy:
    return Policy(
        object_id=object_id,
        licence="cc0",
        access_tier=access_tier,
        embargo_until=None,
        captured_at=datetime.now(timezone.utc),
    )


def test_decide_allows_open_access_policy():
    decision = decide(PRINCIPAL, _policy("open"))
    assert decision.allowed is True
    assert decision.principal_id == "anon"
    assert decision.object_id == "obj-1"
    assert decision.token
    verify_decision(decision)  # does not raise


def test_decide_denies_non_open_policy_without_raising():
    decision = decide(PRINCIPAL, _policy("restricted"))
    assert decision.allowed is False
    assert "restricted" in decision.reason


def test_decide_denies_embargoed_policy_without_raising():
    decision = decide(PRINCIPAL, _policy("embargoed"))
    assert decision.allowed is False


def test_tampered_field_raises_security_error():
    decision = decide(PRINCIPAL, _policy("open"))
    tampered = replace(decision, object_id="a-different-object")
    with pytest.raises(SecurityError):
        verify_decision(tampered)


def test_tampered_token_raises_security_error():
    decision = decide(PRINCIPAL, _policy("open"))
    tampered = replace(decision, token="0" * 64)
    with pytest.raises(SecurityError):
        verify_decision(tampered)


def test_expired_token_raises_security_error():
    old_issued_at = datetime.now(timezone.utc) - timedelta(seconds=TOKEN_MAX_AGE_SECONDS + 1)
    token = _sign(
        allowed=True,
        principal_id=PRINCIPAL.id,
        object_id="obj-1",
        issued_at=old_issued_at,
    )
    decision = Decision(
        allowed=True,
        reason="open access",
        principal_id=PRINCIPAL.id,
        object_id="obj-1",
        issued_at=old_issued_at,
        token=token,
    )
    with pytest.raises(SecurityError):
        verify_decision(decision)


def test_decision_is_frozen():
    decision = decide(PRINCIPAL, _policy("open"))
    with pytest.raises(FrozenInstanceError):
        decision.allowed = False
