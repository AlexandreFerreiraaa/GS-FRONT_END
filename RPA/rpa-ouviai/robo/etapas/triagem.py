"""Etapa 3: triagem inteligente dos pedidos do cidadão (NLP).

Tema RPA: IA aplicada ao processo (classificação de texto) + revisão humana.
Os pedidos chegam do assistente de voz (transcrições) ou de mensagens. O robô:
  1. mascara dados pessoais (LGPD) antes de qualquer outra coisa;
  2. aplica regra de emergência por palavras-chave, que tem prioridade sobre o modelo;
  3. classifica o tema com TF-IDF + Regressão Logística;
  4. manda para revisão humana o que o modelo não tem confiança para decidir;
  5. sugere o encaminhamento certo (órgão/canal) para cada tema.
"""
from __future__ import annotations

import csv
import logging
import re
import unicodedata
from datetime import datetime

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from robo.privacidade import mascarar

log = logging.getLogger("robo.triagem")

ENCAMINHAMENTOS = {
    "beneficio_bpc": "BPC/LOAS: inscrição no CadÚnico no CRAS, depois pedido no Meu INSS ou telefone 135.",
    "saude_auditiva": "Aparelho auditivo pelo SUS: começar pela UBS, que encaminha ao serviço de saúde auditiva/CER.",
    "direitos_idoso": "Estatuto da Pessoa Idosa: Disque 100 para denúncias; Defensoria Pública para orientação jurídica.",
    "transporte_gratuidade": "Gratuidade no transporte (65+): documento com foto no transporte urbano; interestadual pela Carteira da Pessoa Idosa no CRAS.",
    "golpe_suspeito": "Possível golpe: não passar dados nem códigos; confirmar só pelos canais oficiais (135, gov.br). Avisar o cuidador.",
    "fora_escopo": "Fora do tema do OuviAí. Responder com orientação genérica e indicar quem pode ajudar.",
    "emergencia": "EMERGÊNCIA: acionar 192/193/190 e avisar o cuidador imediatamente.",
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


# ---------- modelo ----------

def criar_pipeline() -> Pipeline:
    # n-gramas de caracteres deixam o modelo tolerante a erros de digitação e de transcrição (STT)
    return Pipeline([
        ("features", FeatureUnion([
            ("palavras", TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("caracteres", TfidfVectorizer(preprocessor=normalizar, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ])),
        ("clf", LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")),
    ])


def ler_rotulados(caminho) -> tuple[list[str], list[str]]:
    with open(caminho, encoding="utf-8", newline="") as arq:
        linhas = list(csv.DictReader(arq))
    return [l["texto"] for l in linhas], [l["categoria"] for l in linhas]


def carregar_ou_treinar(cfg) -> Pipeline:
    modelo_ok = cfg.arquivo_modelo.exists() and (
        cfg.arquivo_modelo.stat().st_mtime >= cfg.arquivo_treino.stat().st_mtime)
    if modelo_ok:
        try:
            return joblib.load(cfg.arquivo_modelo)
        except Exception as erro:  # arquivo corrompido ou versão diferente do sklearn
            log.warning("Modelo salvo não pôde ser carregado (%s). Retreinando.", erro)
    textos, rotulos = ler_rotulados(cfg.arquivo_treino)
    modelo = criar_pipeline().fit(textos, rotulos)
    joblib.dump(modelo, cfg.arquivo_modelo)
    log.info("Modelo de triagem treinado com %d exemplos e salvo", len(textos))
    return modelo


# ---------- classificação ----------

def detectar_emergencia(texto: str, palavras: list[str]) -> str | None:
    """Busca expressões inteiras (com fronteira de palavra), para 'caí' não casar com 'caixa'."""
    alvo = normalizar(texto)
    for palavra in palavras:
        if re.search(rf"\b{re.escape(normalizar(palavra))}\b", alvo):
            return palavra
    return None


def classificar(texto: str, modelo, regras: dict) -> dict:
    r = regras["triagem"]
    gatilho = detectar_emergencia(texto, r["palavras_emergencia"])
    if gatilho:
        return {"categoria": "emergencia", "confianca": 1.0, "metodo": f"regra ('{gatilho}')",
                "revisao_humana": False}
    probs = modelo.predict_proba([texto])[0]
    melhor = int(probs.argmax())
    categoria, confianca = modelo.classes_[melhor], float(probs[melhor])
    return {"categoria": categoria, "confianca": round(confianca, 3), "metodo": "modelo",
            "revisao_humana": confianca < r["confianca_minima_modelo"]}


def ler_pedidos(cfg) -> list[dict]:
    pedidos = []
    for arquivo in sorted(cfg.dir_entrada.glob("pedidos_*.csv")):
        with arquivo.open(encoding="utf-8", newline="") as arq:
            for numero, linha in enumerate(csv.DictReader(arq), start=2):
                linha["origem"] = f"{arquivo.name}:{numero}"
                pedidos.append(linha)
    return pedidos


def executar(cfg, detalhes: dict, revisao_humana: list) -> list[dict]:
    pedidos = ler_pedidos(cfg)
    if not pedidos:
        log.warning("Nenhum arquivo pedidos_*.csv com conteúdo. Etapa segue sem pedidos.")
        detalhes.update(pedidos=0, avisos=True)
        return []

    modelo = carregar_ou_treinar(cfg)
    resultados, mascarados = [], 0
    for p in pedidos:
        texto_original = (p.get("texto") or "").strip()
        if not texto_original:
            revisao_humana.append({"tipo": "pedido_vazio", "item": p["origem"], "motivo": "texto vazio",
                                   "acao_sugerida": "Verificar falha de transcrição no assistente de voz"})
            continue
        texto = mascarar(texto_original)
        mascarados += texto != texto_original
        try:
            momento = datetime.fromisoformat(p.get("momento", ""))
        except ValueError:
            momento = None
        res = classificar(texto, modelo, cfg.regras)
        res.update(momento=momento, canal=p.get("canal", "?"), texto=texto, origem=p["origem"],
                   encaminhamento=ENCAMINHAMENTOS.get(res["categoria"], ENCAMINHAMENTOS["fora_escopo"]))
        if res["revisao_humana"]:
            revisao_humana.append({"tipo": "pedido_incerto", "item": p["origem"],
                                   "motivo": f"modelo indeciso ({res['categoria']} com {res['confianca']:.0%})",
                                   "acao_sugerida": "Cuidador ou atendente confirma o tema e responde"})
        resultados.append(res)

    por_categoria: dict[str, int] = {}
    for r in resultados:
        por_categoria[r["categoria"]] = por_categoria.get(r["categoria"], 0) + 1
    detalhes.update(pedidos=len(resultados), dados_pessoais_mascarados=mascarados,
                    emergencias=por_categoria.get("emergencia", 0),
                    revisao_humana=sum(r["revisao_humana"] for r in resultados), por_categoria=por_categoria)
    return resultados
