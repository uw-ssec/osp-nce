from io import BytesIO
import base64

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from backend.libs.sharepoint_connector import SharepointConnector


#
# Fixtures
#
@pytest.fixture
def connector():
    """
    Create a SharepointConnector with dummy parameters for testing.
    """
    return SharepointConnector(client_id="test_client_id", tenant_id="test_tenant_id")


#
# Initialization Tests
#
def test_initialization(connector):
    """Test that the SharepointConnector initializes correctly."""
    assert connector.client_id == "test_client_id"
    assert connector.tenant_id == "test_tenant_id"
    assert "Files.Read.All" in connector.scopes
    assert connector.authority == "https://login.microsoftonline.com/test_tenant_id"


#
# Device Flow Tests
#
@patch("msal.PublicClientApplication")
def test_prompt_user_success(mock_public_client, connector):
    """
    Test that `prompt_user()` correctly initiates a device flow and stores attributes.
    """
    # Set up the mock to simulate a successful device flow initiation.
    mock_app_instance = mock_public_client.return_value
    mock_flow = {
        "user_code": "ABCDEFG",
        "message": "Go to https://microsoft.com/devicelogin and enter ABCDEFG",
    }
    mock_app_instance.initiate_device_flow.return_value = mock_flow

    # Call the method under test.
    message = connector.prompt_user()

    # Assert that the MSAL client was correctly instantiated.
    mock_public_client.assert_called_once_with(
        client_id=connector.client_id,
        authority=connector.authority,
    )

    # Assert that initiate_device_flow was called with the proper scopes.
    mock_app_instance.initiate_device_flow.assert_called_once_with(
        scopes=connector.scopes,
    )

    # Verify that the returned message and stored attributes are correct.
    assert message == mock_flow["message"]
    assert connector._flow == mock_flow
    assert connector._app == mock_app_instance


@patch("msal.PublicClientApplication")
def test_prompt_user_failure_no_user_code(mock_public_client, connector):
    """
    Test that `prompt_user()` raises a RuntimeError if the repsonse contains no user code.
    """
    mock_app_instance = mock_public_client.return_value

    # Simulate a device flow response missing a user_code.
    mock_app_instance.initiate_device_flow.return_value = {
        "message": "test_msg_no_code"
    }

    with pytest.raises(
        RuntimeError,
        match="No user_code in device flow. Check Azure AD app registration.",
    ):
        connector.prompt_user()


def test_prompt_user_failure_no_client_id(connector):
    """
    Test that `prompt_user()` raises an AttributeError if the connector has no client id.
    """
    # Create a connector with no client_id.
    connector = SharepointConnector(client_id=None, tenant_id="test_tenant_id")

    with pytest.raises(
        AttributeError, match="Client ID must be provided in the constructor."
    ):
        connector.prompt_user()


def test_acquire_token_success(connector):
    """
    Test that `acquire_token()` stores the access token upon success.
    """
    # Ensure the flow has been initiated.
    connector._flow = True

    # Simulate a successful token acquisition.
    with patch.object(connector, "_app", new_callable=MagicMock) as mock_app:
        mock_app.acquire_token_by_device_flow.return_value = {
            "access_token": "test_access_token"
        }
        connector.acquire_token()
        assert connector._access_token == "test_access_token"


def test_acquire_token_failure(connector):
    """
    Test that `acquire_token()` raises a RuntimeError when acquisition fails.
    """
    connector._flow = True

    # Simulate a token acquisition failure.
    with patch.object(connector, "_app", new_callable=MagicMock) as mock_app:
        mock_app.acquire_token_by_device_flow.return_value = {
            "error": "test_error_description",
        }
        with pytest.raises(RuntimeError, match="Error acquiring token"):
            connector.acquire_token()


#
# Graph API Tests
#
@patch("requests.get")
def test_get_item_info_from_short_link_success(mock_get, connector):
    """
    Test that `get_item_info_from_short_link` returns the parsed JSON when
    the Graph endpoint responds with status_code 200.
    """
    connector._access_token = "dummy_token"

    # Prepare a mock response for a successful call.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "12345",
        "parentReference": {"driveId": "drive-abc", "siteId": "site-xyz"},
    }
    mock_get.return_value = mock_response

    # Parse a dummy short link
    short_link = "https://short.link/demo"
    result = connector.get_item_info_from_short_link(short_link)

    # Assert that the returned JSON is parsed as expected.
    assert result["id"] == "12345"
    assert result["parentReference"]["siteId"] == "site-xyz"
    assert result["parentReference"]["driveId"] == "drive-abc"

    # Compute the expected URL.
    encoded_bytes = base64.urlsafe_b64encode(short_link.encode())
    encoded_str = encoded_bytes.decode().strip("=")
    expected_url = f"https://graph.microsoft.com/v1.0/shares/u!{encoded_str}/driveItem"

    # Ensure the proper request was made.
    mock_get.assert_called_once_with(
        expected_url, headers={"Authorization": "Bearer dummy_token"}
    )


