FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir .[mcp]

EXPOSE 8000

CMD ["neuro-mcp", "--config", "/app/config.yaml", "serve", "--transport", "streamable-http", "--host", "127.0.0.1", "--port", "8000"]
