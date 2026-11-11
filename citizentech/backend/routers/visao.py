from fastapi import APIRouter, HTTPException, UploadFile, File
from pipelines.visao import classificar
from providers.modelo import ModeloIndisponivel
from schemas.visao import VisaoResposta

router = APIRouter(prefix="/visao", tags=["visao"])

TIPOS = {"image/jpeg", "image/png"}
MAX_BYTES = 5 * 1024 * 1024


@router.post("/classificar", response_model=VisaoResposta)
async def classificar_foto(arquivo: UploadFile = File(...)):
    if arquivo.content_type not in TIPOS:
        raise HTTPException(status_code=415, detail="Envie uma imagem JPG ou PNG.")
    conteudo = await arquivo.read()
    if len(conteudo) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Imagem muito grande (máximo 5 MB).")
    try:
        return classificar(conteudo)
    except ModeloIndisponivel:
        raise HTTPException(status_code=503, detail="Análise de imagem indisponível no momento.")
    except Exception:
        raise HTTPException(status_code=400, detail="Não foi possível ler a imagem.")
