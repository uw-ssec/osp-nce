"""
Helpers to get review matrix autofillables from RAD and the Extension Forms.
"""
from pathlib import Path

import pandas as pd

import connect
import utils.path_utils


# TODO---Smarter relative pathing
def get_rad_data(mod_id, conn):
    """
    Get relevant data related to the mod_id from RAD.
    
    Args:
    - mod_id (str): The MOD ID users can see in SAGE.
    - conn (sqlalchemy.engine.base.Connection): A connection to RAD.
    """
    query_path = utils.path_utils.get_query_path("rad.sql")
    df_rad = connect.fetch_query_result(
        query_path, conn, params={"mod_id": mod_id}
    )
    # TODO---Clean RAD data before returning
    return df_rad


def get_extension_form_data(awrd_id):
    """Get relevant data from MS access extension form.

    Just a stub for now, but eventually we will need to filter the extension
    form data to the record containing the matching AwardNumber and the biggest
    ID (sequence number). We will also want to parse the associated award lines\
    and grants.
    
    Args:
    - awrd_id (str): The Workday ID of the Award. Should only be one per 
        submitted extension form.
    """
    pass


def autofill_erm_fields(mod_id, conn):
    """Fetch data to populate autofillable extension review matrix fields.
    
    Args:
    - mod_id (str): The MOD ID users can see in SAGE.
    - conn (sqlalchemy.engine.base.Connection): A connection to RAD.

    Returns:
    - TBD
    """
    # Get data from RAD pertaining to the MOD request
    df_rad = get_rad_data(mod_id, conn)

    # Use the award  number to fetch the corresponding extension form
    df_xform = get_extension_form_data(df_rad["AwardNumber"])

    # Create a dictionary containing hypothesized ERM fields 
    pass
