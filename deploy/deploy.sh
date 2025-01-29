#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$0")

# Define project paths
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"
SERVE_DIR="$SRC_DIR/serve"

# Load environment variables from .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Function to install Python on macOS
install_python_mac() {
    echo "Installing Python on macOS..."
    if ! command -v brew &> /dev/null
    then
        echo "Homebrew not found, installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python
}

# Function to install Python on Linux
install_python_linux() {
    echo "Installing Python on Linux..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
}

# Function to install Python on Windows
install_python_windows() {
    echo "Installing Python on Windows..."
    curl https://www.python.org/ftp/python/3.13.0/python-3.13.0.exe --output "%TMP%\python-3.13.0.exe" && "%TMP%\python-3.13.0.exe" /quiet InstallAllUsers=1 PrependPath=1
}

# Function to kill processes using a specific port
kill_process_on_port() {
    PORT=$1
    if lsof -i :"$PORT" -t >/dev/null 2>&1
    then
        echo "Killing process on port $PORT..."
        lsof -i :"$PORT" -t | xargs kill -9
    fi
}

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found, installing..."
    case "$OSTYPE" in
        darwin*)  install_python_mac ;;
        linux*)   install_python_linux ;;
        msys*)    install_python_windows ;;
        cygwin*)  install_python_windows ;;
        *)        echo "Unsupported OS: $OSTYPE" && exit 1 ;;
    esac
fi

# Check if environment variables are set, if not prompt the user
if [ -z "$RAD_USER" ]; then
    read -p "Enter your database username: " RAD_USER
    export RAD_USER="$RAD_USER"
fi

if [ -z "$RAD_PASSWORD" ]; then
    read -sp "Enter your database password: " RAD_PASSWORD
    echo
    export RAD_PASSWORD="$RAD_PASSWORD"
fi

if [ -z "$RAD_SERVER" ]; then
    read -p "Enter your database server: " RAD_SERVER
    export RAD_SERVER="$RAD_SERVER"
fi

if [ -z "$RAD_DATABASE" ]; then
    read -p "Enter your database name: " RAD_DATABASE
    export RAD_DATABASE="$RAD_DATABASE"
fi

if [ -z "$AZURE_CLIENT_ID" ]; then
    read -p "Enter your Azure client ID: " AZURE_CLIENT_ID
    export AZURE_CLIENT_ID="$AZURE_CLIENT_ID"
fi

if [ -z "$AZURE_TENANT_ID" ]; then
    read -p "Enter your Azure tenant ID: " AZURE_TENANT_ID
    export AZURE_TENANT_ID="$AZURE_TENANT_ID"
fi

# Save environment variables to .env file
cat <<EOF > "$SCRIPT_DIR/.env"
RAD_USER=$RAD_USER
RAD_PASSWORD=$RAD_PASSWORD
RAD_SERVER=$RAD_SERVER
RAD_DATABASE=$RAD_DATABASE
AZURE_CLIENT_ID=$AZURE_CLIENT_ID
AZURE_TENANT_ID=$AZURE_TENANT_ID
EOF

# Install Poetry if not already installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry could not be found, installing..."
    curl -sSL https://install.python-poetry.org | python3 - > /dev/null 2>&1
    export PATH="$HOME/.local/bin:$PATH"
fi

# Ensure Poetry is in the PATH
export PATH="$HOME/.local/bin:$PATH"

# Set PYTHONPATH to include the src directory
export PYTHONPATH="$SRC_DIR:$PYTHONPATH"

# Change to project root where pyproject.toml is located
cd "$PROJECT_ROOT"

# Install dependencies without development dependencies
echo "Installing dependencies..."
if ! poetry install --no-root > /dev/null 2>&1; then
    echo "Failed to install dependencies."
    exit 1
fi

# Kill any process using port 8000
kill_process_on_port 8000

# Start the FastAPI application
echo "Starting FastAPI application..."
if ! poetry run uvicorn src.serve.wsgi:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 & then
    echo "Failed to start FastAPI application."
    exit 1
fi
UVICORN_PID=$!

# Wait for FastAPI to start
sleep 5

# Check if uvicorn is running
if ! ps -p "$UVICORN_PID" > /dev/null
then
    echo "Failed to start FastAPI application."
    exit 1
fi

# Kill any process using port 8501
kill_process_on_port 8501

# Start the Streamlit application
echo "Starting Streamlit application..."
if ! poetry run streamlit run "$SERVE_DIR/streamlit_app.py" > /dev/null 2>&1 & then
    echo "Failed to start Streamlit application."
    kill "$UVICORN_PID"
    exit 1
fi
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 5

# Check if Streamlit is running
if ! ps -p "$STREAMLIT_PID" > /dev/null
then
    echo "Failed to start Streamlit application."
    kill "$UVICORN_PID"
    exit 1
fi

echo "Both FastAPI and Streamlit applications started successfully."