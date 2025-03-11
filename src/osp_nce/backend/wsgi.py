import logging
import os
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI

from osp_nce.backend.libs.autofiller import ERMAutoFiller
from osp_nce.backend.libs.sharepoint_connector import SharepointConnector
from osp_nce.backend.libs.sql_connector import SQLConnector

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
async def startup_event() -> None:
    """
    Initialize data connectors for RAD and sharepoint on startup

    """
    app.state.sql_connector = SQLConnector(
        user=db_user, password=db_password, server=db_server, database=db_name
    )
    app.state.sharepoint_connector = SharepointConnector(client_id=client_id, tenant_id=tenant_id)
    logger.info("Initialized SQLConnector, SharepointConnector.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Cleanup resources at shutdown.
    """
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
async def ping() -> dict[str, str]:
    health = True
    status = 200 if health else 404
    message = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Status Code {status},"
        f" health check {'passed' if health else 'failed'}."
    )
    return {"message": message}


@app.get("/prompt_azure_mfa/")
async def prompt_azure_mfa(
    sharepoint_connector: SharepointConnector = Depends(get_sharepoint_connector),
) -> dict[str, str]:
    try:
        auth_message = sharepoint_connector.prompt_user()
        return {"auth_message": auth_message, "Status": "200"}
    except Exception as e:
        logger.error(f"Error in prompting MFA: {str(e)}")
        return {"error": str(e)}


@app.get("/acquire_access_token/")
async def acquire_access_token(
    sharepoint_connector: SharepointConnector = Depends(get_sharepoint_connector),
) -> dict[str, str]:
    try:
        sharepoint_connector.acquire_token()
        return {"Status": "200"}
    except Exception as e:
        logger.error(f"Error in acquiring token: {e}")
        return {"error": str(e)}


@app.post("/autofill_erm/")
async def autofill_erm(
    data: dict,
    sql_connector: SQLConnector = Depends(get_sql_connector),
    sharepoint_connector: SharepointConnector = Depends(get_sharepoint_connector),
) -> dict[str, str]:
    try:
        mod_id = data["mod_id"]
        erm_autofiller = ERMAutoFiller(mod_id, sql_connector, sharepoint_connector)
        erm_autofiller.autofill()
        # print(f"AUTOFILL: {erm_autofiller.to_dict()}")
        return {"Data": erm_autofiller.to_json(), "Status": "200"}
    except Exception as e:
        logger.error(f"Error in autofilling ERM: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("osp_nce.backend.wsgi:app", host="0.0.0.0", port=8000)
