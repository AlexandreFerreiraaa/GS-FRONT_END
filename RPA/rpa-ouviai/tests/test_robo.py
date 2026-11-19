"""Testes automatizados do robô. Rodam sem internet e sem SMTP: python -m pytest -q"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robo.config import Config  # noqa: E402
from robo.estado import Estado  # noqa: E402
from robo.etapas import coleta_fontes, eventos, triagem  # noqa: E402
from robo.llm import gerar_resumo  # noqa: E402
from robo.privacidade import mascarar  # noqa: E402
from robo.resiliencia import ErroDeNegocio, ErroDeSistema, Etapa, com_retry  # noqa: E402


@pytest.fixture
def cfg(tmp_path):
    c = Config.carregar(offline=True, demo_falhas=False)
    c.dir_entrada = tmp_path / "entrada"
    c.dir_saida = tmp_path / "saida"
    c.dir_base = tmp_path / "base"
    c.arquivo_modelo = tmp_path / "modelo.joblib"
    for d in (c.dir_entrada, c.dir_saida, c.dir_base):
        d.mkdir()
    return c


# ---------- resiliência ----------

def test_retry_repete_erro_de_sistema_e_depois_desiste():
    chamadas = []

    @com_retry(tentativas=3, espera_inicial=0, dormir=lambda _s: None)
    def instavel():
        chamadas.append(1)
        raise ErroDeSistema("fora do ar")

    with pytest.raises(ErroDeSistema):
        instavel()
    assert len(chamadas) == 3


def test_retry_nao_repete_erro_de_negocio():
    chamadas = []

    @com_retry(tentativas=3, espera_inicial=0, dormir=lambda _s: None)
    def dado_ruim():
        chamadas.append(1)
        raise ErroDeNegocio("linha inválida")

    with pytest.raises(ErroDeNegocio):
        dado_ruim()
    assert len(chamadas) == 1


def test_etapa_que_falha_nao_derruba_o_robo():
    relatorio: dict = {}
    with Etapa("teste", relatorio):
        raise RuntimeError("bug inesperado")
    assert relatorio["etapas"][0]["status"] == "falhou"
    assert "bug inesperado" in relatorio["etapas"][0]["erro"]


# ---------- privacidade ----------

@pytest.mark.parametrize("texto,marcador", [
    ("meu cpf é 123.456.789-09", "[CPF]"),
    ("liga no (11) 98765-4321", "[TELEFONE]"),
    ("manda para maria@exemplo.com", "[EMAIL]"),
])
def test_mascara_dados_pessoais(texto, marcador):
    resultado = mascarar(texto)
    assert marcador in resultado
    assert not any(ch.isdigit() for ch in resultado.split(marcador)[0][-3:])


# ---------- coleta ----------

def test_site_fora_do_ar_usa_snapshot(cfg):
    cfg.modo_offline = False

    def baixar_quebrado(_url):
        raise ErroDeSistema("timeout")

    estado = Estado(cfg.dir_saida / "estado.json")
    revisao: list = []
    detalhes: dict = {}
    res = coleta_fontes.executar(cfg, estado, detalhes, revisao, baixar=baixar_quebrado)
    assert all(r["origem"] == "snapshot" for r in res)
    assert detalhes["avisos"] is True
    assert revisao == []


def test_fonte_sem_snapshot_vai_para_revisao_humana(cfg):
    cfg.fontes = [{"id": "x", "titulo": "X", "orgao": "Y", "url": "https://x.invalid", "categoria": "c",
                   "seletor": None, "snapshot": "nao/existe.html"}]
    revisao: list = []
    res = coleta_fontes.executar(cfg, Estado(cfg.dir_saida / "e.json"), {}, revisao)
    assert res[0]["status"] == "falhou"
    assert revisao[0]["item"] == "x"


def test_segunda_coleta_igual_nao_reindexa(cfg):
    estado = Estado(cfg.dir_saida / "estado.json")
    primeira = coleta_fontes.executar(cfg, estado, {}, [])
    segunda = coleta_fontes.executar(cfg, estado, {}, [])
    assert all(r["mudou"] for r in primeira)
    assert not any(r["mudou"] for r in segunda)


def test_estado_corrompido_nao_trava(tmp_path):
    arquivo = tmp_path / "estado.json"
    arquivo.write_text("{isso não é json", encoding="utf-8")
    estado = Estado(arquivo)
    assert estado.dados["hashes_fontes"] == {}
    assert (tmp_path / "estado.corrompido.json").exists()


# ---------- eventos ----------

def test_linhas_invalidas_vao_para_quarentena():
    linhas = [
        {"momento": "2026-11-09T10:00:00", "classe": "campainha", "confianca": "0.9", "dispositivo": "cel", "_origem": "a"},
        {"momento": "ontem", "classe": "campainha", "confianca": "0.9", "dispositivo": "cel", "_origem": "b"},
        {"momento": "2026-11-09T10:00:00", "classe": "sirene", "confianca": "0.9", "dispositivo": "cel", "_origem": "c"},
        {"momento": "2026-11-09T10:00:00", "classe": "campainha", "confianca": "1.5", "dispositivo": "cel", "_origem": "d"},
    ]
    validos, quarentena = eventos.validar(linhas)
    assert len(validos) == 1
    assert {q["origem"] for q in quarentena} == {"b", "c", "d"}


def test_evento_duplicado_conta_uma_vez():
    linha = {"momento": "2026-11-09T10:00:00", "classe": "campainha", "confianca": "0.9", "dispositivo": "cel"}
    validos, _ = eventos.validar([{**linha, "_origem": "1"}, {**linha, "_origem": "2"}])
    assert len(validos) == 1


def _evento(hora: str, classe: str = "campainha", conf: float = 0.9):
    return eventos.EventoSom(momento=datetime.fromisoformat(hora), classe=classe, confianca=conf, dispositivo="cel")


def test_regra_insistencia_e_porta_noturna(cfg):
    lista = [_evento("2026-11-09T14:00:00"), _evento("2026-11-09T14:01:00"), _evento("2026-11-09T14:02:00"),
             _evento("2026-11-10T03:00:00", "batida_porta")]
    alertas, _ = eventos.gerar_alertas(lista, cfg.regras, agora=datetime(2026, 11, 10, 8))
    tipos = {a["tipo"] for a in alertas}
    assert {"insistencia_porta", "porta_noturna"} <= tipos


def test_baixa_confianca_nao_gera_alerta(cfg):
    lista = [_evento(f"2026-11-09T14:0{i}:00", conf=0.3) for i in range(4)]
    alertas, incertos = eventos.gerar_alertas(lista, cfg.regras, agora=datetime(2026, 11, 9, 15))
    assert alertas == [] and len(incertos) == 4


def test_sem_arquivo_de_eventos_segue_vazio(cfg):
    detalhes: dict = {}
    res = eventos.executar(cfg, detalhes, [])
    assert res["eventos"] == [] and detalhes["avisos"] is True


# ---------- triagem ----------

def test_emergencia_tem_prioridade_sobre_o_modelo(cfg):
    modelo = triagem.carregar_ou_treinar(cfg)
    r = triagem.classificar("caí no banheiro e não consigo levantar", modelo, cfg.regras)
    assert r["categoria"] == "emergencia"


def test_cai_nao_confunde_com_caixa(cfg):
    assert triagem.detectar_emergencia("o caixa do banco estava fechado", cfg.regras["triagem"]["palavras_emergencia"]) is None


def test_texto_ambiguo_vai_para_revisao_humana(cfg):
    modelo = triagem.carregar_ou_treinar(cfg)
    r = triagem.classificar("aquilo", modelo, cfg.regras)
    assert r["revisao_humana"] is True


def test_pedido_vazio_e_cpf_mascarado(cfg):
    (cfg.dir_entrada / "pedidos_t.csv").write_text(
        "momento,canal,texto\n2026-11-09T09:00:00,voz,\n"
        "2026-11-09T09:01:00,voz,meu cpf é 123.456.789-09 e quero pedir o bpc\n", encoding="utf-8")
    revisao: list = []
    res = triagem.executar(cfg, {}, revisao)
    assert len(res) == 1 and "[CPF]" in res[0]["texto"]
    assert revisao[0]["tipo"] == "pedido_vazio"


# ---------- LLM opcional ----------

def test_sem_chave_de_llm_usa_template(cfg):
    ind = {"eventos_validos": 5, "campainhas": 2, "batidas": 1, "emergencias": 0, "alertas_altos": 0,
           "pedidos": 3, "tema_principal": "beneficio_bpc", "revisao_humana": 0}
    texto, origem = gerar_resumo(cfg, ind)
    assert origem == "template" and "5 sons" in texto


def test_llm_fora_do_ar_usa_template(cfg, monkeypatch):
    cfg.llm_api_url, cfg.llm_api_key = "http://127.0.0.1:9", "chave-falsa"
    cfg.regras["rede"]["timeout_s"] = 0.2
    monkeypatch.setattr("time.sleep", lambda _s: None)
    ind = {"eventos_validos": 1, "campainhas": 1, "batidas": 0, "emergencias": 0, "alertas_altos": 0,
           "pedidos": 0, "tema_principal": "nenhum", "revisao_humana": 0}
    _texto, origem = gerar_resumo(cfg, ind)
    assert origem == "template"
