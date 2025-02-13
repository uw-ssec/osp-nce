FROM python:3.13-slim

# Set environment variables to avoid prompts
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# Set working directory
WORKDIR /app

# Copy project files into the container
COPY . /app

# Copy .env file
COPY .env /app/.env

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    freetds-bin \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Install dependencies
RUN poetry install --no-root

# Expose ports
EXPOSE 8000 8501

# Run FastAPI 
CMD ["bash", "-c", "poetry run uvicorn src.serve.wsgi:app --host 0.0.0.0 --port 8000 & poetry run streamlit run src/serve/streamlit_app.py --server.port 8501"]