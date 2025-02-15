import pytest
import pandas as pd
import sqlalchemy
from unittest.mock import MagicMock, patch

from backend.libs.sql_connector import SQLConnector


@pytest.fixture
def mock_engine():
    """Create a mocked SQLAlchemy engine to avoid hitting the actual DB."""
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        mock_engine_instance = MagicMock()
        mock_create_engine.return_value = mock_engine_instance
        yield mock_engine_instance


@pytest.fixture
def sql_connector(mock_engine):
    """Provide an instance of SQLConnector with a mocked engine."""
    return SQLConnector("test_user", "test_pass", "test_server", "test_db")


def test_initialization(sql_connector):
    """Test if the SQLConnector initializes correctly."""
    assert sql_connector.user == "test_user"
    assert sql_connector.password == "test_pass"
    assert sql_connector.server == "test_server"
    assert sql_connector.database == "test_db"
    # Ensure the engine is a mock
    assert isinstance(sql_connector.engine, MagicMock)


def test_query_from_string(sql_connector):
    """Test executing a query string with a mocked connection."""
    mock_conn = sql_connector.engine.connect.return_value.__enter__.return_value

    with patch(
        "pandas.read_sql", return_value=pd.DataFrame({"col1": ["row1", "row2"]})
    ) as mock_read_sql:
        result = sql_connector.query_from_string("SELECT * FROM test_table")
        mock_read_sql.assert_called_once_with(
            "SELECT * FROM test_table", con=mock_conn, params=None
        )
        assert isinstance(result, pd.DataFrame)
        assert result.shape[0] == 2  # Two rows returned


def test_query_from_file(sql_connector, tmp_path):
    """Test executing a parameterized SQL query from a temporary file."""
    query_path = tmp_path / "test_query.sql"
    query_content = "SELECT * FROM test_table WHERE id = :id"
    query_path.write_text(query_content, encoding="utf-8")

    mock_conn = sql_connector.engine.connect.return_value.__enter__.return_value

    with patch(
        "pandas.read_sql", return_value=pd.DataFrame({"col1": ["row1"]})
    ) as mock_read_sql:
        result = sql_connector.query_from_file(str(query_path), params={"id": 1})
        mock_read_sql.assert_called_once_with(
            query_content, con=mock_conn, params={"id": 1}
        )
        assert len(result) == 1  # One row returned


def test_query_from_file_file_not_found(sql_connector):
    """Test handling of missing SQL file."""
    with pytest.raises(FileNotFoundError):
        sql_connector.query_from_file("non_existent.sql")


def test_invalid_sql_query(sql_connector):
    """Test handling of invalid SQL."""
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.side_effect = sqlalchemy.exc.SQLAlchemyError("Invalid SQL")
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            sql_connector.query_from_string("INVALID SQL QUERY")
