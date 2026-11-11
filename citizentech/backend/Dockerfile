FROM python:3.11-slim
WORKDIR /app
ARG INSTALL_VISION=false
COPY requirements.txt requirements-vision.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALL_VISION" = "true" ]; then pip install --no-cache-dir -r requirements-vision.txt; fi
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
