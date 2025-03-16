from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.cloud import secretmanager
import subprocess

class AuthHandler():
    def __init__(self):
        self.secret_name = "msds-grace-api-key"
        self.version = "latest"
        self.client = self.get_secrets_client()
        self.project_id = self.get_project_id()
        self.api_key = self.get_api_key()

    def get_project_id(self):
        project_result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True, text=True, check=True
        )
        project_id = project_result.stdout.strip()
        return project_id
    
    def get_auth_token(self):
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, check=True
        )
        token = result.stdout.strip()
        return token
    
    def get_secrets_client(self):
        auth_token = self.get_auth_token()
        credentials = Credentials(token=auth_token)
        client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        return client 
    
    def get_api_key(self):
        name = f"projects/{self.project_id}/secrets/{self.secret_name}/versions/{self.version}"
        response = self.client.access_secret_version(request={"name": name})
        api_key = response.payload.data.decode("UTF-8")
        return api_key


