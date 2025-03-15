import requests


def extract_error_message(exception: requests.RequestException) -> str:
    """
    Extracts any potential error message from a RequestException.
    """
    if exception.response is not None:
        try:
            error_data = exception.response.json()
            return error_data.get("error", str(exception))
        except Exception:
            pass
    return str(exception)
