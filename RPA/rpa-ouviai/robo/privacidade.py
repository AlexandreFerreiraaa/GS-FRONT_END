"""Mascaramento de dados pessoais (LGPD).

Todo texto livre do cidadão passa por aqui ANTES de ser salvo em relatório,
enviado por e-mail ou mandado para qualquer API de LLM.
"""
from __future__ import annotations

import re

PADROES: list[tuple[str, re.Pattern]] = [
    ("[EMAIL]", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("[CPF]", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("[CEP]", re.compile(r"\b\d{5}-\d{3}\b")),
    ("[TELEFONE]", re.compile(r"(?:\+?55\s?)?\(?\b\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b")),
    ("[NIS]", re.compile(r"\b\d{3}\.?\d{5}\.?\d{2}-?\d\b")),
]


def mascarar(texto: str) -> str:
    if not texto:
        return texto
    for marcador, padrao in PADROES:
        texto = padrao.sub(marcador, texto)
    return texto


def contem_dado_pessoal(texto: str) -> bool:
    return mascarar(texto) != texto
