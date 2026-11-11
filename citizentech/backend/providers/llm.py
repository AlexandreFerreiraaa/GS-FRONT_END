"""Único ponto de acesso ao provedor de LLM. Trocar de provedor = mexer só aqui."""
import os
from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=30)
    return _client


def completar(system: str, user: str) -> str:
    resp = _get_client().messages.create(
        model=os.getenv("LLM_MODEL", "claude-sonnet-5-5"),
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text
