import connect

if __name__ == "__main__":
    print("Getting connection")
    conn = connect.get_connection()
    print("Executing query")
    df = connect.fetch_query_result("./sql/test_query.sql", conn)
    print(df.head())
