import hashlib
import hmac
import json
from datetime import datetime, timezone

from researchcache.config import get_settings
from researchcache.models.decision import Decision
from researchcache.models.policy import Policy
from researchcache.models.principal import Principal

# Decision tokens are scoped to a single request's duration, not a session -
# a 60s window is generous for that while keeping a stolen/logged token
# useless shortly after issuance.
TOKEN_MAX_AGE_SECONDS = 60


class SecurityError(Exception):
    """Raised when a Decision token is missing, tampered with, or expired."""


def _sign(*, allowed: bool, principal_id: str, object_id: str, issued_at: datetime) -> str:
    payload = json.dumps(
        {
            "allowed": allowed,
            "principal_id": principal_id,
            "object_id": object_id,
            "issued_at": issued_at.isoformat(),
        },
        sort_keys=True,
    )
    secret = get_settings().DECISION_HMAC_SECRET
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def decide(principal: Principal, policy: Policy) -> Decision:
    """The only place an ALLOW/DENY access decision is ever made.

    DENY is a normal outcome, not an error - it's returned as a Decision
    like ALLOW, never raised.
    """
    allowed = policy.access_tier == "open"
    reason = "open access" if allowed else f"access_tier '{policy.access_tier}' is not open"
    issued_at = datetime.now(timezone.utc)

    token = _sign(
        allowed=allowed,
        principal_id=principal.id,
        object_id=policy.object_id,
        issued_at=issued_at,
    )

    return Decision(
        allowed=allowed,
        reason=reason,
        principal_id=principal.id,
        object_id=policy.object_id,
        issued_at=issued_at,
        token=token,
    )


def verify_decision(decision: Decision) -> None:
    """Raise SecurityError if a Decision's token was tampered with or has expired."""
    expected = _sign(
        allowed=decision.allowed,
        principal_id=decision.principal_id,
        object_id=decision.object_id,
        issued_at=decision.issued_at,
    )
    if not hmac.compare_digest(decision.token, expected):
        raise SecurityError("Decision token invalid or tampered")

    age = datetime.now(timezone.utc) - decision.issued_at
    if age.total_seconds() > TOKEN_MAX_AGE_SECONDS:
        raise SecurityError("Decision token expired")
