import json
import re
from datetime import datetime

import requests
import streamlit as st


class AutofillError(Exception):
    """
    Exception raised for autofill retrieval failures.
    """

    pass


def is_valid_mod_id(mod_id: str) -> bool:
    """
    Check if the given MOD ID has the expected format: 'MOD' followed by 5 digits.
    """
    return bool(re.fullmatch(r"MOD\d{5}", mod_id))


def autosave_values() -> None:
    """
    Save the current user input into session state and regenerates the PDF bytes.
    """
    updated = {}
    for key in st.session_state.erm.to_dict():
        updated[key] = {
            "value": st.session_state.get(key, ""),
            "notes": st.session_state.get(f"{key}_notes", ""),
        }
    st.session_state.erm.update_fields(updated)


def new_mod() -> None:
    """
    Clear the current MOD from session state to trigger loading the query page.
    """
    st.session_state["working_mod"] = False


def restore_autofiller_responses() -> None:
    """
    Revert current form values to the originally fetched autofilled responses.
    """
    st.session_state.erm.update_fields(st.session_state.get("autofilled_vals", {}))


def fetch_autofill(mod_id: str) -> dict:
    """
    Send a POST request to retrieve autofill data for the given MOD ID.

    Raises:
        AutofillError: If any network errors or invalid responses are encountered.
    """
    url = "http://backend:8000/autofill_erm/"
    payload = {"mod_id": mod_id}
    try:
        response = requests.post(url, json=payload)
    except requests.RequestException as e:
        raise AutofillError(f"Request failed: {e}")

    # If the response is not 200, build an error message and raise an AutofillError
    if not response.ok:
        message = f"Server responded with {response.status_code}."
        try:
            detail = response.json().get("detail")
            if detail:
                message += f" Detail: {detail}"
        except json.JSONDecodeError:
            message += " No JSON in error response."
        raise AutofillError(message)

    # Otherwise, attempt to parse the autofilled fields
    try:
        data_str = response.json().get("Data", "")
        if not data_str:
            raise AutofillError("No 'Data' field in JSON response.")
        autofiller_data = json.loads(data_str)
    except (json.JSONDecodeError, TypeError) as e:
        raise AutofillError(f"Error processing JSON 'Data': {e}")

    return autofiller_data


def get_curr_pdf() -> bytes:
    """
    Retrieve the latest PDF bytes from session state.
    """
    try:
        return st.session_state.erm.to_bytes()
    except Exception as e:
        raise Exception(e)


def get_curr_filename() -> str:
    """
    Construct a standardized filename for the PDF output.

    Returns:
        str: A filename of the form 'Review_Matrix_<PIName>_<MODID>_<YYYY-MM-DD>.pdf'.
    """
    mod_id = st.session_state.erm.form_dict["mod_id"].get("value", "")
    pi_name = st.session_state.erm.form_dict["pi_name"].get("value", "")
    sanitized_pi_name = pi_name.replace(",", "_")
    current_date = datetime.now().strftime("%Y-%m-%d")

    return f"Review_Matrix_{sanitized_pi_name}_{mod_id}_{current_date}.pdf"


def show_basic_info_fields(form_dict: dict[dict]) -> None:
    """
    Displays fields for MOD/Worktag ID and PI Name on the page.
    """
    col_left, col_right = st.columns(2)
    with col_left:
        st.text_input("MOD/Worktag ID:", value=form_dict["mod_id"].get("value", ""), key="mod_id")
    with col_right:
        st.text_input("PI Name:", value=form_dict["pi_name"].get("value", ""), key="pi_name")


def show_review_fields(form_dict: dict[dict]) -> None:
    """
    Displays the main Extension Review Matrix fields and associated notes.
    """
    ri_fields_in_order = {
        key: value
        for key, value in form_dict.items()
        if key not in ["review_notes", "mod_id", "pi_name"]
    }

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.subheader("Review Items")
    with col2:
        st.subheader("Action")
    with col3:
        st.subheader("Notes")

    # Display the editable form fields with helper text and autofiller notes
    for ri, field in ri_fields_in_order.items():
        display_name = field.get("display_name", "")
        value = field.get("value", "")
        helper_text = field.get("helper_text", "")
        notes = field.get("notes", "")

        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.text_input(display_name, value=value, key=ri)
        with col2:
            st.caption(helper_text)
        with col3:
            st.text_area(f"Notes ({display_name})", value=notes, key=f"{ri}_notes", height=100)

    # Display the editable autofiller review notes
    st.subheader("Review Notes")
    st.text_area(
        label=" ",
        value=form_dict["review_notes"].get("value", ""),
        key="review_notes",
        height=300,
    )


def show_utility_buttons() -> None:
    """
    Display buttons for downloading the PDF, restoring autofill, and entering a new MOD.
    """
    with st.sidebar:
        st.markdown("### Toolbar")
        st.write("Reset or download your form data below.")

        st.download_button(
            "Download PDF",
            data=get_curr_pdf(),
            file_name=get_curr_filename(),
            key="DownloadPDFButton",
            use_container_width=True,
        )
        st.button(
            "Restore Autofill",
            key="RestoreAutofiller",
            on_click=restore_autofiller_responses,
            help="Undo all changes back to autofilled responses.",
            use_container_width=True,
        )
        st.button(
            "New Mod",
            key="NewMod",
            on_click=new_mod,
            help="Enter a different MOD/Worktag ID.",
            use_container_width=True,
        )


def display_editable_form_page() -> None:
    """
    Display a user-editable Extension Review Matrix with autofilled fields.

    Notes:
        Only called  when the `working_mod` flag is set in the session state.
    """
    placeholder = st.empty()
    form_dict = st.session_state["erm"].to_dict()

    with placeholder.container():
        st.title("Editable Form - Extension Review Matrix")
        show_basic_info_fields(form_dict)
        show_review_fields(form_dict)
        autosave_values()
        show_utility_buttons()


def autofill_callback(mod_id_input: str) -> None:
    """
    A callback to send the MOD ID to the backend to  autofill the local `ExtensionReviewMatrix`.
    """
    # Sanitize the user input
    mod_id = mod_id_input.replace(" ", "").upper()
    if not mod_id.startswith("MOD"):
        mod_id = "MOD" + mod_id
    if not is_valid_mod_id(mod_id):
        st.warning("Invalid MOD ID. Must be 'MOD' plus exactly 5 digits.")
        return

    # Fetch autofiller response
    try:
        autofill = fetch_autofill(mod_id)
        st.session_state["erm"].update_fields(autofill)

    except AutofillError as e:
        st.warning(f"Autofill retrieval failed: {e}")
        return

    st.session_state["working_mod"] = True
    st.session_state["autofilled_vals"] = autofill


def display_query_page() -> None:
    """
    Display a page where the user can input a MOD ID to fetch autofilled form data.

    Notes:
        Only called when there is no `working_mod` under consideration.
    """
    placeholder = st.empty()
    with placeholder.container():
        st.title("Editable Form - Extension Review Matrix")
        st.subheader("Enter a MOD/Worktag ID to Prefill the Review Matrix")

        mod_id_input = st.text_input("MOD/Worktag ID:", value="MOD", key="curr_mod_input")

        st.button(
            "Proceed",
            key="ProceedButtonLanding",
            on_click=autofill_callback,
            args=(mod_id_input,),
        )


def run() -> None:
    """
    Determine which page to display based on the current session state.
    """
    if not st.session_state.get("working_mod", False):
        display_query_page()
    else:
        display_editable_form_page()


if __name__ == "__page__":
    run()
