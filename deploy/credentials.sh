#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$0")
# Define project paths
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd $PROJECT_ROOT
# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Check if environment variables are set, if not prompt the user
if [ -z "$RAD_USER" ]; then
    read -p "Enter your database username: " RAD_USER
    RAD_USER="netid\\$RAD_USER"
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

if [ -z "$EXTENSION_FORMS_SHORT_LINK" ]; then
    read -p "Enter your extension forms short link: " EXTENSION_FORMS_SHORT_LINK
    export EXTENSION_FORMS_SHORT_LINK="$EXTENSION_FORMS_SHORT_LINK"
fi

touch $PROJECT_ROOT/.env
chmod 644 $PROJECT_ROOT/.env

# Save environment variables to .env file
cat <<EOF > "$PROJECT_ROOT/.env"
RAD_USER="netid\\edouas"
RAD_PASSWORD=$RAD_PASSWORD
RAD_SERVER=$RAD_SERVER
RAD_DATABASE=$RAD_DATABASE
AZURE_CLIENT_ID=$AZURE_CLIENT_ID
AZURE_TENANT_ID=$AZURE_TENANT_ID
EXTENSION_FORMS_SHORT_LINK=$EXTENSION_FORMS_SHORT_LINK
EOF



