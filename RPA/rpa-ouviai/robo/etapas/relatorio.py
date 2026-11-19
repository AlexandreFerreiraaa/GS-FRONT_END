"""Etapa 4: geração dos relatórios (planilha Excel + página HTML acessível).

Tema RPA: automação de planilhas e documentos.
"""
from __future__ import annotations

import html
import logging
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

log = logging.getLogger("robo.relatorio")

CORES_SEVERIDADE = {"alta": "F8D7DA", "media": "FFF3CD", "baixa": "E2E3E5"}
ROTULO_SEVERIDADE = {"alta": "ALTA ⚠", "media": "MÉDIA", "baixa": "BAIXA"}


def indicadores(ev: dict, pedidos: list[dict], revisao: list) -> dict:
    eventos = ev.get("eventos", [])
    cats: dict[str, int] = {}
    for p in pedidos:
        cats[p["categoria"]] = cats.get(p["categoria"], 0) + 1
    tema = max((c for c in cats if c != "emergencia"), key=cats.get, default="nenhum")
    return {
        "eventos_validos": len(eventos),
        "campainhas": sum(e.classe == "campainha" for e in eventos),
        "batidas": sum(e.classe == "batida_porta" for e in eventos),
        "eventos_incertos": len(ev.get("incertos", [])),
        "alertas": len(ev.get("alertas", [])),
        "alertas_altos": sum(a["severidade"] == "alta" for a in ev.get("alertas", [])),
        "pedidos": len(pedidos),
        "emergencias": cats.get("emergencia", 0),
        "tema_principal": tema,
        "pedidos_por_tema": cats,
        "revisao_humana": len(revisao),
    }


