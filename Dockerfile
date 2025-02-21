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

# Copy dependency files 
COPY pyproject.toml poetry.lock ./

# Install dependencies 
RUN poetry install --no-root

# Clear Poetry cache to reduce image size
RUN poetry cache clear --all pypi

# Ensure logs are flushed to stdout immediately
ENV PYTHONUNBUFFERED=1

# Frontend
FROM base AS streamlit
EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "./src/frontend/app.py", "--server.port", "8501"]

# Backend
FROM base AS fastapi
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.backend.wsgi:app", "--host", "0.0.0.0", "--port", "8000"]