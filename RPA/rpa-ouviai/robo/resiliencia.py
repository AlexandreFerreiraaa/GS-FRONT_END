"""Tratamento de falhas no estilo REFramework.

- ErroDeNegocio: o dado está errado (linha inválida, campo faltando). Não adianta
  tentar de novo, o item vai para quarentena ou revisão humana.
- ErroDeSistema: algo de fora falhou (site fora do ar, timeout, API). Vale tentar
  de novo com espera crescente, e se continuar falhando, seguimos pelo caminho seguro.
"""
from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")
log = logging.getLogger("robo.resiliencia")


class ErroDeNegocio(Exception):
    """Dado inválido ou fora da regra. Não deve ser repetido."""


class ErroDeSistema(Exception):
    """Falha de infraestrutura. Pode ser repetida."""


def com_retry(tentativas: int = 3, espera_inicial: float = 1.0, fator: float = 2.0,
              excecoes: tuple[type[BaseException], ...] = (ErroDeSistema,),
              dormir: Callable[[float], None] = time.sleep):
    """Repete a função em caso de ErroDeSistema com backoff exponencial."""

    def decorador(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def envelope(*args, **kwargs) -> T:
            espera = espera_inicial
            for tentativa in range(1, tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except excecoes as erro:
                    if tentativa == tentativas:
                        log.error("%s falhou após %d tentativas: %s", func.__name__, tentativas, erro)
                        raise
                    log.warning("%s falhou (tentativa %d/%d): %s. Nova tentativa em %.1fs",
                                func.__name__, tentativa, tentativas, erro, espera)
                    dormir(espera)
                    espera *= fator
            raise RuntimeError("inalcançável")

        return envelope

    return decorador


class Etapa:
    """Context manager que cronometra uma etapa e registra status no relatório de execução.

    Uma falha inesperada dentro da etapa é registrada e NÃO derruba o robô inteiro:
    as próximas etapas continuam com o que estiver disponível.
    """

    def __init__(self, nome: str, relatorio: dict):
        self.nome = nome
        self.relatorio = relatorio
        self.inicio = 0.0
        self.registro: dict = {"etapa": nome, "status": "ok", "detalhes": {}}

    def __enter__(self) -> dict:
        self.inicio = time.perf_counter()
        log.info("▶ Etapa: %s", self.nome)
        return self.registro["detalhes"]

    def __exit__(self, tipo, erro, _tb) -> bool:
        self.registro["duracao_s"] = round(time.perf_counter() - self.inicio, 3)
        if erro is not None:
            self.registro["status"] = "falhou"
            self.registro["erro"] = f"{tipo.__name__}: {erro}"
            log.exception("Etapa '%s' falhou, seguindo pelo caminho seguro", self.nome)
        elif self.registro["detalhes"].get("avisos"):
            self.registro["status"] = "ok_com_avisos"
        self.relatorio.setdefault("etapas", []).append(self.registro)
        log.info("■ %s: %s (%.2fs)", self.nome, self.registro["status"], self.registro["duracao_s"])
        return True  # suprime a exceção: o robô segue
