import pytest
from pipelines import analise
from pipelines.analise import ErroLLM
from schemas.relato import RelatoEntrada

ENTRADA = RelatoEntrada(descricao="Buraco enorme na avenida, carros desviando.", local="Av. Paulista")
JSON_OK = ('{"categoria":"buraco","urgencia":"alta","resumo":"Buraco grande na via.",'
           '"orientacao":"Sinalize e evite o local.","encaminhamento":"Secretaria de Obras"}')


def test_resposta_valida(monkeypatch):
    monkeypatch.setattr(analise, "completar", lambda s, u: JSON_OK)
    r = analise.analisar(ENTRADA)
    assert r.categoria == "buraco" and r.urgencia == "alta"


def test_json_com_texto_em_volta(monkeypatch):
    monkeypatch.setattr(analise, "completar", lambda s, u: f"Aqui está:\n{JSON_OK}\nOk.")
    assert analise.analisar(ENTRADA).categoria == "buraco"


def test_resposta_sem_json(monkeypatch):
    monkeypatch.setattr(analise, "completar", lambda s, u: "não sei")
    with pytest.raises(ErroLLM):
        analise.analisar(ENTRADA)


def test_categoria_invalida(monkeypatch):
    ruim = JSON_OK.replace('"buraco"', '"dragao"')
    monkeypatch.setattr(analise, "completar", lambda s, u: ruim)
    with pytest.raises(ErroLLM):
        analise.analisar(ENTRADA)


def test_falha_do_provedor(monkeypatch):
    def quebra(s, u):
        raise TimeoutError()
    monkeypatch.setattr(analise, "completar", quebra)
    with pytest.raises(ErroLLM):
        analise.analisar(ENTRADA)
