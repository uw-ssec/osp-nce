# Base
FROM ubuntu:latest
FROM python:3.10-slim AS base
WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    freetds-bin \
    freetds-dev \
    freetds-bin \
    tdsodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Define build argument
ARG RAD_PASSWORD

# Set environment variable
ENV RAD_PASSWORD=${RAD_PASSWORD}

# Print the RAD_PASSWORD environment variable
RUN echo "RAD_PASSWORD is: $RAD_PASSWORD"

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