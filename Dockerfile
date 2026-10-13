FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Core Padua VTE calculator is zero-dependency (stdlib only).
# Optional: install pydantic for enterprise supervisor features.
RUN pip install --no-cache-dir 'pydantic>=2,<3'

COPY . .

# Default: show usage. Override CMD for specific commands.
CMD ["python", "cli.py", "info"]
