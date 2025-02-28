import json
import re
from datetime import datetime
from io import BytesIO
import time

import streamlit as st
import pandas as pd
import requests
from PyPDF2 import PdfReader, PdfWriter

from osp_nce.shared.erm_form import Form


def get_curr_filename() -> str:
    mod_id = st.session_state.get("curr_mod", "")
    pi_name = st.session_state.get("pi_name", "")
    return (
        f"Review_Matrix_{pi_name.replace(',', '_')}_{mod_id}_"
        f"{datetime.now().strftime('%Y-%m-%d')}.pdf"
    )


def fetch_autofill(mod_id: str) -> bool:
    try:
        response = requests.get("http://backend:8000/run", params={"mod_id": mod_id})
        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "Unknown error")
            except json.JSONDecodeError:
                detail = "No JSON to parse."
            st.error(f"Error from server: {detail}")
            return False

        json_data = response.json()
        data = json.loads(json_data.get("Data", None))
        if data is None:
            st.error("No 'Data' field in JSON response.")
            return False

        st.session_state["autofilled_vals"] = data
        st.session_state["curr_vals"] = data.copy()
        st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()
        return True

    except requests.RequestException as exc:
        st.error(f"Error connecting to server: {exc}")
        return False
    except (json.JSONDecodeError, TypeError) as e:
        st.error(f"Error processing data: {e}")
        return False


def is_valid_mod_id(mod_id: str) -> bool:
    """
    Validate that the MOD ID is in the format 'MOD' followed by exactly 5 digits.
    """
    return bool(re.fullmatch(r"MOD\d{5}", mod_id))


def instantiate_query_page() -> None:
    placeholder = st.empty()
    with placeholder.container():
        st.title("Editable Form - Extension Review Matrix")
        st.subheader("Enter a MOD ID to Prefill the Review Matrix")

        mod_id_input = st.text_input(
            "MOD/Worktag ID:", value="MOD", key="curr_mod_input"
        )

        def proceed_callback():
            # Sanitize input: remove all spaces and convert to uppercase.
            mod_id = mod_id_input.replace(" ", "").upper()
            # If missing the "MOD" prefix, prepend it.
            if not mod_id.startswith("MOD"):
                mod_id = "MOD" + mod_id

            # Validate the sanitized MOD ID.
            if not is_valid_mod_id(mod_id):
                st.warning(
                    "Invalid MOD ID. It must be 'MOD' plus exactly 5 digits (e.g., MOD45982)."
                )
                return

            if fetch_autofill(mod_id):
                st.session_state["curr_mod"] = mod_id
            else:
                st.warning(
                    "Autofill retrieval failed. Please try a different MOD ID or check the server."
                )

        st.button("Proceed", key="ProceedButtonLanding", on_click=proceed_callback)


def fill_pdf_to_bytes() -> bytes:
    """Create and return a new PDF containing the updated values as bytes."""
    try:
        updated = st.session_state.get("curr_vals", {})
        template_path = "./assets/extension_review_matrix.pdf"
        if not updated:
            raise ValueError("'curr_vals' missing from state.")

        with open(template_path, "rb") as template_file:
            pdf_template = PdfReader(template_file)
            writer = PdfWriter()

            for idx, page in enumerate(pdf_template.pages):
                for key, field_name in st.session_state.fields_map_pdf.items():
                    if field_name:
                        val = updated.get(key, {}).get("val", "")
                        writer.update_page_form_field_values(page, {field_name: val})
                writer.add_page(page)

        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        return pdf_bytes.getvalue()

    except Exception as e:
        st.error(f"An error occurred while creating the PDF: {e}")
        return b""


def instantiate_editable_form_page() -> None:
    """
    Displays the query page with update, download, and restore functions.

    The values displayed are pulled from "curr_vals" in state, which reflect
    the most recent user edits
    """
    placeholder = st.empty()
    data = st.session_state.get("curr_vals", {})

    with placeholder.container():
        st.title("Editable Form - Extension Review Matrix")
        _show_basic_info_fields(data)
        if data.get("mod_id", {}).get("val", ""):
            _show_review_fields(data)
            _show_review_notes(data)

        _show_utility_buttons()

    # Autosave the updated values
    autosave_values()


def autosave_values() -> None:
    """
    Autosave the filled entries from user input and save to session state.

    This method is called whenever the form is displayed to ensure changes are saved.
    """
    updated = st.session_state.get("curr_vals", {}).copy()
    for key in st.session_state.fields_map:
        updated[key] = {
            "val": st.session_state.get(key, ""),
            "notes": st.session_state.get(f"{key}_notes", ""),
        }

    st.session_state["curr_vals"] = updated
    st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()


