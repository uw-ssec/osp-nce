import sys

sys.path.append("../")
from libs.sql_connector import SQLConnector
import logging

logger = logging.getLogger(__name__)

test_filename = "../../sql/nonprod_rad.sql"

if __name__ == "__main__":
    logging.info("Starting test")
    try:
        sql_connecter = SQLConnector()
        with open(test_filename, "r") as test_query_file:
            test_query = test_query_file.read()
        df = None
        df = sql_connecter.query_from_file(test_filename, params={"mod_id": "MOD25169"})
        if df is not None:
            print(df.head())
            logging.info("Test Passed")
        else:
            logging.error("Test Failed: connection established but no data returned")
    except Exception as e:
        logging.error(f"Test failed with error {e}")
