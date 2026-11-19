"""Acesso ao modelo de fissuras treinado no Colab (MobileNetV2, .keras)."""
import io
import os

_model = None


class ModeloIndisponivel(Exception):
    pass


def _carregar():
    global _model
    if _model is None:
        caminho = os.getenv("MODEL_PATH", "models/modelo.keras")
        if not os.path.exists(caminho):
            raise ModeloIndisponivel(f"modelo não encontrado em {caminho}")
        try:
            import tensorflow as tf
        except ImportError as e:
            raise ModeloIndisponivel("tensorflow não instalado") from e
        _model = tf.keras.models.load_model(caminho)
    return _model


def prever(imagem_bytes: bytes) -> float:
    """Retorna a probabilidade (0 a 1) de a imagem conter fissura."""
    modelo = _carregar()   # primeiro: sem modelo ou sem as libs de visão, a resposta é 503
    try:
        import numpy as np
        from PIL import Image
    except ImportError as e:
        raise ModeloIndisponivel("dependências de visão não instaladas") from e

    img = Image.open(io.BytesIO(imagem_bytes)).convert("RGB").resize((224, 224))
    x = np.asarray(img, dtype="float32") / 127.5 - 1.0   # mesmo preprocess_input do MobileNetV2
    return float(modelo(x[None], training=False)[0][0])
