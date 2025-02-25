import os

def get_project_root() -> str:
    """Return the root directory of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

def get_src_dir() -> str:
    """Return the path to the src directory of the project."""
    return os.path.join(get_project_root, "src")

def get_frontend_dir() -> str:
    """Return the src/frontend directory."""
    return os.path.join(get_src_dir(), "frontend")

def get_backend_dir() -> str:
    """Return the src/backend directory."""
    return os.path.join(get_src_dir(), "backend")

def get_queries_dir() -> str:
    """Return the path to the src/sql directory."""
    return os.path.join(get_src_dir(), "sql")

def get_tests_dir() -> str:
    """return the path to the tests directory."""
    return os.path.join(get_project_root(), "tests")

def get_data_dir() -> str:
    """Return the path to the data directory."""
    return os.path.join(get_project_root(), "data")

def get_assets_dir() -> str:
    """Return the path to the assets directory."""
    return os.path.join(get_project_root(), "assets")

def get_query_path(query_name: str) -> str:
    """Return the full path to a query file given its name."""
    return os.path.join(get_queries_dir(), query_name)

def get_data_path(data_file: str) -> str:
    """Return the full path of a data file given its name."""
    return os.path.join(get_data_dir(), data_file)