import sys 
sys.path.append("../")
from libs.sql_connecter import SQLConnecter
import logging 

logger = logging.getLogger(__name__)

test_filename = "../../sql/test_query.sql"

if __name__ == "__main__":
    logging.info("Starting test")
    try:
        sql_connecter = SQLConnecter()
        with open(test_filename, "r") as test_query_file:
            test_query = test_query_file.read()
        df = None
        df = sql_connecter.query_database(test_query)
        if df is not None:
            logging.info("Test Passed")
        else:
            logging.error("Test Failed: connection established but no data returned")
    except Exception as e:
        logging.error(f"Test failed with error {e}")