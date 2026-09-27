FROM python:3.12.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 TZ=UTC

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

COPY --chown=appuser:appgroup . .

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 CMD python -c "import os,sys; sys.exit(0 if any('__main__.py' in open(f'/proc/{p}/cmdline','rb').read().decode(errors='ignore') for p in os.listdir('/proc') if p.isdigit()) else 1)"

CMD ["python", "__main__.py"]
