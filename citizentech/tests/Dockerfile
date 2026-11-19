FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY backend/requirements.txt tests/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
COPY backend backend
COPY tests tests
# sem chave de API e sem modelo: o LLM é simulado nos testes e a visão responde 503
CMD ["python", "-m", "pytest", "-v", "tests"]
