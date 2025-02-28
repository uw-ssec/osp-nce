import streamlit as st
import requests

from osp_nce.shared.erm_form import Form


def get_mfa_message() -> None:
    """
    Request a device flow link and code from the FastAPI backend.

    If the request is successful, flag the "Proceed" button to appear.
    """
    try:
        response = requests.get("http://backend:8000/prompt_azure_mfa/")
        if response.status_code == 200:
            body = response.json()
            st.session_state["auth_message"] = body.get("auth_message", "")
            st.session_state["show_proceed"] = True
        else:
            st.error(
                f"Request for auth code failed. Status code {response.status_code}"
            )
    except requests.RequestException as e:
        st.error(f"Failed to contact server: {e}")


def get_user_auth() -> None:
    """Retrieve the user's access token after device flow authentication."""
    try:
        response = requests.get("http://backend:8000/acquire_access_token/")
        if response.status_code == 200:
            st.session_state["logged_in"] = True
        else:
            st.error(f"Request for token failed. Status code {response.status_code}")
    except requests.RequestException as e:
        st.error(f"Failed to contact server: {e}")


def instantiate_auth_page() -> None:
    """Displays the authentication page."""
    # Initialize the form object
    form = Form()
    st.session_state["form"] = form
    st.session_state["fields"] = form.get_fields()
    st.session_state["fields_map"] = form.get_fields_map()
    st.session_state["fields_map_pdf"] = form.get_fields_map_pdf()
    placeholder = st.empty()
    with placeholder.container():
        st.title("Get your Login Code to Start Automatic Form-Filling.")
        st.button(
            "Get Code",
            key="requested_code",
            on_click=get_mfa_message,
        )

        auth_message = st.session_state.get("auth_message", "")
        if auth_message:
            st.write(auth_message)
            st.text("After authentication, click proceed.")

        if st.session_state.get("show_proceed", False):
            st.button("Proceed", key="ProceedButtonAuth", on_click=get_user_auth)


def logout():
    for key in st.session_state:
        del st.session_state[key]
    st.rerun()


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


login_page = st.Page(instantiate_auth_page, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
form_page = st.Page(
    "form_page.py", title="Editable Form", icon=":material/person_edit:"
)
chatbot_page = st.Page(
    "chatbot_page.py", title="Document Chat", icon=":material/smart_toy:"
)

# Note that page order matters here. If logged in will default to form_page
if st.session_state.get("logged_in", False):
    pg = st.navigation(
        {
            "Extension Review": [form_page, chatbot_page],
            "Account": [logout_page],
        }
    )
else:
    pg = st.navigation([login_page])

# print(pg.title)
pg.run()
