import os
from string import Template

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

class SQLConnecter:
    def __init__(self):
        self.required_vars = ["DB_USER", "DB_PASSWORD", "DB_SERVER", "DB_DATABASE"]

        vars_present = True
        for var in self.required_vars:
            if not os.getenv(var):
                all_present = False
                break 
        
        if not vars_present: 
            load_dotenv()
        
        [self.user, self.password, self.server, self.database] = [os.getenv(var) for var in self.required_vars]

        if not all([self.user, self.password, self.server, self.database]):
            raise EnvironmentError("One or more environment variables are not set.")

        # Establish the database connection
        connection_url = sqlalchemy.engine.url.URL.create(
            drivername="mssql+pymssql",
            username=f"netid\\{self.user}",
            password=self.password,
            host=self.server,
            database=self.database,
        )
        self.engine = sqlalchemy.create_engine(connection_url)

    def query_database(self, query, params = None):
        connection = self.engine.connect()
        if params:
            query = Template(query).substitute(params)
        res = pd.read_sql(query, connection)
        return res 

        
