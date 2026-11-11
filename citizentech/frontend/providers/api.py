"""Cliente HTTP da API. Traduz falhas técnicas em mensagens claras para o cidadão."""
import os
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_URL = os.getenv("API_URL", "http://localhost:8000")


class ErroApi(Exception):
    """A mensagem já está pronta para ser mostrada ao cidadão."""


def _post(caminho: str, timeout: int, **kwargs) -> dict:
    try:
        r = requests.post(f"{API_URL}{caminho}", timeout=timeout, **kwargs)
    except requests.exceptions.ConnectionError:
        raise ErroApi("O serviço está fora do ar no momento. Tente novamente em alguns minutos.")
    except requests.exceptions.Timeout:
        raise ErroApi("A análise demorou mais que o esperado. Tente novamente.")

    if r.status_code == 422:
        raise ErroApi("Confira os campos: a descrição precisa de pelo menos 10 caracteres.")
    if r.status_code in (413, 415):
        raise ErroApi("Imagem inválida. Envie um arquivo JPG ou PNG de até 5 MB.")
    if r.status_code == 503:
        raise ErroApi("A análise de imagem não está disponível agora. Você pode continuar só com o texto.")
    if r.status_code >= 400:
        raise ErroApi("Não conseguimos concluir a análise agora. Tente novamente.")
    try:
        return r.json()
    except ValueError:
        raise ErroApi("Recebemos uma resposta inesperada. Tente novamente.")


def enviar_relato(descricao: str, local: str) -> dict:
    dados = _post("/relatos", 40, json={"descricao": descricao, "local": local})
    try:
        for chave in ("categoria", "urgencia", "resumo", "orientacao", "encaminhamento"):
            dados["analise"][chave]
        dados["protocolo"]
    except (KeyError, TypeError):
        raise ErroApi("Recebemos uma resposta inesperada. Tente novamente.")
    return dados


def classificar_foto(nome: str, conteudo: bytes, tipo: str) -> dict:
    dados = _post("/visao/classificar", 40, files={"arquivo": (nome, conteudo, tipo)})
    if "possivel_fissura" not in dados or "confianca" not in dados:
        raise ErroApi("Recebemos uma resposta inesperada. Tente novamente.")
    return dados
