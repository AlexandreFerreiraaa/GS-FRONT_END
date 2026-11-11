from pydantic import BaseModel, Field


class VisaoResposta(BaseModel):
    possivel_fissura: bool
    confianca: float = Field(ge=0, le=1)
    limiar: float = Field(ge=0, le=1)
    aviso: str
