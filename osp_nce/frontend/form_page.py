import json
import re
from datetime import datetime
from io import BytesIO

import requests
import streamlit as st
from PyPDF2 import PdfReader, PdfWriter


class AutofillError(Exception):
    """
    Exception raised for autofill retrieval failures.
    """

    pass


# -------------------------------
# Helpers and Callbacks
# -------------------------------


def is_valid_mod_id(mod_id: str) -> bool:
    """
    Check if the given MOD ID has the expected format: 'MOD' followed by 5 digits.
    """
    return bool(re.fullmatch(r"MOD\d{5}", mod_id))


def autosave_values() -> None:
    """
    Save the current user inputs into session state and regenerate the PDF bytes.
    """
    updated = st.session_state.get("curr_vals", {}).copy()
    for key in st.session_state.fields_map:
        updated[key] = {
            "val": st.session_state.get(key, ""),
            "notes": st.session_state.get(f"{key}_notes", ""),
        }
    st.session_state["curr_vals"] = updated
    st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()


def new_mod() -> None:
    """
    Clear the current MOD from session state to trigger loading the query page.
    """
    st.session_state["curr_mod"] = ""


def restore_autofiller_responses() -> None:
    """
    Revert current form values to the originally fetched autofilled responses.
    """
    st.session_state["curr_vals"] = st.session_state.get("autofilled_vals", {})
    st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()


def fetch_autofill_data(mod_id: str, form_dict: dict) -> dict:
    """
    Send a POST request to retrieve autofill data for the given MOD ID.

    Raises:
        AutofillError: If any network errors or invalid responses are encountered.
    """
    url = "http://backend:8000/run/"
    payload = {"mod_id": mod_id, "form": form_dict}
    try:
        response = requests.post(url, json=payload)
    except requests.RequestException as exc:
        raise AutofillError(f"Request failed: {exc}")

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

    # Otherwise, attempt to parse the autofilled form fields
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
    return st.session_state.get("curr_pdf_bytes", b"")


# -------------------------------
# PDF Fill / Generation
# -------------------------------


def get_curr_filename() -> str:
    """
    Construct a standardized filename for the PDF output.

    Returns:
        str: A filename of the form 'Review_Matrix_<PIName>_<MODID>_<YYYY-MM-DD>.pdf'.
    """
    mod_id = st.session_state.get("curr_mod", "")
    pi_name = st.session_state.get("pi_name", "")
    sanitized_pi_name = pi_name.replace(",", "_")
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"Review_Matrix_{sanitized_pi_name}_{mod_id}_{current_date}.pdf"


def fill_pdf_to_bytes() -> bytes:
    """
    Return a PDF (as bytes) populated with the current session values.

    Raises:
        ValueError: If 'curr_vals' is missing from session state.
    """
    try:
        curr_vals = st.session_state.get("curr_vals", {})
        if not curr_vals:
            raise ValueError("'curr_vals' missing from session state.")

        template_path = "./assets/extension_review_matrix.pdf"
        with open(template_path, "rb") as template_file:
            pdf_template = PdfReader(template_file)
            writer = PdfWriter()

            for page in pdf_template.pages:
                for key, field_name in st.session_state.fields_map_pdf.items():
                    if field_name:
                        val = curr_vals.get(key, {}).get("val", "")
                        writer.update_page_form_field_values(page, {field_name: val})
                writer.add_page(page)

        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes.getvalue()

    except Exception as e:
        st.error(f"An error occurred while creating the PDF: {e}")
        return b""


# -------------------------------
# Main Page Display (UI)
# -------------------------------


def show_basic_info_fields(data: dict) -> None:
    """
    Displays fields for MOD/Worktag ID and PI Name on the page.

    Args:
        data (dict): Current dictionary of values to display.
    """
    col_left, col_right = st.columns(2)
    with col_left:
        st.text_input(
            "MOD/Worktag ID:", value=data.get("mod_id", {}).get("val", ""), key="mod_id_form"
        )
    with col_right:
        st.text_input("PI Name:", value=data.get("pi_name", {}).get("val", ""), key="pi_name_form")


def show_review_fields(data: dict) -> None:
    """
    Displays the main Extension Review Matrix fields and associated notes.

    Args:
        data (dict): Current dictionary of values to display.
    """
    fields_in_order = [f for f in st.session_state.fields_map if f != "review_notes"]

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.subheader("Review Items")
    with col2:
        st.subheader("Action")
    with col3:
        st.subheader("Notes")

    # Display the editable form fields with helper text and autofiller notes
    for ri_field in fields_in_order:
        field_label = st.session_state.fields_map[ri_field]
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.text_input(field_label, value=data.get(ri_field, {}).get("val", ""), key=ri_field)
        with col2:
            helper_text = st.session_state.fields.get(field_label, "")
            if helper_text:
                st.caption(helper_text)
        with col3:
            st.text_area(
                f"Notes ({field_label})",
                value=data.get(ri_field, {}).get("notes", ""),
                key=f"{ri_field}_notes",
                height=100,
            )

    # Display the editable autofiller review notes
    if "review_notes" in st.session_state.fields_map:
        st.subheader("Review Notes")
        st.text_area(
            label=" ",
            value=data.get("review_notes", {}).get("val", ""),
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
        Only called  when a valid `curr_mod` is present in session state.
    """
    placeholder = st.empty()
    curr_vals = st.session_state.get("curr_vals", {})

    with placeholder.container():
        st.title("Editable Form - Extension Review Matrix")
        show_basic_info_fields(curr_vals)
        show_review_fields(curr_vals)
        autosave_values()
        show_utility_buttons()


def display_query_page() -> None:
    """
    Display a page where the user can input a MOD ID to fetch autofilled form data.

    Notes:
        Only called when there is no "curr_mod" under consideration.
    """
    placeholder = st.empty()
    with placeholder.container():
        st.title("Editable Form - Extension Review Matrix")
        st.subheader("Enter a MOD/Worktag ID to Prefill the Review Matrix")

        mod_id_input = st.text_input("MOD/Worktag ID:", value="MOD", key="curr_mod_input")

        def process_input_and_autofill():
            # Sanitize and validate the user inputted MOD ID
            mod_id = mod_id_input.replace(" ", "").upper()
            if not mod_id.startswith("MOD"):
                mod_id = "MOD" + mod_id
            if not is_valid_mod_id(mod_id):
                st.warning("Invalid MOD ID. Must be 'MOD' plus exactly 5 digits.")
                return

            # Fetch autofiller response
            try:
                data = fetch_autofill_data(mod_id, st.session_state.form.to_dict())
            except AutofillError as e:
                st.warning(f"Autofill retrieval failed: {e}")
                return

            st.session_state["curr_mod"] = mod_id
            st.session_state["autofilled_vals"] = data
            st.session_state["curr_vals"] = data.copy()
            st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()

        st.button("Proceed", key="ProceedButtonLanding", on_click=process_input_and_autofill)


def run():
    """
    Determine which page to display based on the current session state.
    """
    if not st.session_state.get("curr_mod", ""):
        display_query_page()
    else:
        display_editable_form_page()


if __name__ == "__page__":
    run()
