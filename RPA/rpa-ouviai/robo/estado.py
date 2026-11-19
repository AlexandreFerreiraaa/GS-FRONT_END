"""Estado persistente entre execuções, usado para idempotência.

Guarda o hash de cada fonte (para só reindexar o que mudou) e o registro de
notificações já enviadas (para nunca mandar o mesmo relatório duas vezes).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger("robo.estado")


class Estado:
    def __init__(self, arquivo: Path):
        self.arquivo = arquivo
        self.dados: dict = {"hashes_fontes": {}, "notificacoes_enviadas": [], "execucoes": []}
        if arquivo.exists():
            try:
                self.dados.update(json.loads(arquivo.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                # Estado corrompido não pode travar o robô: guardamos uma cópia e recomeçamos
                backup = arquivo.with_suffix(".corrompido.json")
                arquivo.rename(backup)
                log.error("Estado corrompido movido para %s; iniciando estado limpo", backup.name)

    def salvar(self) -> None:
        tmp = self.arquivo.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.dados, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.arquivo)  # escrita atômica

    def hash_fonte(self, fonte_id: str) -> str | None:
        return self.dados["hashes_fontes"].get(fonte_id)

    def registrar_hash(self, fonte_id: str, valor: str) -> None:
        self.dados["hashes_fontes"][fonte_id] = valor

    def ja_notificado(self, chave: str) -> bool:
        return chave in self.dados["notificacoes_enviadas"]

    def registrar_notificacao(self, chave: str) -> None:
        self.dados["notificacoes_enviadas"].append(chave)

    def registrar_execucao(self, resumo: dict) -> None:
        self.dados["execucoes"] = (self.dados["execucoes"] + [resumo])[-30:]
