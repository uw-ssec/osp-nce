import sys
import uvicorn
import os

from libs.sql_connector import SQLConnector
from libs.sharepoint_connector import SharepointConnector
import streamlit as st
from typing import Dict
from datetime import datetime
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Get database credentials from environment variables
db_user = os.getenv("RAD_USER")
db_password = os.getenv("RAD_PASSWORD")
db_server = os.getenv("RAD_SERVER")
db_name = os.getenv("RAD_DATABASE")
client_id = os.getenv("AZURE_CLIENT_ID")
tenant_id = os.getenv("AZURE_TENANT_ID")


sql_connector = SQLConnector(user=db_user, password=db_password, server=db_server, database=db_name)
sharepoint_connector = SharepointConnector(client_id=client_id, tenant_id=tenant_id)


app = FastAPI()

@app.get("/ping/")
async def ping() -> Dict[str, str]:
    health = True
    status = 200 if health else 404
    message = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Status Code {status}, health check {'passed' if health else 'failed'}"
    )
    return {"message": message}

@app.get("/prompt_azure_mfa/")
async def prompt_azure_mfa(sharepoint_connector=sharepoint_connector) -> Dict[str, str]:
    try:
        auth_message = sharepoint_connector.prompt_user()
        return {"auth_message": auth_message, "Status": '200'}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}
    
@app.get("/acquire_access_token/")
async def acquire_access_token(sharepoint_connector=sharepoint_connector):
    try:
        access_token = sharepoint_connector.acquire_token()
        return {"Status": '200'}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}

@app.get("/run/")
async def run(mod_id: str, 
              sql_connector=sql_connector,
              sharepoint_connector=sharepoint_connector) -> Dict[str, str]:
    try:
        query_file = "../../sql/test_query.sql"
        with open(query_file, "r") as f:
            query = f.read()
        df = sql_connector.query_database(query)
        
        return {"Data": df.to_json(), "Status": '200'}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("serve.wsgi:app", host="0.0.0.0", port=8000)