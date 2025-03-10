import requests
import streamlit as st

from osp_nce.shared.forms import ExtensionReviewMatrix


def request_device_flow_code() -> None:
    """
    Request a device flow link and code from the query backend.
    """
    try:
        response = requests.get("http://backend:8000/prompt_azure_mfa/")
        if response.status_code == 200:
            body = response.json()
            st.session_state["auth_message"] = body.get("auth_message", "")
            st.session_state["show_proceed"] = True
        else:
            st.error(f"Request for auth code failed. Status code {response.status_code}")
    except requests.RequestException as e:
        st.error(f"Failed to contact server: {e}")


def fetch_user_access_token() -> None:
    """
    Retrieve the user's access token after device flow authentication.
    """
    try:
        response = requests.get("http://backend:8000/acquire_access_token/")
        if response.status_code == 200:
            st.session_state["logged_in"] = True
        else:
            st.error(f"Request for token failed. Status code {response.status_code}")
    except requests.RequestException as e:
        st.error(f"Failed to contact server: {e}")


def display_login_page() -> None:
    """
    Display the landing page for Microsoft device flow authentication.
    """
    placeholder = st.empty()
    with placeholder.container():
        st.title("Get Your Login Code to Start Automatic Form-Filling")
        st.button("Get Code", key="requested_code", on_click=request_device_flow_code)

        auth_message = st.session_state.get("auth_message", "")
        if auth_message:
            st.write(auth_message)
            st.text("After authentication, click proceed.")

        if st.session_state.get("show_proceed", False):
            st.button("Proceed", key="ProceedButtonAuth", on_click=fetch_user_access_token)


def logout() -> None:
    """
    Clear session state and reruns the app, effectively logging the user out.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def run() -> None:
    """
    Configure the app layout, define page navigation, and render the current page.
    """
    st.set_page_config(
        page_title="GRACE",
        page_icon=":robot_face:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "# A streamlined approach to grant extension reviewing.",
            "Report a bug": "https://github.com/uw-ssec/osp-nce/issues",
        },
    )

    # Intialize an ExtensionReviewMatrix on the first run
    if "erm" not in st.session_state:
        st.session_state["erm"] = ExtensionReviewMatrix()

    # Define the main app pages from callables/scripts
    login_page = st.Page(display_login_page, title="Log in", icon=":material/login:")
    logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
    form_page = st.Page("form_page.py", title="Editable Form", icon=":material/person_edit:")
    chatbot_page = st.Page("chatbot_page.py", title="Document Chat", icon=":material/smart_toy:")

    # Determine which pages to make available based on login status
    if st.session_state.get("logged_in", False):
        page = st.navigation(
            {
                "Extension Review": [form_page, chatbot_page],
                "Account": [logout_page],
            }
        )
    else:
        page = st.navigation([login_page])

    # Render the current page
    page.run()


if __name__ == "__main__":
    run()
