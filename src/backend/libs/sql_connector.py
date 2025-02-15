import pandas as pd
import sqlalchemy


class SQLConnector:
    """
    Connector for establishing an SQL database connection and executing queries.

    Uses an SQLAlchemy engine for executing queries.

    Attributes:
        user (str): Database username.
        password (str): Database password.
        server (str): Database server hostname or IP.
        database (str): Database name.
        driver (str): The SQLAlchemy driver name (e.g., 'mssql+pymssql').
        engine (sqlalchemy.engine.Engine): Query engine for query execution.
    """

    def __init__(self, user, password, server, database, driver="mssql+pymssql"):
        """
        Initialize the SQLConnector with credentials and parameters.

        Args:
            user (str): Database username (can include domain).
            password (str): Database password.
            server (str): Database server hostname or IP.
            database (str): Database name.
            driver (str, optional): The SQLAlchemy driver name. Defaults to
                "mssql+pymssql".
        """
        self.user = user
        self.password = password
        self.server = server
        self.database = database
        self.driver = driver

        # Build the SQLAlchemy connection URL
        connection_url = sqlalchemy.engine.url.URL.create(
            drivername=self.driver,
            username=self.user,
            password=self.password,
            host=self.server,
            database=self.database,
        )

        # Intialize the query engine
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
            query_path (str): Filesystem path to the .sql query to execute.
            params (dict, optional): A dict of parameters for binding.

        Returns:
            pd.DataFrame: Query results as a pandas DataFrame.

        Raises:
            FileNotFoundError: If the SQL file doesn't exist or can't be read.
        """
        with open(query_path, "r", encoding="utf-8") as query_file:
            query = query_file.read()

        with self.engine.connect() as connection:
            return pd.read_sql(query, con=connection, params=params)
