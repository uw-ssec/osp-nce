import connect
import sys

# Check if an argument is provided
if len(sys.argv) < 2:
    print("Usage: python test_connect.py <your_argument>")
    sys.exit(1)

# Retrieve the user-supplied argument
user_argument = sys.argv[1]
print(f"You entered: {user_argument}")

if __name__ == "__main__":
    print("Getting connection")
    conn = connect.get_connection()
    print("Executing query")
    df = connect.fetch_query_result("../sql/test_query.sql", conn, params=user_argument)
    print(df.head())
