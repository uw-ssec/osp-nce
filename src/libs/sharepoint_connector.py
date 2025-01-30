import base64
from io import BytesIO

import msal
import pandas as pd
import requests


class SharepointConnector:
    """
    Connector for pulling files from SharePoint.

    Uses Azure AD device-flow to authenticate (for now). Parses shared links and
    downloads files using the Microsoft Graph API.

    Attributes:
        client_id (str): Azure AD application (client) ID.
        tenant_id (str): Azure AD tenant ID.
        scopes (list[str]): List of Graph permissions to request.
        authority (str): Azure AD authority URL (constructed from tenant_id).
        access_token (str or None): Current access token to use for requests.
    """

    def __init__(
        self, client_id, tenant_id, scopes=["Files.Read", "Files.Read.All"]
    ):
        """
        Initialize the connector with the required Azure AD application details.

        Args:
            client_id (str): Azure AD client (application) ID.
            tenant_id (str): Azure AD tenant ID (or domain).
            scopes (list[str], optional): List of Graph permissions to request.
                Defaults to ["Files.Read", "Files.Read.All"] if not provided.
        """
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scopes = scopes
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self._access_token = None
        self._flow = None
        self._app = None

    def prompt_user(self):
        """
        Use Azure AD device-flow to acquire an access token.

        Prompts the user to visit https://microsoft.com/devicelogin and enter a
        code. Stores the acquired token internally.

        Raises:
            ValueError: If device flow or token acquisition fails.
        """
        if not self.client_id:
            raise ValueError("Client ID must be provided in the constructor.")

        # Set up MSAL client for device flow authentication
        app = msal.PublicClientApplication(
            client_id=self.client_id, authority=self.authority
        )

        # Intiate authentication
        flow = app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise ValueError(
                "Failed to create device flow. Check Azure AD app registration."
            )
        self._flow = flow
        self._app = app
        return flow['message']

    def acquire_token(self):
        # Prompt the user to go to the link to enter an access code
        result = self._app.acquire_token_by_device_flow(self._flow)
        # Extract the access token from the result
        if "access_token" not in result:
            error_detail = result.get("error_description") or result.get(
                "error"
            )
            return (f"Error acquiring token: {error_detail}")
        else:
            self._access_token = result["access_token"]
            return ("Access token acquired successfully.")

    def get_item_info_from_short_link(self, short_link):
        """
        Use the Microsfot Graph API to decode a SharePoint short link.

        Args:
            short_link (str): The short link of the item to decode.

        Returns:
            dict: The parsed response from the Graph API containing site, drive,
                and item info.

        Raises:
            RuntimeError: If an error from the endpoint or no token exists.
        """
        if not self._access_token:
            raise RuntimeError(
                "Access token not found. Call acquire_token() first."
            )

        # Encode the short link into base64 (URL-safe, no padding).
        encoded_bytes = base64.urlsafe_b64encode(short_link.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8").rstrip("=")

        # Build the Graph API shares endpoint
        shares_endpoint = (
            f"https://graph.microsoft.com/v1.0/shares/u!{encoded_str}/driveItem"
        )
        headers = {"Authorization": f"Bearer {self._access_token}"}

        # Make the request to decode the short link
        response = requests.get(shares_endpoint, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Error from endpoint ({response.status_code}): {response.text}"
            )

        return response.json()

    def download_excel(
        self,
        site_id,
        drive_id,
        item_id,
        local_file_path="downloaded_file.xlsx",
    ):
        """
        Download a file from the site, drive, and item ID in SharePoint.

        Args:
            site_id (str): The site ID of the file in SharePoint.
            drive_id (str): The drive ID of the file in SharePoint.
            item_id (str): The item ID of the file in SharePoint.
            local_file_path (str, optional): The local path (including filename)
                to save the file. Defaults to 'downloaded_file.xlsx'.

        Raises:
            RuntimeError: If an error from the endpoint or no token exists.
        """
        # Ensure the access token is available
        if not self._access_token:
            raise RuntimeError(
                "Access token not found. Call acquire_token() first."
            )

        # Construct the download URL
        download_url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/"
            f"{drive_id}/items/{item_id}/content"
        )
        headers = {"Authorization": f"Bearer {self._access_token}"}

        # Make the request to download the file
        response = requests.get(download_url, headers=headers)
        if response.status_code == 200:
            with open(local_file_path, "wb") as file:
                file.write(response.content)
            print(f"File downloaded successfully at: {local_file_path}")
        else:
            raise RuntimeError(
                f"Error downloading file ({response.status_code}): {response.text}"
            )

    def download_excel_from_short_link(
        self, short_link, local_file_path="downloaded_file.xlsx"
    ):
        """
        Convenience method to download a file from a SharePoint short link.

        This method acquires a token (if not already acquired), decodes the
        short link, retrieves item info, and downloads the file to the specified
        local path.

        Args:
            short_link (str): The SharePoint short link to decode.
            local_file_path (str, optional): The local path (including filename)
                to save the file. Defaults to 'downloaded_file.xlsx'.

        Raises:
            RuntimeError: If token acquisition or file download fails.
        """
        # Ensure access token is available
        if not self._access_token:
            self.acquire_token()

        # Decode the short link and extract item metadata
        item_info = self.get_item_info_from_short_link(short_link)
        site_id = item_info["parentReference"]["siteId"]
        drive_id = item_info["parentReference"]["driveId"]
        item_id = item_info["id"]

        # Download the file to the specified local path
        self.download_excel(site_id, drive_id, item_id, local_file_path)

    def read_excel_from_short_link(
        self, short_link, header=None, skiprows=0, names=None
    ):
        """
        Read an Excel file from a SharePoint short link into a pandas DataFrame.

        This method acquires a token (if needed), decodes the short link,
        downloads the Excel file content in memory, and returns it as a
        DataFrame.

        Args:
            short_link (str): The SharePoint short link to decode.
            header (int, list of int, default 0): Row (0-indexed) to use for the 
                column labels of the parsed DataFrame.
            skiprows (int, list-like, default 0): Line numbers to skip 
                (0-indexed) or number of lines to skip (int) at the start of the 
                file.
            names (array-like, optional): List of column names to use. If file 
                contains no header row, then you should explicitly pass 
                header=None.

        Returns:
            pandas.DataFrame: The data read from the remote Excel file.

        Raises:
            RuntimeError: If token acquisition or file download fails.
        """
        # Ensure access token is available
        if not self._access_token:
            self.acquire_token()

        # Decode the short link and extract item metadata
        item_info = self.get_item_info_from_short_link(short_link)
        item_id = item_info["id"]
        drive_id = item_info["parentReference"]["driveId"]
        site_id = item_info["parentReference"]["siteId"]

        # Construct the download URL for the Excel file
        download_url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/"
            f"{drive_id}/items/{item_id}/content"
        )
        headers = {"Authorization": f"Bearer {self._access_token}"}

        # Download the file and convert its content into a DataFrame
        response = requests.get(download_url, headers=headers)
        if response.status_code == 200:
            return pd.read_excel(
                BytesIO(response.content),
                header=header,
                skiprows=skiprows,
                names=names,
            )
        else:
            raise RuntimeError(
                f"Error reading file ({response.status_code}): {response.text}"
            )

    def read_extension_forms_from_short_link(self, short_link):
        """
        Read the extension forms from the OSP Sharepoint site.

        This is a convenience method for pre-parsing a particular excel files
        (extension forms).

        Args:
            short_link (str): The SharePoint short link to the extension form
                submissions.

        Returns:
            pandas.DataFrame: Parsed extension forms, up to date. 
        """
        column_names = [
            "ID",
            "StartTime",
            "CompletionTime",
            "Email",
            "Name",
            "Question",
            "YourName",
            "YourName2",
            "YourEmail",
            "PIName",
            "UWAwardNumber",
            "IsRemainingBalanceMoreThan25Percent",
            "ExplanationForRemainingBalance",
            "RequestedEndDate",
            "isTemporaryExtensionRequest",
            "IsAwardInDeficit",
            "DeficitExplanation",
            "AlternativeNonSponsoredDepartmentalWorktag",
            "allDeliverablesSubmitted",
            "isNIH2PlusExtension",
            "WillPIMaintainMeasurableEffort",
            "ContinuingHumanSubjectsResearch",
            "CurrentIRBProtocolNumber",
            "IRBLocation",
            "IRBExpirationDate",
            "CurrentIRBProtocolNumber2",
            "IRBExpirationDate2",
            "IRBLocation2",
            "CurrentIRBProtocolNumber3",
            "AnimalResearchDone",
            "CurrentIACUCProtocolNumber",
            "IACUCExpirationDate",
            "CurrentIACUCProtocolNumber2",
            "IACUCExpirationDate2",
            "CurrentIACUCProtocolNumber3",
            "IACUCExpirationDate3",
            "CurrentIRBProtocolNumber4",
            "IRBLocation3",
            "IRBExpirationDate3",
            "isNewCostShare",
            "AdditionalComments",
            "AdditionalIRBProtocols",
            "AdditionalIRBProtocolDetails",
            "AdditionalIACUCProtocolDetails",
        ]
        df_forms_raw = self.read_excel_from_short_link(
            short_link,
            header=None,
            skiprows=2,
            names=column_names,
        )
        return df_forms_raw