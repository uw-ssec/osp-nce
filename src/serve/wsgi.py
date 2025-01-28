import sys
import uvicorn
import os

from libs.sql_connector import SQLConnector
import streamlit as st
from typing import Dict
from datetime import datetime
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Get database credentials from environment variables
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_server = os.getenv("DB_SERVER")
db_name = os.getenv("DB_DATABASE")

sql_connector = SQLConnector(user=db_user, password=db_password, server=db_server, database=db_name)
streamlit_app = StreamLitApp()

app = FastAPI()

@app.get("/ping/")
async def ping() -> Dict[str, str]:
    health = True
    status = 200 if health else 404
    message = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Status Code {status}, health check {'passed' if health else 'failed'}"
    )
    return {"message": message}

@app.get("/run/")
async def run(pi_name: str, mod_id: str) -> Dict[str, str]:
    try:
        query_file = "../../sql/test_query.sql"
        with open(query_file, "r") as f:
            query = f.read()
        df = sql_connector.query_database(query)
        return {"Data": df.to_json(), "Status": 200}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("serve.wsgi:app", host="0.0.0.0", port=8000)