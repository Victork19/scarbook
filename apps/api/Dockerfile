FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system --gid 10001 scarbook \
    && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin scarbook

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/api/app /app/app
COPY apps/api/fixtures /app/fixtures

RUN mkdir -p /var/lib/scarbook/raw \
    && chown -R scarbook:scarbook /app /var/lib/scarbook

USER scarbook
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
