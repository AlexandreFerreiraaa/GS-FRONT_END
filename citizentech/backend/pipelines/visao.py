import os
from providers.modelo import prever
from schemas.visao import VisaoResposta

AVISO = ("Resultado de apoio à triagem. A presença de fissura na imagem não indica "
         "a gravidade do dano nem a segurança estrutural: encaminhe para inspeção profissional.")


def classificar(imagem_bytes: bytes) -> VisaoResposta:
    limiar = float(os.getenv("LIMIAR_FISSURA", "0.5"))
    p = prever(imagem_bytes)
    return VisaoResposta(possivel_fissura=p >= limiar, confianca=p, limiar=limiar, aviso=AVISO)
