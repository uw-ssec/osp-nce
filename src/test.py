from src.backend.libs.sql_connector import SQLConnector
from dotenv import load_dotenv
import os

load_dotenv("./.env")

user = os.getenv("RAD_USER")
password = os.getenv("RAD_PASSWORD")
server = os.getenv("RAD_SERVER")
database = os.getenv("RAD_DATABASE")

db = SQLConnector(user, password, server, database)

print(db.query_from_string("SELECT * FROM RADDB.UW.vAward"))