def _aba(wb: Workbook, titulo: str, cabecalho: list[str], linhas: list[list], larguras: list[int] | None = None):
    ws = wb.create_sheet(titulo)
    ws.append(cabecalho)
    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", fgColor="1F3A5F")
    for linha in linhas:
        ws.append(linha)
    for i, largura in enumerate(larguras or [18] * len(cabecalho), start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura
    for linha in ws.iter_rows(min_row=2):
        for celula in linha:
            celula.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    if linhas:
        ws.auto_filter.ref = ws.dimensions
    return ws


def gerar_excel(destino: Path, run_id: str, ind: dict, resumo: str, ev: dict, pedidos: list[dict],
                revisao: list, fontes: list[dict], execucao: dict, grupo: dict | None = None) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo"
    ws["A1"] = "OuviAí — Relatório do Robô Cuidador"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A2"] = f"Execução {run_id} · gerado em {datetime.now():%d/%m/%Y %H:%M}"
    ws["A4"] = resumo
    ws["A4"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A4:D8")
    linha = 10
    for chave, valor in ind.items():
        if isinstance(valor, dict):
            valor = ", ".join(f"{k}: {v}" for k, v in valor.items())
        ws.cell(linha, 1, chave.replace("_", " ").capitalize()).font = Font(bold=True)
        ws.cell(linha, 2, valor)
        linha += 1
    if grupo and grupo.get("integrantes"):
        linha += 1
        ws.cell(linha, 1, "Identificação do grupo").font = Font(bold=True, size=12)
        ws.cell(linha + 1, 1, grupo.get("projeto", ""))
        ws.cell(linha + 2, 1, grupo.get("disciplina", ""))
        linha += 3
        for membro in grupo["integrantes"]:
            ws.cell(linha, 1, membro["nome"])
            ws.cell(linha, 2, f"RM {membro['rm']}")
            linha += 1
    ws.column_dimensions["A"].width = 28
    for col in "BCD":
        ws.column_dimensions[col].width = 30

    wsa = _aba(wb, "Alertas", ["Quando", "Severidade", "Tipo", "Dispositivo", "Mensagem"],
               [[a["momento"].strftime("%d/%m %H:%M"), ROTULO_SEVERIDADE[a["severidade"]], a["tipo"],
                 a["dispositivo"], a["mensagem"]] for a in ev.get("alertas", [])], [14, 12, 22, 16, 70])
    for linha_ws, alerta in zip(wsa.iter_rows(min_row=2), ev.get("alertas", [])):
        for celula in linha_ws:
            celula.fill = PatternFill("solid", fgColor=CORES_SEVERIDADE[alerta["severidade"]])

    _aba(wb, "Pedidos", ["Quando", "Canal", "Tema", "Confiança", "Método", "Revisão humana", "Texto (mascarado)", "Encaminhamento"],
         [[p["momento"].strftime("%d/%m %H:%M") if p["momento"] else "?", p["canal"], p["categoria"],
           p["confianca"], p["metodo"], "SIM" if p["revisao_humana"] else "não", p["texto"], p["encaminhamento"]]
          for p in pedidos], [14, 14, 20, 10, 16, 12, 50, 55])

    _aba(wb, "Eventos", ["Quando", "Classe", "Confiança", "Dispositivo"],
         [[e.momento.strftime("%d/%m %H:%M:%S"), e.classe, e.confianca, e.dispositivo] for e in ev.get("eventos", [])])

    _aba(wb, "Revisão humana", ["Tipo", "Item", "Motivo", "Ação sugerida", "Resolvido? (preencher)"],
         [[r["tipo"], r["item"], r["motivo"], r["acao_sugerida"], ""] for r in revisao], [18, 26, 50, 50, 20])

    _aba(wb, "Fontes", ["Fonte", "Origem", "Mudou?", "Trechos", "Status", "Erro", "URL"],
         [[f["titulo"], f.get("origem", "-"), "sim" if f.get("mudou") else "não", f.get("trechos", "-"),
           f["status"], f.get("erro", ""), f["url"]] for f in fontes], [40, 10, 8, 8, 10, 40, 60])

    _aba(wb, "Execução", ["Etapa", "Status", "Duração (s)", "Detalhes"],
         [[e["etapa"], e["status"], e.get("duracao_s"), str({k: v for k, v in e["detalhes"].items() if k != "avisos"})
           + (f" | ERRO: {e['erro']}" if e.get("erro") else "")] for e in execucao.get("etapas", [])], [26, 14, 12, 90])

    wb.save(destino)
    log.info("Planilha gerada: %s", destino.name)
    return destino


def gerar_html(destino: Path, ind: dict, resumo: str, ev: dict, pedidos: list[dict], grupo: dict | None = None) -> Path:
    """Versão para ler no celular: fonte grande, alto contraste, severidade com texto e ícone (não só cor)."""
    def esc(t):
        return html.escape(str(t))

    alertas = "".join(
        f'<li class="{a["severidade"]}"><strong>{esc(ROTULO_SEVERIDADE[a["severidade"]])}</strong> · '
        f'{a["momento"]:%d/%m %H:%M} · {esc(a["mensagem"])}</li>' for a in ev.get("alertas", [])
    ) or "<li>Nenhum alerta nesta semana.</li>"
    urgentes = "".join(
        f'<li class="alta"><strong>EMERGÊNCIA</strong> · {esc(p["texto"])}<br>{esc(p["encaminhamento"])}</li>'
        for p in pedidos if p["categoria"] == "emergencia")
    integrantes = " · ".join(f"{esc(m['nome'])} (RM {esc(m['rm'])})" for m in (grupo or {}).get("integrantes", []))
    temas = "".join(f"<li>{esc(k.replace('_', ' '))}: {v}</li>" for k, v in ind["pedidos_por_tema"].items())

    destino.write_text(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resumo OuviAí</title>
<style>
body{{font-family:system-ui,Arial,sans-serif;font-size:20px;line-height:1.5;max-width:720px;margin:0 auto;padding:16px;background:#fff;color:#111}}
h1{{font-size:28px}} h2{{font-size:24px;margin-top:28px}}
li{{margin:10px 0;padding:10px;border-radius:8px;list-style:none;border-left:8px solid #6c757d;background:#f1f3f5}}
li.alta{{border-color:#b00020;background:#fde8eb}} li.media{{border-color:#a66b00;background:#fff4d6}}
.resumo{{font-size:22px;background:#eef4ff;padding:14px;border-radius:8px}}
</style></head><body>
<h1>Resumo da semana · OuviAí</h1>
<p class="resumo">{esc(resumo)}</p>
{f"<h2>Precisa de atenção agora</h2><ul>{urgentes}</ul>" if urgentes else ""}
<h2>Alertas da casa</h2><ul>{alertas}</ul>
<h2>Pedidos por tema</h2><ul>{temas or "<li>Nenhum pedido.</li>"}</ul>
<p><small>Relatório gerado automaticamente. O OuviAí é um protótipo educacional e não substitui serviços de emergência (192, 193, 190).</small></p>
{f'<p><small>{esc((grupo or {}).get("projeto", ""))} · {esc((grupo or {}).get("disciplina", ""))}<br>Grupo: {integrantes}</small></p>' if integrantes else ""}
</body></html>""", encoding="utf-8")
    return destino
