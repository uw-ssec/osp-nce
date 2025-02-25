# Base
FROM python:3.10-slim AS base
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    freetds-bin \
    freetds-dev \
    tdsodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first for caching
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies (no local package install yet)
RUN poetry install --no-root

# Now install project as a local package
COPY assets/ ./assets/
COPY osp_nce/ ./osp_nce/
RUN poetry install

# Clear Poetry cache to reduce image size
RUN poetry cache clear --all pypi

# Ensure logs are flushed to stdout immediately
ENV PYTHONUNBUFFERED=1

# Frontend
FROM base AS streamlit
EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "./osp_nce/frontend/main.py", "--server.port", "8501"]

# Backend
FROM base AS fastapi
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "osp_nce.backend.wsgi:app", "--host", "0.0.0.0", "--port", "8000"]