"""Resumo em linguagem simples para o cuidador, com LLM opcional.

O LLM NÃO é obrigatório. Sem chave configurada, ou se a chamada falhar, voltar
vazia ou vier inválida, o robô usa um resumo por template. Só dados agregados e
já mascarados são enviados (nunca o texto livre do cidadão).

Funciona com qualquer API compatível com o formato OpenAI /chat/completions:
Groq (camada gratuita), Ollama local (http://localhost:11434/v1) etc.
"""
from __future__ import annotations

import json
import logging

import requests

from robo.privacidade import contem_dado_pessoal
from robo.resiliencia import ErroDeSistema, com_retry

log = logging.getLogger("robo.llm")

PROMPT_SISTEMA = (
    "Você escreve o resumo semanal do OuviAí para o familiar ou cuidador de uma pessoa idosa com perda auditiva. "
    "Use português do Brasil, tom acolhedor e direto, no máximo 6 frases, sem markdown e sem emojis. "
    "Use SOMENTE os números e fatos do JSON recebido. Não invente nada, não dê diagnóstico médico nem conselho jurídico. "
    "Se houver emergência, comece por ela."
)


def resumo_template(indicadores: dict) -> str:
    partes = [f"Nesta semana o OuviAí registrou {indicadores['eventos_validos']} sons válidos "
              f"({indicadores['campainhas']} de campainha e {indicadores['batidas']} de batida na porta)."]
    if indicadores["emergencias"]:
        partes.insert(0, f"Atenção: {indicadores['emergencias']} pedido(s) com sinal de emergência. Confira a aba Pedidos.")
    if indicadores["alertas_altos"]:
        partes.append(f"Houve {indicadores['alertas_altos']} alerta(s) de prioridade alta, veja a aba Alertas.")
    partes.append(f"Foram {indicadores['pedidos']} pedidos de orientação, o tema mais comum foi "
                  f"{indicadores['tema_principal'].replace('_', ' ')}.")
    if indicadores["revisao_humana"]:
        partes.append(f"{indicadores['revisao_humana']} item(ns) precisam de uma olhada humana.")
    return " ".join(partes)


def gerar_resumo(cfg, indicadores: dict) -> tuple[str, str]:
    """Retorna (texto, origem) onde origem é 'llm' ou 'template'."""
    if not (cfg.llm_api_url and cfg.llm_api_key):
        return resumo_template(indicadores), "template"

    @com_retry(tentativas=2, espera_inicial=2.0)
    def chamar() -> str:
        try:
            resp = requests.post(
                cfg.llm_api_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {cfg.llm_api_key}"},
                json={"model": cfg.llm_modelo, "temperature": 0.2, "max_tokens": 300,
                      "messages": [{"role": "system", "content": PROMPT_SISTEMA},
                                   {"role": "user", "content": json.dumps(indicadores, ensure_ascii=False)}]},
                timeout=cfg.regras["rede"]["timeout_s"] * 2,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, ValueError) as erro:
            raise ErroDeSistema(f"LLM indisponível: {erro}") from erro

    try:
        texto = (chamar() or "").strip()
    except ErroDeSistema as erro:
        log.warning("%s. Caminho seguro: resumo por template.", erro)
        return resumo_template(indicadores), "template"

    # Validação da resposta: vazia, longa demais, com markdown ou com dado pessoal é descartada
    if not texto or len(texto) > 1200 or "**" in texto or "#" in texto or contem_dado_pessoal(texto):
        log.warning("Resposta do LLM inválida (vazia/longa/formatada/dado pessoal). Usando template.")
        return resumo_template(indicadores), "template"
    return texto, "llm"
