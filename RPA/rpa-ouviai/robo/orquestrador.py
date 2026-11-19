"""Orquestrador do Robô Cuidador OuviAí.

Estrutura inspirada no REFramework do UiPath:
  Init (config, logs, estado) → etapas de processamento → End (relatório de execução).
Cada etapa roda isolada: se uma falhar, ela é registrada e as demais continuam.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime

from robo.config import Config
from robo.estado import Estado
from robo.etapas import coleta_fontes, eventos, notificacao, relatorio, triagem
from robo.llm import gerar_resumo
from robo.logs import configurar_logs
from robo.resiliencia import Etapa


def executar(offline: bool | None = None, demo_falhas: bool | None = None, forcar_envio: bool = False,
             agora: datetime | None = None) -> dict:
    agora = agora or datetime.now()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    cfg = Config.carregar(offline=offline, demo_falhas=demo_falhas)
    log = configurar_logs(cfg.dir_logs, run_id)
    log.info("Modo: %s%s", "offline" if cfg.modo_offline else "online com fallback",
             " + demonstração de falhas" if cfg.demo_falhas else "")
    estado = Estado(cfg.dir_estado / "estado.json")
    inicio = time.perf_counter()

    execucao: dict = {"grupo": cfg.grupo, "run_id": run_id, "inicio": agora.isoformat(timespec="seconds"),
                      "modo_offline": cfg.modo_offline, "demo_falhas": cfg.demo_falhas}
    revisao: list[dict] = []
    fontes, ev, pedidos = [], {"eventos": [], "alertas": [], "incertos": []}, []

    if cfg.demo_falhas:
        _preparar_falhas_demo(cfg)

    with Etapa("1. Coleta de fontes oficiais", execucao) as d:
        fontes = coleta_fontes.executar(cfg, estado, d, revisao)

    with Etapa("2. Eventos sonoros e alertas", execucao) as d:
        ev = eventos.executar(cfg, d, revisao, agora=agora)

    with Etapa("3. Triagem de pedidos (NLP)", execucao) as d:
        pedidos = triagem.executar(cfg, d, revisao)

    periodo = f"{agora.isocalendar().year}-S{agora.isocalendar().week:02d}"
    planilha = cfg.dir_saida / f"relatorio_{periodo}.xlsx"
    pagina = cfg.dir_saida / f"resumo_{periodo}.html"
    resumo = ""
    with Etapa("4. Relatórios (Excel + HTML)", execucao) as d:
        ind = relatorio.indicadores(ev, pedidos, revisao)
        resumo, origem = gerar_resumo(cfg, ind)
        relatorio.gerar_html(pagina, ind, resumo, ev, pedidos, grupo=cfg.grupo)
        # a aba Execução é preenchida com o que já rodou até aqui
        relatorio.gerar_excel(planilha, run_id, ind, resumo, ev, pedidos, revisao, fontes, execucao, grupo=cfg.grupo)
        d.update(planilha=planilha.name, pagina=pagina.name, resumo_por=origem, indicadores=ind)

    with Etapa("5. Notificação ao cuidador", execucao) as d:
        if not planilha.exists():
            raise FileNotFoundError("planilha não foi gerada; notificação cancelada")
        assunto = f"[OuviAí] Resumo da semana {periodo}"
        if ev.get("alertas") and any(a["severidade"] == "alta" for a in ev["alertas"]) or \
                any(p["categoria"] == "emergencia" for p in pedidos):
            assunto = "⚠ " + assunto + " — há itens de prioridade alta"
        notificacao.executar(cfg, estado, d, periodo, assunto, resumo,
                             pagina.read_text(encoding="utf-8"), planilha, forcar=forcar_envio)

    if cfg.demo_falhas:  # entradas de demonstração não podem contaminar as próximas execuções
        for arquivo in cfg.dir_entrada.glob("*_demo_falhas.csv"):
            arquivo.unlink()

    execucao["duracao_total_s"] = round(time.perf_counter() - inicio, 2)
    execucao["revisao_humana"] = revisao
    execucao["status_geral"] = ("ok" if all(e["status"] == "ok" for e in execucao["etapas"])
                                else "concluido_com_pendencias")
    estado.registrar_execucao({"run_id": run_id, "status": execucao["status_geral"],
                               "duracao_s": execucao["duracao_total_s"]})
    estado.salvar()

    destino = cfg.dir_saida / "execucoes" / f"execucao_{run_id}.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(execucao, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log.info("===== Execução %s finalizada: %s em %.2fs | %d item(ns) para revisão humana =====",
             run_id, execucao["status_geral"], execucao["duracao_total_s"], len(revisao))
    return execucao


def _preparar_falhas_demo(cfg) -> None:
    """Injeta entradas problemáticas para demonstrar o tratamento de falhas no vídeo."""
    log = logging.getLogger("robo.demo")
    (cfg.dir_entrada / "eventos_demo_falhas.csv").write_text(
        "momento,classe,confianca,dispositivo\n"
        "2026-11-09T10:00:00,campainha,1.7,celular-dona-lucia\n"      # confiança fora de 0..1
        "ontem de tarde,batida_porta,0.9,celular-dona-lucia\n"         # data inválida
        "2026-11-09T11:00:00,alarme_incendio,0.95,celular-dona-lucia\n"  # classe que o modelo não tem
        "2026-11-09T12:00:00,ambiente,0.88,\n",                         # dispositivo vazio
        encoding="utf-8")
    (cfg.dir_entrada / "pedidos_demo_falhas.csv").write_text(
        "momento,canal,texto\n"
        "2026-11-09T09:00:00,assistente_voz,\n"                          # transcrição vazia
        "2026-11-09T09:05:00,whatsapp,meu cpf é 123.456.789-09 e o telefone (11) 98765-4321 me ajuda com o benefício\n",
        encoding="utf-8")
    log.info("Demonstração de falhas: entradas inválidas criadas em %s", cfg.dir_entrada.name)
