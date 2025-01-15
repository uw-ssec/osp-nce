"""
Database functions to connect to and query RAD. 

This code requires certain environment variables to be set for authentication. 
If these variables are not set, it will attempt to load them from a .env file.

Requirements:
- Environment variables:
    - DB_USER: Your netid (e.g "jdoe", not 'jdoe@uw.edu')
    - DB_PASSWORD: Your netid password
    - DB_SERVER: "rad-rpt-prod.db.oris.washington.edu"
    - DB_DATABASE: "master"
"""

import os

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv


def get_connection():
    """Establish a connection to the EDW using SQLAlchemy.

    Raises:
    - EnvironmentError: If one or more environment variables are not set.

    Returns:
    - sqlalchemy.engine.base.Connection: A connection to the EDW.
    """
    REQUIRED_VARS = ["DB_USER", "DB_PASSWORD", "DB_SERVER"]

    # Load environment variables from .env file if not already set
    if not all(os.getenv(var) for var in REQUIRED_VARS):
        load_dotenv()

    # Resolve environment
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")

    if not all([user, password, server, database]):
        raise EnvironmentError("One or more environment variables are not set.")

    # Establish the database connection
    connection_url = sqlalchemy.engine.url.URL.create(
        drivername="mssql+pymssql",
        username=f"netid\\{user}",
        password=password,
        host=server,
        database=database,
    )
    engine = sqlalchemy.create_engine(connection_url)
    return engine.connect()


def fetch_query_result(query_path, conn, params=None):
    """Fetch the result of the SQL query located at the given file path.

    Args:
    - query_path: The path to the SQL query.
    - conn (sqlalchemy.engine.base.Connection): A database connection object.
    - params (dict, optional): A dictionary of parameters to substitute into
        the query.

    Returns:
    - pd.DataFrame: A DataFrame containing the result set of the query.
    """
    with open(query_path, "r") as query_file:
        query = query_file.read()
        if params:
            df = pd.read_sql(sqlalchemy.text(query), conn, params=params)
        else:
            df = pd.read_sql(sqlalchemy.text(query), conn)
        return df
