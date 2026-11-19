"""Etapa 2: ingestão dos eventos sonoros do OuviAí e regras inteligentes de alerta.

Tema RPA: automação de arquivos/planilhas + regras de negócio inteligentes.
Os eventos vêm do classificador de áudio (MFE + CNN do Edge Impulse). O robô lê
os eventos exportados (CSV) ou de uma API, valida linha a linha, separa o que
está inválido em quarentena e transforma sequências de eventos em alertas úteis
para a pessoa e para o cuidador.
"""
from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Literal

import requests
from pydantic import BaseModel, Field, ValidationError, field_validator

from robo.resiliencia import ErroDeSistema, com_retry

log = logging.getLogger("robo.eventos")
CLASSES_PORTA = {"campainha", "batida_porta"}


class EventoSom(BaseModel):
    momento: datetime
    classe: Literal["campainha", "batida_porta", "ambiente"]
    confianca: float = Field(ge=0.0, le=1.0)
    dispositivo: str = Field(min_length=1, max_length=40)

    @field_validator("classe", mode="before")
    @classmethod
    def normalizar_classe(cls, valor):
        return str(valor).strip().lower().replace(" ", "_") if valor is not None else valor


# ---------- leitura ----------

def ler_csvs(cfg) -> tuple[list[dict], list[str]]:
    arquivos = sorted(cfg.dir_entrada.glob("eventos_*.csv"))
    linhas = []
    for arquivo in arquivos:
        with arquivo.open(encoding="utf-8", newline="") as arq:
            for numero, linha in enumerate(csv.DictReader(arq), start=2):
                linha["_origem"] = f"{arquivo.name}:{numero}"
                linhas.append(linha)
    return linhas, [a.name for a in arquivos]


def ler_api(url: str, timeout: float) -> list[dict]:
    @com_retry(tentativas=3, espera_inicial=1.0)
    def _get():
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            dados = resp.json()
        except (requests.RequestException, ValueError) as erro:
            raise ErroDeSistema(f"API de eventos indisponível: {erro}") from erro
        if not isinstance(dados, list):
            raise ErroDeSistema("API de eventos devolveu formato inesperado")
        return dados

    return [{**item, "_origem": "api"} for item in _get()]


def validar(linhas: list[dict]) -> tuple[list[EventoSom], list[dict]]:
    validos, quarentena = [], []
    vistos = set()
    for linha in linhas:
        origem = linha.pop("_origem", "?")
        try:
            evento = EventoSom(**linha)
        except ValidationError as erro:
            motivo = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in erro.errors())
            quarentena.append({**linha, "origem": origem, "motivo": motivo})
            continue
        chave = (evento.momento, evento.classe, evento.dispositivo)
        if chave in vistos:  # idempotência: o mesmo evento exportado duas vezes conta uma vez
            continue
        vistos.add(chave)
        validos.append(evento)
    return sorted(validos, key=lambda e: e.momento), quarentena


# ---------- regras inteligentes ----------

def _noturno(momento: datetime, faixa: list[int]) -> bool:
    inicio, fim = faixa
    return momento.hour >= inicio or momento.hour < fim


