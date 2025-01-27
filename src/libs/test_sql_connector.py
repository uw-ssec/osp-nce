import os

from dotenv import load_dotenv

from sql_connector import SQLConnector

# Replace with your actual test parameters
load_dotenv(override=True)
DB_USER = os.getenv("RAD_USER")
DB_PASSWORD = os.getenv("RAD_PASSWORD")
DB_SERVER = os.getenv("RAD_SERVER")
DB_DATABASE = os.getenv("RAD_DATABASE")
TEST_QUERY_FILE = "../../sql/nonprod_rad.sql"
TEST_PARAMS = {"mod_id": "MOD25169"}


def main():
    """
    Test the SQLConnector class.

    Attempts to execute a SQL query from a file and fetch data.
    """
    try:
        # Initialize the SQLConnector
        print("Initializing SQLConnector...")
        sql_connector = SQLConnector(
            DB_USER,
            DB_PASSWORD,
            DB_SERVER,
            DB_DATABASE,
        )

        # Execute the query
        print("Executing the SQL query...")
        df = sql_connector.query_from_file(TEST_QUERY_FILE, params=TEST_PARAMS)

        # Check the results
        if df is not None and not df.empty:
            print("Query executed successfully. First few rows of the result:")
            print(df.head())
        else:
            print("Test failed: Query executed, but no data was returned.")

    except Exception as e:
        print(f"Error during testing: {e}")


if __name__ == "__main__":
    main()
