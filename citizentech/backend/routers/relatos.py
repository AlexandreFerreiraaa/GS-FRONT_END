from uuid import uuid4
from fastapi import APIRouter, HTTPException
from schemas.relato import RelatoEntrada, RelatoResposta
from pipelines.analise import analisar, ErroLLM

router = APIRouter(prefix="/relatos", tags=["relatos"])


@router.post("", response_model=RelatoResposta)
def criar_relato(entrada: RelatoEntrada):
    try:
        analise = analisar(entrada)
    except ErroLLM:
        # o detalhe técnico fica no servidor; o cidadão recebe mensagem genérica
        raise HTTPException(status_code=502, detail="Não foi possível analisar o relato agora.")
    return RelatoResposta(protocolo=f"CT-{uuid4().hex[:8].upper()}", analise=analise)
