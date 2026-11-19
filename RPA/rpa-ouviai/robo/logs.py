"""Logging do robô: arquivo rotativo (auditoria) + console (acompanhamento)."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMATO = "%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s"


def configurar_logs(dir_logs: Path, run_id: str) -> logging.Logger:
    raiz = logging.getLogger("robo")
    raiz.setLevel(logging.INFO)
    raiz.handlers.clear()

    arquivo = RotatingFileHandler(dir_logs / "robo.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    arquivo.setFormatter(logging.Formatter(FORMATO))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)-7s | %(message)s"))

    raiz.addHandler(arquivo)
    raiz.addHandler(console)
    raiz.info("===== Execução %s iniciada =====", run_id)
    return raiz
