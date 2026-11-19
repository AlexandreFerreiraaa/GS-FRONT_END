"""Etapa 1: coleta das fontes oficiais e atualização da base de conhecimento.

Tema RPA: web scraping + extração de documentos (HTML e PDF).
Fluxo por fonte: baixar → extrair texto → calcular hash → comparar com a última
execução → se mudou, quebrar em trechos e gravar para o RAG do assistente reindexar.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from robo.resiliencia import ErroDeNegocio, ErroDeSistema, com_retry

log = logging.getLogger("robo.coleta")
CABECALHOS = {"User-Agent": "RoboOuviAi/1.0 (projeto academico FIAP; contato no README)"}


# ---------- extração ----------

def limpar_texto(texto: str) -> str:
    texto = re.sub(r"[ \t\xa0]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n\n", texto)
    return texto.strip()


def extrair_html(html: str, seletor: str | None) -> str:
    sopa = BeautifulSoup(html, "html.parser")
    for lixo in sopa(["script", "style", "nav", "header", "footer", "aside", "form"]):
        lixo.decompose()
    alvo = sopa.select_one(seletor) if seletor else None
    alvo = alvo or sopa.body or sopa
    return limpar_texto(alvo.get_text("\n"))


def extrair_pdf(conteudo: bytes) -> str:
    from pypdf import PdfReader

    leitor = PdfReader(io.BytesIO(conteudo))
    return limpar_texto("\n\n".join(pagina.extract_text() or "" for pagina in leitor.pages))


def dividir_em_trechos(texto: str, alvo_chars: int = 900) -> list[str]:
    """Agrupa parágrafos inteiros até ~alvo_chars, sem cortar frase no meio."""
    trechos, atual = [], ""
    for paragrafo in texto.split("\n\n"):
        if atual and len(atual) + len(paragrafo) > alvo_chars:
            trechos.append(atual.strip())
            atual = ""
        atual += paragrafo + "\n\n"
    if atual.strip():
        trechos.append(atual.strip())
    return trechos


# ---------- download com retry ----------

def criar_baixador(timeout: float, tentativas: int, espera: float, fator: float, sessao=None):
    sessao = sessao or requests.Session()

    @com_retry(tentativas=tentativas, espera_inicial=espera, fator=fator)
    def baixar(url: str) -> tuple[bytes, str]:
        try:
            resp = sessao.get(url, headers=CABECALHOS, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as erro:
            raise ErroDeSistema(f"sem conexão com {url}: {erro.__class__.__name__}") from erro
        if resp.status_code >= 500:
            raise ErroDeSistema(f"HTTP {resp.status_code} em {url}")
        if resp.status_code >= 400:
            raise ErroDeNegocio(f"HTTP {resp.status_code} em {url} (URL errada ou removida)")
        return resp.content, resp.headers.get("Content-Type", "")

    return baixar


# ---------- etapa ----------

def obter_texto(fonte: dict, cfg, baixar) -> tuple[str, str]:
    """Retorna (texto, origem). Tenta online; se falhar, cai no snapshot local."""
    if not cfg.modo_offline:
        try:
            conteudo, tipo = baixar(fonte["url"])
            if "pdf" in tipo or fonte["url"].lower().endswith(".pdf"):
                return extrair_pdf(conteudo), "online"
            return extrair_html(conteudo.decode("utf-8", errors="replace"), fonte.get("seletor")), "online"
        except (ErroDeSistema, ErroDeNegocio) as erro:
            log.warning("Fonte '%s' indisponível online (%s). Usando snapshot local.", fonte["id"], erro)

    snapshot = cfg.raiz / fonte["snapshot"]
    if not snapshot.exists():
        raise ErroDeNegocio(f"sem acesso online e sem snapshot local ({fonte['snapshot']})")
    return extrair_html(snapshot.read_text(encoding="utf-8"), None), "snapshot"


def executar(cfg, estado, detalhes: dict, revisao_humana: list, baixar=None) -> list[dict]:
    rede = cfg.regras["rede"]
    baixar = baixar or criar_baixador(rede["timeout_s"], rede["tentativas"],
                                      rede["espera_inicial_s"], rede["fator_backoff"])
    resultados, para_reindexar = [], []

    for fonte in cfg.fontes:
        registro = {"id": fonte["id"], "titulo": fonte["titulo"], "url": fonte["url"]}
        try:
            texto, origem = obter_texto(fonte, cfg, baixar)
            if len(texto) < 200:
                raise ErroDeNegocio(f"texto extraído muito curto ({len(texto)} caracteres), página mudou de layout?")
            assinatura = hashlib.sha256(texto.encode("utf-8")).hexdigest()
            mudou = estado.hash_fonte(fonte["id"]) != assinatura
            registro.update(origem=origem, caracteres=len(texto), mudou=mudou, status="ok")

            if mudou:
                trechos = dividir_em_trechos(texto)
                gravar_trechos(cfg.dir_base / f"{fonte['id']}.jsonl", fonte, trechos, origem)
                estado.registrar_hash(fonte["id"], assinatura)
                para_reindexar.append(fonte["id"])
                registro["trechos"] = len(trechos)
                log.info("Fonte '%s' (%s) mudou: %d trechos gravados", fonte["id"], origem, len(trechos))
            else:
                log.info("Fonte '%s' sem alteração desde a última execução (nada a reindexar)", fonte["id"])
        except ErroDeNegocio as erro:
            registro.update(status="falhou", erro=str(erro))
            revisao_humana.append({"tipo": "fonte", "item": fonte["id"], "motivo": str(erro),
                                   "acao_sugerida": "Conferir a URL/snapshot e atualizar config/fontes.json"})
            log.error("Fonte '%s' enviada para revisão humana: %s", fonte["id"], erro)
        resultados.append(registro)

    (cfg.dir_base / "reindexar.json").write_text(json.dumps(
        {"gerado_em": datetime.now().isoformat(timespec="seconds"), "fontes": para_reindexar},
        ensure_ascii=False, indent=2), encoding="utf-8")

    detalhes.update(fontes=len(resultados), atualizadas=len(para_reindexar),
                    via_snapshot=sum(r.get("origem") == "snapshot" for r in resultados),
                    falhas=sum(r["status"] == "falhou" for r in resultados))
    if detalhes["falhas"] or (detalhes["via_snapshot"] and not cfg.modo_offline):
        detalhes["avisos"] = True
    return resultados


def gravar_trechos(destino: Path, fonte: dict, trechos: list[str], origem: str) -> None:
    agora = datetime.now().isoformat(timespec="seconds")
    with destino.open("w", encoding="utf-8") as arq:
        for i, trecho in enumerate(trechos):
            arq.write(json.dumps({
                "id": f"{fonte['id']}#{i:03d}", "texto": trecho, "fonte": fonte["titulo"],
                "orgao": fonte["orgao"], "url": fonte["url"], "categoria": fonte["categoria"],
                "coletado_em": agora, "origem": origem,
            }, ensure_ascii=False) + "\n")
