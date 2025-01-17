from flask import Flask, request, render_template_string
import connect

app = Flask(__name__)

# HTML template for the webpage
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Database Query App</title>
</head>
<body>
    <h1>Database Query App</h1>
    <form method="POST">
        <label for="argument">Enter your argument:</label>
        <input type="text" id="argument" name="argument" required>
        <button type="submit">SUBMIT</button>
    </form>
    {% if result is not none %}
        <h2>Result:</h2>
        <pre>{{ result }}</pre>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        user_argument = request.form["argument"]
        try:
            # Get database connection
            conn = connect.get_connection()
            # Execute query
            df = connect.fetch_query_result("../sql/test_query.sql", conn, params=user_argument)
            # Extract and format the result to display on the page
            result = df["FECDMSponsorEntityType"].to_string(index=False)
        except Exception as e:
            result = f"An error occurred: {str(e)}"
    return render_template_string(html_template, result=result)

if __name__ == "__main__":
    app.run(debug=True)
