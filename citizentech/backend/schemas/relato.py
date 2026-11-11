from enum import Enum
from pydantic import BaseModel, Field


class Categoria(str, Enum):
    buraco = "buraco"
    fissura = "fissura"
    calcada = "calcada"
    iluminacao = "iluminacao"
    outro = "outro"


class Urgencia(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class RelatoEntrada(BaseModel):
    descricao: str = Field(min_length=10, max_length=1000)
    local: str = Field(min_length=3, max_length=120)


class RelatoAnalise(BaseModel):
    """Saída estruturada que o LLM precisa devolver."""
    categoria: Categoria
    urgencia: Urgencia
    resumo: str = Field(max_length=200)
    orientacao: str = Field(max_length=400)
    encaminhamento: str = Field(max_length=150)


class RelatoResposta(BaseModel):
    protocolo: str
    analise: RelatoAnalise