@patch("requests.get")
def test_get_item_info_from_short_link_failure_unauthorized(mock_get, connector):
    """
    Test that `get_item_info_from_short_link` raises a RuntimeError when
    the Graph endpoint returns a non-200 status code.
    """
    connector._access_token = "dummy_token"

    # Prepare a mock response simulating an unauthorized error.
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_get.return_value = mock_response

    with pytest.raises(RuntimeError, match="Error from endpoint"):
        connector.get_item_info_from_short_link("some_short_link")


#
# File Download Tests: download_excel
#
@patch("requests.get")
def test_download_excel_success(mock_get, connector, tmp_path):
    """
    Test that `download_excel` writes file content to a local path on success.
    """
    connector._access_token = "dummy_token"

    # Create a mock response simulating a successful file download.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake binary content"
    mock_get.return_value = mock_response

    # Use pytest's tmp_path fixture to get a temporary file path.
    local_file_path = tmp_path / "test_file.xlsx"

    # Call the method under test.
    connector.download_excel(
        site_id="site123",
        drive_id="drive123",
        item_id="item123",
        local_file_path=str(local_file_path),
    )

    # Verify that the file was written with the expected content.
    with open(local_file_path, "rb") as f:
        written_content = f.read()
    assert written_content == b"fake binary content"

    # Verify the correct URL and headers were used in the GET request.
    expected_url = (
        "https://graph.microsoft.com/v1.0/sites/site123/"
        "drives/drive123/items/item123/content"
    )
    mock_get.assert_called_once_with(
        expected_url, headers={"Authorization": "Bearer dummy_token"}
    )


@patch("requests.get")
def test_download_excel_failure(mock_get, connector):
    """
    Test that `download_excel` raises a RuntimeError if the file download fails.
    """
    connector._access_token = "dummy_token"

    # Simulate a failed download response.
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "File not found"
    mock_get.return_value = mock_response

    with pytest.raises(RuntimeError, match="Error downloading file"):
        connector.download_excel("site123", "drive123", "item123")


#
# Excel Read Tests: read_excel_from_short_link
#
@patch("requests.get")
@patch.object(SharepointConnector, "get_item_info_from_short_link")
def test_read_excel_from_short_link_success(mock_get_item_info, mock_get, connector):
    """
    Test that `read_excel_from_short_link` returns a DataFrame when the Graph API 
    endpoint responds with valid Excel file content.
    """
    connector._access_token = "dummy_token"

    # Simulate a successful item info retrieval.
    mock_get_item_info.return_value = {
        "id": "dummy_item_id",
        "parentReference": {"driveId": "dummy_drive_id", "siteId": "dummy_site_id"},
    }

    # Create an in-memory Excel file.
    df_test = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    excel_buffer = BytesIO()
    df_test.to_excel(excel_buffer, index=False)
    excel_bytes = excel_buffer.getvalue()

    # Simulate a successful file download response.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = excel_bytes
    mock_get.return_value = mock_response

    # Attempt to acquire the dummy content and load it into a DataFrame
    df_excel = connector.read_excel_from_short_link("dummy_short_link", header=0)
    assert not df_excel.empty
    assert list(df_excel.columns) == ["A", "B"]
    assert df_excel.iloc[0].to_dict() == {"A": 1, "B": 3}


@patch("requests.get")
@patch.object(SharepointConnector, "get_item_info_from_short_link")
def test_read_excel_from_short_link_failure(mock_get_item_info, mock_get, connector):
    """
    Test that `read_excel_from_short_link` raises a RuntimeError when the download fails.
    """
    connector._access_token = "dummy_token"

    # Simulate successful retrieval of item info.
    mock_get_item_info.return_value = {
        "id": "dummy_item_id",
        "parentReference": {"driveId": "dummy_drive_id", "siteId": "dummy_site_id"},
    }

    # Simulate a failed file download response.
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_get.return_value = mock_response

    with pytest.raises(RuntimeError, match="Error reading file"):
        connector.read_excel_from_short_link("dummy_short_link")
