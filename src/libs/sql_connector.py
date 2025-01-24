import os

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv


class SQLConnector:
    """A class to establish an SQL database connection and execute queries.

    Attributes:
        required_vars (list): Environment variables required for DB connection.
        user (str): Database username.
        password (str): Database password.
        server (str): Database server hostname.
        database (str): Database name.
        engine (sqlalchemy.engine.Engine): SQLAlchemy query engine.
    """

    def __init__(self, driver="mssql+pymssql"):
        """Initialize the SQLConnector.

        Check for required environment variables. If they're not set, attempt
        to load them from a .env file. Then initialize an SQLAlchemy engine for
        executing queries.

        Args:
            driver (str): The SQLAlchemy driver name. Defaults to the
                "mssql+pymssql" driver, which is used by RAD and the EDW.

        Raises:
            EnvironmentError: If one or more environment variables are not set.
        """
        self.required_vars = [
            "DB_USER",
            "DB_PASSWORD",
            "DB_SERVER",
            "DB_DATABASE",
        ]

        # Attempt to load from .env if any required var is missing
        if not all(os.getenv(var) for var in self.required_vars):
            load_dotenv()

        # Read environment variables
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_DATABASE")

        # Ensure all required vars are present
        missing = [var for var in self.required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        # Build the SQLAlchemy connection URL
        connection_url = sqlalchemy.engine.url.URL.create(
            drivername=driver,
            username=f"netid\\{self.user}",
            password=self.password,
            host=self.server,
            database=self.database,
        )
        self.engine = sqlalchemy.create_engine(connection_url)

    def query_from_string(self, sql_query, params=None):
        """Execute raw SQL with optional parameter binding.

        Args:
            sql_query (str): The SQL query to execute. Use the templating format
                required by the RDBMS.
            params (dict, optional): A dict of parameters for binding.
                Example: {"mod_id": "MOD25169"}.

        Returns:
            pd.DataFrame: Query result set as a pandas DataFrame.
        """
        with self.engine.connect() as connection:
            return pd.read_sql(sql_query, con=connection, params=params)

    def query_from_file(self, query_path, params=None):
        """Execute the query at query_path with optional parameter binding.

        Args:
            query_path (str): Filesystem path to the .sql file with the query.
            params (dict, optional): A dict of parameters for binding.

        Returns:
            pd.DataFrame: Query results as a pandas DataFrame.

        Raises:
            FileNotFoundError: If the SQL file doesn't exist or can't be read.
        """
        with open(query_path, "r") as query_file:
            query = query_file.read()

        with self.engine.connect() as connection:
            return pd.read_sql(query, con=connection, params=params)