def _show_basic_info_fields(data: dict) -> None:
    """Displays the MOD/Worktag ID and PI Name fields."""
    col_left, col_right = st.columns(2)
    with col_left:
        st.text_input(
            "MOD/Worktag ID:",
            value=data.get("mod_id", {}).get("val", ""),
            key="mod_id_form",
        )
    with col_right:
        st.text_input(
            "PI Name:",
            value=data.get("pi_name", {}).get("val", ""),
            key="pi_name_form",
        )


def _show_review_fields(data: dict) -> None:
    """Displays the fields except the 'review_notes' entry."""
    fields_in_order = [
        field for field in st.session_state.fields_map if field != "review_notes"
    ]

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.subheader("**Review Items**")
    with col2:
        st.subheader("**Action**")
    with col3:
        st.subheader("**Notes**")

    for ri_field in fields_in_order:
        field_label = st.session_state.fields_map[ri_field]
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.text_input(
                field_label,
                value=data.get(ri_field, {}).get("val", ""),
                key=ri_field,
            )
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


def _show_review_notes(data: dict) -> None:
    """Displays the 'review_notes' field at the bottom."""
    review_key = "review_notes"
    if review_key in st.session_state.fields_map:
        st.subheader("Review Notes")
        st.text_area(
            label=" ",
            value=data.get(review_key, {}).get("val", ""),
            key=review_key,
            height=300,
        )


def _show_utility_buttons() -> None:
    """Displays sidebar buttons for download, restore, and new mod."""
    with st.sidebar:
        st.markdown("### Toolbar")
        st.write("*Below you'll find options to reset or download your form data.*")

        # Define a callback function for the download button
        def download_callback():
            autosave_values()
            st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()

        st.download_button(
            "Download PDF",
            data=get_pdf_bytes(),
            file_name=get_curr_filename(),
            key="DownloadPDFButton",
            help="Generate and download a filled-out PDF form based on your last save.",
            use_container_width=True,
            on_click=download_callback,
        )
        st.button(
            "Restore Autofill",
            key="RestoreAutofiller",
            on_click=restore_autofiller_responses,
            help="Undo any changes you've made and revert to the original autofilled responses.",
            use_container_width=True,
        )
        st.button(
            "New Mod",
            key="NewMod",
            on_click=new_mod,
            help="Return to the landing page to enter a different MOD/Worktag ID.",
            use_container_width=True,
        )


def get_pdf_bytes() -> bytes:
    """Generate and return the PDF bytes."""
    autosave_values()
    return st.session_state.get("curr_pdf_bytes", b"")


def new_mod() -> None:
    """Switch back to landing page."""
    # TODO: Reset the state before transition
    st.session_state["curr_mod"] = ""


def restore_autofiller_responses() -> None:
    """Revert to original autofiller responses."""
    st.session_state["curr_vals"] = st.session_state.get("autofilled_vals", {})
    st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()


def update_values() -> None:
    """
    Update the filled entries from user input and save to session state.

    After execution, remain on the query page.
    """
    updated = st.session_state.get("curr_vals", {}).copy()
    for key in st.session_state.fields_map:
        updated[key] = {
            "val": st.session_state.get(key, ""),
            "notes": st.session_state.get(f"{key}_notes", ""),
        }

    st.session_state["curr_vals"] = updated
    st.session_state["curr_pdf_bytes"] = fill_pdf_to_bytes()
    st.session_state["page"] = "query"


#
# --------------------- PDF DOWNLOAD ---------------------
#
def fill_pdf_to_bytes() -> bytes:
    """Create and return a new PDF containing the updated values as bytes."""
    try:
        updated = st.session_state.get("curr_vals", {})
        template_path = "./assets/extension_review_matrix.pdf"
        if not updated:
            raise ValueError("'curr_vals' missing from state.")

        with open(template_path, "rb") as template_file:
            pdf_template = PdfReader(template_file)
            writer = PdfWriter()

            for idx, page in enumerate(pdf_template.pages):
                for key, field_name in st.session_state.fields_map_pdf.items():
                    if field_name:
                        val = updated.get(key, {}).get("val", "")
                        writer.update_page_form_field_values(page, {field_name: val})
                writer.add_page(page)

        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        return pdf_bytes.getvalue()

    except Exception as e:
        st.error(f"An error occurred while creating the PDF: {e}")
        return b""


def run():
    # st.write(st.session_state)
    if not st.session_state.get("curr_mod", ""):
        instantiate_query_page()
    else:
        instantiate_editable_form_page()


if __name__ == "__page__":
    run()
