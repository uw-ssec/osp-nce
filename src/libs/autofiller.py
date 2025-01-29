import os

from dotenv import load_dotenv
from sharepoint_connector import SharepointConnector
from sql_connector import SQLConnector
import pandas as pd

from business_logic import process_query_result

# for sharepoint connection
SHORT_LINK = "https://uwnetid.sharepoint.com/:x:/s/og_osp_managers/EQaeSnjtfdFGjXYAk_sa0w0B79v0wjCaesSKdTe96lTvfg?e=5QgFxk" 
LOCAL_FILE_PATH = "test_file.xlsx"

# for sql connection
RAD_QUERY_FILE = "../../sql/nonprod_rad.sql"

class Autofiller:
    """
    Autofiller class that takes in parameters, connects to the RAD and Sharepoint databases, and returns the autofilled form.
    
    Parameters:
        - params: dictionary of parameters to pass to the RAD query
        - rad_connector: SQLConnector object to connect to the RAD database
        - sharepoint_connector: SharepointConnector object to connect to the Sharepoint database
    """
    def __init__(self, params, rad_connector, sharepoint_connector):
        """
        Initializes the Autofiller object.
        
        Parameters:
            - params: dictionary of parameters to pass to the RAD query
            - rad_connector: SQLConnector object to connect to the RAD database
            - sharepoint_connector: SharepointConnector object to connect to the Sharepoint database
        """
        
        rad_df = rad_connector.query_from_file(RAD_QUERY_FILE, params=params)
        
        sharepoint_df = sharepoint_connector.read_extension_forms_from_short_link(SHORT_LINK)
        
        # check that rad_df and sharepoint_df are one row each
        
        if len(rad_df) == 1 and len(sharepoint_df) == 1:
            self.df = pd.concat([rad_df, sharepoint_df], axis=1)
        
        else:
            raise ValueError("RAD and Sharepoint queries must return exactly one row")
    
    def autofill(self):
        """
        Autofills the form by processing the query result.
        
        Returns:
            - JSON mapping the abbreviation for each question in the form to its answer
        """
        
        return process_query_result(self.df)
    
        
        
        
        
        