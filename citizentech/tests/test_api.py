from fastapi.testclient import TestClient
from main import app
from pipelines import analise

client = TestClient(app)
JSON_OK = ('{"categoria":"fissura","urgencia":"media","resumo":"Fissura em muro.",'
           '"orientacao":"Evite aproximar-se.","encaminhamento":"Defesa Civil"}')


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_relato_ok(monkeypatch):
    monkeypatch.setattr(analise, "completar", lambda s, u: JSON_OK)
    r = client.post("/relatos", json={"descricao": "Fissura grande no muro da escola", "local": "Centro"})
    assert r.status_code == 200
    assert r.json()["protocolo"].startswith("CT-")


def test_relato_validacao():
    r = client.post("/relatos", json={"descricao": "curto", "local": "x"})
    assert r.status_code == 422


def test_erro_llm_vira_502(monkeypatch):
    monkeypatch.setattr(analise, "completar", lambda s, u: "lixo")
    r = client.post("/relatos", json={"descricao": "Buraco na rua principal", "local": "Centro"})
    assert r.status_code == 502
    assert "Não foi possível" in r.json()["detail"]


def test_visao_tipo_invalido():
    r = client.post("/visao/classificar", files={"arquivo": ("a.txt", b"oi", "text/plain")})
    assert r.status_code == 415


def test_visao_modelo_ausente():
    r = client.post("/visao/classificar", files={"arquivo": ("a.jpg", b"\xff\xd8\xff", "image/jpeg")})
    assert r.status_code == 503
