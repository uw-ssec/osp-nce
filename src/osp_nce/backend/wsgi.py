import logging
from datetime import datetime

import uvicorn
from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from osp_nce.backend.libs.autofiller import ERMAutoFiller
from osp_nce.backend.libs.sharepoint_connector import SharepointConnector
from osp_nce.backend.libs.sql_connector import SQLConnector

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    rad_user: str = Field(..., env="RAD_USER")
    rad_password: str = Field(..., env="RAD_PASSWORD")
    rad_server: str = Field(..., env="RAD_SERVER")
    rad_database: str = Field(..., env="RAD_DATABASE")
    azure_client_id: str = Field(..., env="AZURE_CLIENT_ID")
    azure_tenant_id: str = Field(..., env="AZURE_TENANT_ID")

    class Config:
        env_file = ".env"


# Load the secrets if they are not already set
settings = Settings()


class PingResponse(BaseModel):
    message: str


class AuthResponse(BaseModel):
    auth_message: str


class AutofillRequest(BaseModel):
    mod_id: str


class AutofillResponse(BaseModel):
    data: dict


# Intialize app and define endpoint functionality
app = FastAPI(title="AutoFill Backend for GRACE")
health_router = APIRouter()
auth_router = APIRouter()
autofill_router = APIRouter()


@health_router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    """
    A basic health check endpoint.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{now} - Health check passed."
    return PingResponse(message=message)


@auth_router.get("/prompt_azure_mfa", response_model=AuthResponse)
async def prompt_azure_mfa(
    sharepoint_connector: SharepointConnector = Depends(lambda: app.state.sharepoint_connector),
) -> AuthResponse:
    """
    Prompt the user for Azure MFA via the SharePoint Connector.
    """
    auth_message = sharepoint_connector.prompt_user()
    return AuthResponse(auth_message=auth_message)


@auth_router.get("/acquire_access_token", response_model=AuthResponse)
async def acquire_access_token(
    sharepoint_connector: SharepointConnector = Depends(lambda: app.state.sharepoint_connector),
) -> AuthResponse:
    """
    Acquire an access token upon user completion of their device-code flow.
    """
    sharepoint_connector.acquire_token()
    return AuthResponse(auth_message="Access token acquired successfully.")


@autofill_router.post("/autofill_erm", response_model=AutofillResponse)
async def autofill_erm(
    request: AutofillRequest,
    sql_connector: SQLConnector = Depends(lambda: app.state.sql_connector),
    sharepoint_connector: SharepointConnector = Depends(lambda: app.state.sharepoint_connector),
) -> AutofillResponse:
    """
    Perform Review Matrix autofill using an `ERMAutoFiller`.
    """
    erm_autofiller = ERMAutoFiller(request.mod_id, sql_connector, sharepoint_connector)
    erm_autofiller.autofill()
    return AutofillResponse(data=erm_autofiller.to_dict())


@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialize data connectors for RAD and SharePoint on startup.
    """
    app.state.sql_connector = SQLConnector(
        user=settings.rad_user,
        password=settings.rad_password,
        server=settings.rad_server,
        database=settings.rad_database,
    )
    app.state.sharepoint_connector = SharepointConnector(
        client_id=settings.azure_client_id, tenant_id=settings.azure_tenant_id
    )
    logger.info("Initialized SQLConnector and SharepointConnector.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Cleanup resources on shutdown.
    """
    if hasattr(app.state, "sql_connector"):
        app.state.sql_connector.close()
    logger.info("Cleaned up resources.")


@app.exception_handler(Exception)
async def global_exception_handler(exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})


# Include routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(autofill_router, prefix="/autofill")


if __name__ == "__main__":
    uvicorn.run("osp_nce.backend.wsgi2:app", host="0.0.0.0", port=8000, reload=True)
