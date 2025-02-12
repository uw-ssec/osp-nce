from pathlib import Path
import os

def get_project_root() -> Path:
    """Return the root directory of the project."""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(current_dir, "../../"))

def get_queries_dir() -> Path:
    """Return the path to the sql directory."""
    return get_project_root().joinpath("sql")

def get_data_dir() -> Path:
    """Return the path to the data directory."""
    return get_project_root().joinpath("data")

def get_query_path(query_name: str) -> Path:
    """Return the full path to a query file given its name."""
    return get_queries_dir().joinpath(query_name)

def get_data_path(data_file: str) -> Path:
    """Return the full path of a data file given its name."""
    return get_data_dir().joinpath(data_file)
