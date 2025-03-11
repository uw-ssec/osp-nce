import pytest
import pandas as pd
import sqlalchemy
from unittest.mock import MagicMock, patch

from osp_nce.backend.libs.sql_connector import SQLConnector


#
# Fixtures
#
@pytest.fixture
def mock_engine():
    """
    Return a mocked SQLAlchemy engine to avoid hitting RAD.
    """
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        engine_mock = MagicMock()
        mock_create_engine.return_value = engine_mock
        yield engine_mock


@pytest.fixture
def connector(mock_engine):
    """
    Provide an instance of SQLConnector with a mocked engine.
    """
    return SQLConnector("test_user", "test_pass", "test_server", "test_db")


#
# Initialization Tests
#
def test_initialization(connector):
    """
    Test that the testing SQLConnector initializes correctly.
    """
    assert connector.user == "test_user"
    assert connector.password == "test_pass"
    assert connector.server == "test_server"
    assert connector.database == "test_db"
    assert isinstance(connector.engine, MagicMock)


#
# Query Execution Tests
#
def test_query_from_string_success(connector):
    """
    Test that executing a SQL query string makes the proper pandas.read_sql call.
    """
    # Mock a connection context using the mocked engine.
    mock_conn = connector.engine.connect.return_value.__enter__.return_value

    with patch(
        "pandas.read_sql", return_value=pd.DataFrame({"col1": ["row1", "row2"]})
    ) as mock_read_sql:
        df = connector.query_from_string("SELECT * FROM test_table")

        # Ensure that pandas.read_sql was called with the expected arguments.
        mock_read_sql.assert_called_once_with(
            "SELECT * FROM test_table", con=mock_conn, params=None
        )

        # Ensure the expected DataFrame was returned
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 2


def test_query_from_string_failure_invalid_sql(connector):
    """
    Test that an invalid SQL query raises an SQLAlchemyError.
    """
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.side_effect = sqlalchemy.exc.SQLAlchemyError("Invalid SQL")

        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            connector.query_from_string("INVALID SQL QUERY")


def test_query_from_file_success(connector, tmp_path):
    """
    Test executing a parameterized SQL query loaded from a file.
    """
    # Create a temporary SQL file.
    query_path = tmp_path / "test_query.sql"
    query_content = "SELECT * FROM test_table WHERE id = :id"
    query_path.write_text(query_content, encoding="utf-8")

    # Mock a connection context using the mocked engine.
    mock_conn = connector.engine.connect.return_value.__enter__.return_value

    with patch(
        "pandas.read_sql", return_value=pd.DataFrame({"col1": ["row1"]})
    ) as mock_read_sql:
        df = connector.query_from_file(str(query_path), params={"id": 1})

        # Verify that pandas.read_sql was called with the file content.
        mock_read_sql.assert_called_once_with(
            query_content, con=mock_conn, params={"id": 1}
        )
        assert df.shape[0] == 1


def test_query_from_file_failure_file_not_found(connector):
    """
    Test that a FileNotFoundError is raised when the SQL file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        connector.query_from_file("non_existent.sql")
