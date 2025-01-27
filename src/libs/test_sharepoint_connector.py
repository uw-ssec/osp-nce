import os

from dotenv import load_dotenv
from sharepoint_connector import SharepointConnector

# Replace with your actual values for testing
load_dotenv(override=False)
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
SHORT_LINK = "https://uwnetid.sharepoint.com/:x:/s/og_osp_managers/EQaeSnjtfdFGjXYAk_sa0w0B79v0wjCaesSKdTe96lTvfg?e=5QgFxk" 
LOCAL_FILE_PATH = "test_file.xlsx"

def main():
    """
    Test the SharepointConnector class.

    Attempts to both download the extension forms and read them into a 
    DataFrame. Authentication link for device flow should print in terminal.
    """
    try:
        # Initialize the connector
        connector = SharepointConnector(
            client_id=CLIENT_ID,
            tenant_id=TENANT_ID,
        )

        # Test downloading the file
        print("Downloading file from short link...")
        connector.download_excel_from_short_link(SHORT_LINK, LOCAL_FILE_PATH)
        print(f"File downloaded successfully to: {LOCAL_FILE_PATH}")

        # Test reading the file into a DataFrame
        print("Reading the downloaded file into a DataFrame...")
        df = connector.read_excel_from_short_link(SHORT_LINK)
        print("First few rows of the DataFrame:")
        print(df.head())

    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()