def gerar_alertas(eventos: list[EventoSom], regras: dict, agora: datetime) -> tuple[list[dict], list[EventoSom]]:
    r = regras["eventos"]
    alertas, incertos = [], []
    confiaveis = []
    for e in eventos:
        (confiaveis if e.confianca >= r["confianca_minima"] else incertos).append(e)

    porta = [e for e in confiaveis if e.classe in CLASSES_PORTA]

    # Regra 1: insistência na porta (várias detecções numa janela curta)
    janela = timedelta(minutes=r["janela_repeticao_min"])
    i = 0
    while i < len(porta):
        grupo = [porta[i]]
        j = i + 1
        while j < len(porta) and porta[j].momento - porta[i].momento <= janela and porta[j].dispositivo == porta[i].dispositivo:
            grupo.append(porta[j])
            j += 1
        if len(grupo) >= r["repeticoes_para_alerta"]:
            alertas.append({
                "momento": grupo[0].momento, "tipo": "insistencia_porta", "severidade": "media",
                "dispositivo": grupo[0].dispositivo,
                "mensagem": f"{len(grupo)} sons de porta em {r['janela_repeticao_min']} min. "
                            "Alguém pode ter tentado contato sem ser atendido.",
            })
            i = j
        else:
            i += 1

    # Regra 2: som de porta de madrugada
    for e in porta:
        if _noturno(e.momento, r["horario_noturno"]):
            alertas.append({
                "momento": e.momento, "tipo": "porta_noturna", "severidade": "alta", "dispositivo": e.dispositivo,
                "mensagem": f"{e.classe.replace('_', ' ')} às {e.momento:%H:%M}, fora do horário comum. "
                            "Vale confirmar com a pessoa se está tudo bem.",
            })

    # Regra 3: dispositivo silencioso (celular sem enviar nada, inclusive 'ambiente')
    ultimo_por_disp = defaultdict(lambda: None)
    for e in eventos:
        anterior = ultimo_por_disp[e.dispositivo]
        if anterior and e.momento - anterior > timedelta(hours=r["horas_sem_evento_dispositivo_offline"]):
            alertas.append(_alerta_offline(e.dispositivo, anterior, e.momento))
        ultimo_por_disp[e.dispositivo] = e.momento
    for disp, ultimo in ultimo_por_disp.items():
        if ultimo and agora - ultimo > timedelta(hours=r["horas_sem_evento_dispositivo_offline"]):
            alertas.append(_alerta_offline(disp, ultimo, agora, ainda=True))

    return sorted(alertas, key=lambda a: a["momento"]), incertos


def _alerta_offline(disp: str, desde: datetime, ate: datetime, ainda: bool = False) -> dict:
    horas = (ate - desde).total_seconds() / 3600
    return {
        "momento": desde, "tipo": "dispositivo_silencioso", "severidade": "alta" if ainda else "baixa",
        "dispositivo": disp,
        "mensagem": f"Nenhum som registrado por {horas:.0f} h"
                    + (" e o celular continua sem enviar dados. Verificar bateria/conexão." if ainda
                       else ". O monitoramento ficou parado nesse intervalo."),
    }


def executar(cfg, detalhes: dict, revisao_humana: list, agora: datetime | None = None) -> dict:
    agora = agora or datetime.now()
    linhas, fonte = [], "csv"
    if cfg.eventos_api_url:
        try:
            linhas = ler_api(cfg.eventos_api_url, cfg.regras["rede"]["timeout_s"])
            fonte = "api"
        except ErroDeSistema as erro:
            log.warning("%s. Caminho seguro: lendo os CSVs exportados.", erro)
    if not linhas:
        linhas, arquivos = ler_csvs(cfg)
        detalhes["arquivos"] = arquivos
        if not arquivos:
            log.warning("Nenhum arquivo eventos_*.csv em %s. Relatório sairá sem eventos.", cfg.dir_entrada)
            detalhes["avisos"] = True

    eventos, quarentena = validar(linhas)
    alertas, incertos = gerar_alertas(eventos, cfg.regras, agora)

    for item in quarentena:
        revisao_humana.append({"tipo": "evento_invalido", "item": item["origem"], "motivo": item["motivo"],
                               "acao_sugerida": "Corrigir ou descartar a linha na exportação do OuviAí"})
    if quarentena:
        log.warning("%d linha(s) de evento inválida(s) foram para quarentena", len(quarentena))
        detalhes["avisos"] = True

    detalhes.update(fonte=fonte, lidos=len(linhas), validos=len(eventos), quarentena=len(quarentena),
                    incertos=len(incertos), alertas=len(alertas))
    return {"eventos": eventos, "alertas": alertas, "incertos": incertos, "quarentena": quarentena}
