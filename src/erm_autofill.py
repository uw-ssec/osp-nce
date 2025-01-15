"""
Helpers to get review matrix autofillables from RAD and the Extension Forms.
"""

import os

import pandas as pd

import connect


# TODO---Smarter relative pathing
def get_rad_data(mod_id, conn):
    """Get relevant data related to the mod_id from RAD."""
    query_path = "sql/rad.sql"
    df_rad = connect.fetch_query_result(
        query_path, conn, params={"mod_id": mod_id}
    )
    # Clean RAD data

    return df_rad


def get_extension_form_data(awrd_id):
    """Get relevant data from MS access extension form."""

    # Filter Extension Form data to record with matching AwardNumber and biggest
    # ID (sequence number)
    pass


def autofill_erm_fields(mod_id, conn):
    """Fetch data to populate autofillable extension review matrix fields."""
    # Get data from RAD pertaining to the MOD request

    # Use the AWRD number to fetch the corresponding extension form

    # Use the data to create a response packet with hypothesized ERM fields 
    pass
