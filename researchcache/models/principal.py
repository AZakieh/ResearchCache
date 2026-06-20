from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Principal:
    id: str
    type: Literal['anonymous', 'api_key']
    institution: str | None
    api_key_id: str | None

AnonymousPrincipal = Principal(id='anon', type='anonymous', institution=None, api_key_id=None)