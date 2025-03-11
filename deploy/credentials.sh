#!/bin/bash

# Set project paths
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Move to project root
cd "$PROJECT_ROOT" || exit 1

# Load environment variables from .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    while IFS= read -r line; do
        if [[ -n "$line" && "$line" != \#* ]]; then
            # Remove the surrounding double quotes
            line=$(echo "$line" | sed 's/^"\(.*\)"$/\1/')
            eval "export $line"
        fi
    done < "$PROJECT_ROOT/.env"
fi

# Prompt for username if not set
prompt_for_username() {
    local var_name="$1"
    local prompt_text="$2"
    if [ -z "${!var_name}" ]; then
        read -rp "$prompt_text: " $var_name
        export $var_name="netid\\${!var_name}"
    fi
}

# Prompt for secret if not set
prompt_for_secret() {
    local var_name="$1"
    local prompt_text="$2"
    if [ -z "${!var_name}" ]; then
        read -rsp "$prompt_text: " $var_name
        echo # New line for formatting
    fi
}

# Prompt for variables if not set
prompt_for_var() {
    local var_name="$1"
    local prompt_text="$2"
    if [ -z "${!var_name}" ]; then
        read -rp "$prompt_text: " $var_name
        export $var_name="${!var_name}"
    fi
}

# Prompt for missing environment variables
prompt_for_username "RAD_USER" "Enter your database username"
prompt_for_secret "RAD_PASSWORD" "Enter your database password"
prompt_for_var "RAD_SERVER" "Enter your database server"
prompt_for_var "RAD_DATABASE" "Enter your database name"
prompt_for_var "AZURE_CLIENT_ID" "Enter your Azure client ID"
prompt_for_var "AZURE_TENANT_ID" "Enter your Azure tenant ID"
prompt_for_var "EXTENSION_FORMS_SHORT_LINK" "Enter your extension forms short link"

# Ensure .env exists with proper permissions
touch "$PROJECT_ROOT/.env"
chmod 644 "$PROJECT_ROOT/.env"

# Save environment variables to .env file safely with single quotes
cat <<EOF >"$PROJECT_ROOT/.env"
RAD_USER='${RAD_USER}'
RAD_PASSWORD='${RAD_PASSWORD}'
RAD_SERVER='${RAD_SERVER}'
RAD_DATABASE='${RAD_DATABASE}'
AZURE_CLIENT_ID='${AZURE_CLIENT_ID}'
AZURE_TENANT_ID='${AZURE_TENANT_ID}'
EXTENSION_FORMS_SHORT_LINK='${EXTENSION_FORMS_SHORT_LINK}'
EOF