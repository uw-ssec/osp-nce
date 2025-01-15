import connect

if __name__ == "__main__":
    print("Getting connection")
    conn = connect.get_connection()
    print("Executing query")
    df = connect.fetch_query_result("./sql/intial_query.sql", conn)
    df.to_csv("./data/data_pull.csv")
    print(df.head())
