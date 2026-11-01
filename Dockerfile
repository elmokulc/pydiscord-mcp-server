FROM ghcr.io/astral-sh/uv:0.13.6 AS uv
FROM python:3.12-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    MCP_HOST=0.0.0.0 MCP_PORT=8085
RUN useradd --system --uid 10001 --create-home app
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
USER app
EXPOSE 8085
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('MCP_PORT','8085')+'/health/ready', timeout=3).close()"]
CMD ["python", "-m", "pydiscord_mcp_server"]
