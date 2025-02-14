# Base
FROM python:3.13-slim AS base
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    freetds-bin \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry install --no-root
RUN poetry cache clear --all pypi
ENV PYTHONUNBUFFERED=1

# Frontend
FROM base AS streamlit
EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "./src/frontend/app.py", "--server.port", "8501"]

# Backend
FROM base AS fastapi
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.backend.wsgi:app", "--host", "0.0.0.0", "--port", "8000"]