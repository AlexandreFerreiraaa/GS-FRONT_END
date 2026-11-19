"""Configuração central do robô.

Tudo que muda entre ambientes (chaves, SMTP, modo offline) vem de variáveis de
ambiente ou do arquivo .env. Nada sensível fica no código ou no repositório.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv é opcional; sem ele, usamos só o ambiente
    def load_dotenv(*_args, **_kwargs):
        return False

RAIZ = Path(__file__).resolve().parent.parent


def _bool(nome: str, padrao: bool = False) -> bool:
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


@dataclass
class Config:
    raiz: Path = RAIZ
    modo_offline: bool = False
    demo_falhas: bool = False

    # Pastas
    dir_entrada: Path = field(default_factory=lambda: RAIZ / "dados" / "entrada")
    dir_saida: Path = field(default_factory=lambda: RAIZ / "saida")
    dir_logs: Path = field(default_factory=lambda: RAIZ / "logs")
    dir_estado: Path = field(default_factory=lambda: RAIZ / "estado")
    dir_base: Path = field(default_factory=lambda: RAIZ / "saida" / "base_conhecimento")
    arquivo_modelo: Path = field(default_factory=lambda: RAIZ / "estado" / "modelo_triagem.joblib")
    arquivo_treino: Path = field(default_factory=lambda: RAIZ / "dados" / "treino" / "pedidos_rotulados.csv")

    # Integrações opcionais (todas com caminho seguro quando ausentes)
    eventos_api_url: str | None = None
    llm_api_url: str | None = None
    llm_api_key: str | None = None
    llm_modelo: str = "llama-3.1-8b-instant"
    smtp_host: str | None = None
    smtp_porta: int = 587
    smtp_usuario: str | None = None
    smtp_senha: str | None = None
    email_remetente: str = "robo-ouviai@example.org"
    email_cuidador: str = "cuidador@example.org"

    fontes: list[dict] = field(default_factory=list)
    grupo: dict = field(default_factory=dict)
    regras: dict = field(default_factory=dict)

    @classmethod
    def carregar(cls, offline: bool | None = None, demo_falhas: bool | None = None) -> "Config":
        load_dotenv(RAIZ / ".env")
        cfg = cls(
            modo_offline=_bool("ROBO_OFFLINE") if offline is None else offline,
            demo_falhas=_bool("ROBO_DEMO_FALHAS") if demo_falhas is None else demo_falhas,
            eventos_api_url=os.getenv("EVENTOS_API_URL") or None,
            llm_api_url=os.getenv("LLM_API_URL") or None,
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_modelo=os.getenv("LLM_MODELO", "llama-3.1-8b-instant"),
            smtp_host=os.getenv("SMTP_HOST") or None,
            smtp_porta=int(os.getenv("SMTP_PORTA", "587")),
            smtp_usuario=os.getenv("SMTP_USUARIO") or None,
            smtp_senha=os.getenv("SMTP_SENHA") or None,
            email_remetente=os.getenv("EMAIL_REMETENTE", "robo-ouviai@example.org"),
            email_cuidador=os.getenv("EMAIL_CUIDADOR", "cuidador@example.org"),
        )
        fontes = json.loads((RAIZ / "config" / "fontes.json").read_text(encoding="utf-8"))["fontes"]
        cfg.fontes = [f for f in fontes if cfg.demo_falhas or not f.get("somente_demo_falhas")]
        arquivo_grupo = RAIZ / "config" / "grupo.json"
        cfg.grupo = json.loads(arquivo_grupo.read_text(encoding="utf-8")) if arquivo_grupo.exists() else {}
        cfg.regras = json.loads((RAIZ / "config" / "regras.json").read_text(encoding="utf-8"))
        for pasta in (cfg.dir_saida, cfg.dir_logs, cfg.dir_estado, cfg.dir_base):
            pasta.mkdir(parents=True, exist_ok=True)
        return cfg
