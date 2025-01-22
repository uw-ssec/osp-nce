"""
Script to test database connection and query execution. 

Adapt and put into tests folder later.
"""

import logging

import connect

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def main():
    """Get connection and execute query."""
    print("Getting connection")
    conn = connect.get_connection()
    print("Executing query")
    df = connect.fetch_query_result(
        "./sql/rad.sql", conn, params={"mod_id": "MOD25008"}
    )
    # df = connect.fetch_query_result("sql/test_query.sql", conn)
    print(df.head())


if __name__ == "__main__":
    main()
