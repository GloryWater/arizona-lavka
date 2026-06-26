# =============================================================================
# ARIZONA LAVKA MARKETPLACE - BACKEND DOCKERFILE
# =============================================================================
# Local-friendly production image
# =============================================================================

FROM python:3.12-slim AS production

LABEL maintainer="Arizona Lavka Team"
LABEL version="3.2.0"
LABEL description="Arizona Lavka Marketplace Backend API - Production"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    APP_HOME=/app

WORKDIR /app

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup . .

RUN mkdir -p /app/data /app/secrets && \
    chown -R appuser:appgroup /app/data /app/secrets && \
    find /app -type f -name "*.py" -exec chmod 644 {} \; && \
    find /app -type d -exec chmod 755 {} \; && \
    chmod 700 /app/secrets

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
