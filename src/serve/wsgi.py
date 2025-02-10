import sys
import uvicorn
import os
import logging

from libs.sql_connector import SQLConnector
from libs.sharepoint_connector import SharepointConnector
from libs.erm_autofiller import ERMAutofiller
import streamlit as st
from typing import Dict
from datetime import datetime
from fastapi import FastAPI, Depends

logger = logging.getLogger(__name__)

# Get database credentials from environment variables
db_user = os.getenv("RAD_USER")
db_password = os.getenv("RAD_PASSWORD")
db_server = os.getenv("RAD_SERVER")
db_name = os.getenv("RAD_DATABASE")
client_id = os.getenv("AZURE_CLIENT_ID")
tenant_id = os.getenv("AZURE_TENANT_ID")

# Create FastAPI app
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize connectors at startup."""
    app.state.sql_connector = SQLConnector(
        user=db_user, password=db_password, server=db_server, database=db_name
    )
    app.state.sharepoint_connector = SharepointConnector(
        client_id=client_id, tenant_id=tenant_id
    )
    logger.info("Initialized SQLConnector and SharepointConnector.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources at shutdown."""
    if hasattr(app.state, "sql_connector"):
        app.state.sql_connector.close()  # Ensure proper cleanup
    logger.info("Cleaned up resources.")


# Dependency to retrieve the singleton instance of SQLConnector
def get_sql_connector():
    return app.state.sql_connector


# Dependency to retrieve the singleton instance of SharepointConnector
def get_sharepoint_connector():
    return app.state.sharepoint_connector


@app.get("/ping/")
async def ping() -> Dict[str, str]:
    health = True
    status = 200 if health else 404
    message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Status Code {status}, health check {'passed' if health else 'failed'}"
    return {"message": message}


@app.get("/prompt_azure_mfa/")
async def prompt_azure_mfa(
    sharepoint_connector: SharepointConnector = Depends(
        get_sharepoint_connector,
    )
) -> Dict[str, str]:
    try:
        auth_message = sharepoint_connector.prompt_user()
        return {"auth_message": auth_message, "Status": "200"}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}


@app.get("/acquire_access_token/")
async def acquire_access_token(
    sharepoint_connector: SharepointConnector = Depends(get_sharepoint_connector),
) -> Dict[str, str]:
    try:
        sharepoint_connector.acquire_token()
        return {"Status": "200"}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}


@app.get("/run/")
async def run(
    mod_id: str,
    sql_connector: SQLConnector = Depends(get_sql_connector),
    sharepoint_connector: SharepointConnector = Depends(get_sharepoint_connector),
) -> Dict[str, str]:
    try:
        erm_autofiller = ERMAutofiller(mod_id, sql_connector, sharepoint_connector)
        erm_autofiller.autofill()
        print(erm_autofiller.to_json())
        return {"Data": erm_autofiller.to_json(), "Status": "200"}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("serve.wsgi:app", host="0.0.0.0", port=8000)
