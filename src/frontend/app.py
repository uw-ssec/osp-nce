import json
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd
import requests
from PyPDF2 import PdfReader, PdfWriter


class StreamLitApp:
    """
    StreamLitApp manages all Streamlit pages, user interactions, and PDF creation.
    """

    def __init__(self):
        # TODO --- Move this stuff to the ERM autofiller in some way
        # Initialize the fields with their helper texts
        self.fields = {
            "SFI Current?": "No - Send email to research@uw.edu for review.",
            "Remaining Balance $$": "Check Award Portal for award balance.",
            "Is the award in deficit?": "Yes - PI must explain deficit & transfer costs to appropriate non-federal, non-sponsored departmental worktag or provide Sponsor assurance that further funding is forthcoming.",
            "Is the balance greater than 25% of the total award?": "Yes - PI must provide a programmatic explanation for a large balance.",
            "Award lines listed or 'extend all' indicated?": "Note in MOD Comments which award lines are to be extended if campus so indicates.",
            "Temporary Request?": "Include non-sponsored departmental worktag in MOD Comments & History.",
            "New Cost Share?": "Yes - Attach revised CS Addendum to MOD.",
            "Human Subjects?": "Yes - Verify and document IRB approval(s). Refer to Human Subjects Review Guidance.",
            "Animal Use?": "Yes - Verify and document IACUC approval(s). Refer to Animal Use Compliance Verification guidance.",
            "Prior Approval required?": "Federal award - Review Federal-Wide Research Terms & Conditions (RTCs) Prior Approval Matrix, Appendix A to confirm whether the award requires prior approval.",
            "Has the project previously been extended? Is this an NIH 2nd+ extension?": "Yes - Ensure that the Budget, Progress Report, and Programmatic Justification are included as 3 separate PDFs.",
            "Is the request to extend within Sponsor’s required timeframe?": "No - Extension requires Sponsor approval.",
            "Is this a federal contract?": "Yes - Extension requires Sponsor approval.",
            "Fixed Price terms?": "No - Extension requires Sponsor approval. Review fixed price terms.",
            "Paid in full?": "No - Check Award Portal. If outstanding payments exist, deny extension until PI/campus resolve with Sponsor.",
            "All deliverables submitted?": "No - Extension requires Sponsor approval. Review fixed price terms.",
            "FAR clause 52.222-54 (e-verify)?": "Yes - Forward E-verify process to your campus contact & state in MOD comments that e-verify is required.",
            "Review Notes": "Enter any additional notes here.",
        }
        self.fields_map = {
            "ri1": "SFI Current?",
            "ri2": "Remaining Balance $$",
            "ri3": "Is the award in deficit?",
            "ri4": "Is the balance greater than 25% of the total award?",
            "ri5": "Award lines listed or 'extend all' indicated?",
            "ri6": "Temporary Request?",
            "ri7": "New Cost Share?",
            "ri8": "Human Subjects?",
            "ri9": "Animal Use?",
            "ri10": "Prior Approval required?",
            "ri11": "Has the project previously been extended? Is this an NIH 2nd+ extension?",
            "ri12": "Is the request to extend within Sponsor’s required timeframe?",
            "ri13": "Is this a federal contract?",
            "ri14": "FAR clause 52.222-54 (e-verify)?",
            "ri15": "Fixed Price terms?",
            "ri16": "Paid in full?",
            "ri17": "All deliverables submitted?",
            "review_notes": "Review Notes",
        }
        self.fields_map_pdf = {
            "pi_name": "PI Name",
            "mod_id": "MOD/Worktag ID",
            "ri1": "SFI",
            "ri2": "RemBal",
            "ri3": "Deficit?",
            "ri4": "Greater than 25%?",
            "ri5": "Award lines",
            "ri6": "TempReq",
            "ri7": "CostShare",
            "ri8": "HumSub",
            "ri9": "AnimalUse",
            "ri10": "PriorApp",
            "ri11": "PrevExt?",
            "ri12": "ExtendInTime?",
            "ri13": "FedContract?",
            "ri14": "FAR clause 5222254",
            "ri15": "Fixed Price terms",
            "ri16": "Paid in full",
            "ri17": "All deliverables  submitted",
            "review_notes": "Review Notes",
        }
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

    #
    # --------------------- NAVIGATION & PAGE MANAGEMENT ---------------------
    #
    def run(self) -> None:
        """Entry point for app that manages which page to display."""
        current_page = st.session_state.get("current_page", "")
        if not current_page:
            current_page = "auth"
            st.session_state["current_page"] = current_page

        if current_page == "auth":
            self.instantiate_auth_page()
        elif current_page == "landing":
            self.instantiate_landing_page()
        elif current_page == "query":
            self.instantiate_query_page()

    # TODO: We can use st.navigation for this
    def change_page(self, page: str) -> None:
        """Changes the current page in session state and reruns the app."""
        if page not in ["auth", "landing", "query"]:
            raise ValueError(
                f"Invalid page: {page}. Must be one of 'auth', 'landing', or 'query'."
            )
        st.session_state["current_page"] = page

    #
    # --------------------- UTILITY METHODS ---------------------
    #
    def get_curr_mod(self) -> str:
        return st.session_state.get("curr_mod", "")

    def get_curr_pi_name(self) -> str:
        curr_vals = st.session_state.get("curr_vals", {})
        return curr_vals.get("pi_name", "").get("val", "")

    def get_curr_filename(self) -> str:
        mod_id = self.get_curr_mod()
        pi_name = self.get_curr_pi_name()
        return (
            f"Review_Matrix_{pi_name.replace(',', '_')}_{mod_id}_"
            f"{datetime.now().strftime('%Y-%m-%d')}.pdf"
        )

    #
    # --------------------- AUTH PAGE ---------------------
    #
    def get_mfa_message(self) -> None:
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
                    f"Request for atuh code failed. Status code {response.status_code}"
                )
        except requests.RequestException as e:
            st.error(f"Failed to contact server: {e}")

    def get_user_auth(self) -> None:
        """Retrieve the user's access token after device flow authentication."""
        try:
            response = requests.get(
                "http://backend:8000/acquire_access_token/")
            if response.status_code == 200:
                self.change_page("landing")  # Includes the "Proceed" button
            else:
                st.error(
                    f"Request for token failed. Status code {response.status_code}"
                )
        except requests.RequestException as e:
            st.error(f"Failed to contact server: {e}")

    def instantiate_auth_page(self) -> None:
        """Displays the authentication page."""
        placeholder = st.empty()
        with placeholder.container():
            st.title("Get your Login Code to Start Automatic Form-Filling.")
            st.button(
                "Get Code",
                key="authenticate",
                on_click=self.get_mfa_message,
            )

            auth_message = st.session_state.get("auth_message", "")
            if auth_message:
                st.write(auth_message)
                st.text("After authentication, click proceed.")

            if st.session_state.get("show_proceed", False):
                st.button(
                    "Proceed", key="ProceedButtonAuth", on_click=self.get_user_auth
                )

    def instantiate_landing_page(self) -> None:
        """Displays the landing page for collecting MOD/Worktag ID."""
        placeholder = st.empty()
        with placeholder.container():
            st.title("Editable Form - Extension Review Matrix")
            st.subheader("Enter a MOD ID to Prefill the Review Matrix")

            # Prefill the text input with "MOD"
            mod_id_input = st.text_input(
                "MOD/Worktag ID:", value="MOD", key="curr_mod_input")

            # Check for invalid characters and display a warning if necessary
            if any(char.isalpha() and char.upper() not in "MOD" for char in mod_id_input):
                st.warning(
                    "Please ensure the MOD ID only contains 'MOD' followed by numbers.")

            # Define a callback function for the "Proceed" button
            def proceed_callback():
                # Convert the input to uppercase and ensure it starts with "MOD"
                mod_id = mod_id_input.upper()
                if not mod_id.startswith("MOD"):
                    mod_id = "MOD" + mod_id.lstrip("MOD")

                # Update the session state with the formatted MOD ID
                st.session_state["curr_mod"] = mod_id

                # Call the fetch_autofill method
                self.fetch_autofill()

            # Button to proceed with the form submission
            st.button("Proceed", key="ProceedButtonLanding",
                      on_click=proceed_callback)

    #
    # --------------------- QUERY PAGE ---------------------
    #
    def instantiate_query_page(self) -> None:
        """
        Displays the query page with update, download, and restore functions.

        The values displayed are pulled from "curr_vals" in state, which reflect
        the most recent user edits
        """
        placeholder = st.empty()
        data = st.session_state.get("curr_vals", {})

        with placeholder.container():
            st.title("Editable Form - Extension Review Matrix")
            self._show_basic_info_fields(data)
            if data.get("mod_id", {}).get("val", ""):
                self._show_review_fields(data)
                self._show_review_notes(data)
            self._show_utility_buttons()

        # Autosave the updated values
        self.autosave_values()

    def autosave_values(self) -> None:
        """
        Autosave the filled entries from user input and save to session state.

        This method is called whenever the form is displayed to ensure changes are saved.
        """
        updated = st.session_state.get("curr_vals", {}).copy()
        for key in self.fields_map:
            updated[key] = {
                "val": st.session_state.get(key, ""),
                "notes": st.session_state.get(f"{key}_notes", ""),
            }

        st.session_state["curr_vals"] = updated
        st.session_state["curr_pdf_bytes"] = self.fill_pdf_to_bytes()

    def _show_basic_info_fields(self, data: dict) -> None:
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

    def _show_review_fields(self, data: dict) -> None:
        """Displays the fields except the 'review_notes' entry."""
        fields_in_order = [
            field for field in self.fields_map if field != "review_notes"
        ]

        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.subheader("**Review Items**")
        with col2:
            st.subheader("**Action**")
        with col3:
            st.subheader("**Notes**")

        for ri_field in fields_in_order:
            field_label = self.fields_map[ri_field]
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.text_input(
                    field_label,
                    value=data.get(ri_field, {}).get("val", ""),
                    key=ri_field,
                )
            with col2:
                helper_text = self.fields.get(field_label, "")
                if helper_text:
                    st.caption(helper_text)
            with col3:
                st.text_area(
                    f"Notes ({field_label})",
                    value=data.get(ri_field, {}).get("notes", ""),
                    key=f"{ri_field}_notes",
                    height=100,
                )

    def _show_review_notes(self, data: dict) -> None:
        """Displays the 'review_notes' field at the bottom."""
        review_key = "review_notes"
        if review_key in self.fields_map:
            st.subheader("Review Notes")
            st.text_area(
                label=" ",
                value=data.get(review_key, {}).get("val", ""),
                key=review_key,
                height=300,
            )

    def _show_utility_buttons(self) -> None:
        """Displays sidebar buttons for download, restore, and new mod."""
        with st.sidebar:
            st.markdown("### Toolbar")
            st.write(
                "*Below you'll find options to reset or download your form data.*")

            # Define a callback function for the download button
            def download_callback():
                self.autosave_values()
                st.session_state["curr_pdf_bytes"] = self.fill_pdf_to_bytes()

            st.download_button(
                "Download PDF",
                data=self.get_pdf_bytes(),
                file_name=self.get_curr_filename(),
                key="DownloadPDFButton",
                help="Generate and download a filled-out PDF form based on your last save.",
                use_container_width=True,
                on_click=download_callback
            )
            st.button(
                "Restore Autofill",
                key="RestoreAutofiller",
                on_click=self.restore_autofiller_responses,
                help="Undo any changes you've made and revert to the original autofilled responses.",
                use_container_width=True
            )
            st.button(
                "New Mod",
                key="NewMod",
                on_click=self.new_mod,
                help="Return to the landing page to enter a different MOD/Worktag ID.",
                use_container_width=True
            )
            
    def get_pdf_bytes(self) -> bytes:
        """Generate and return the PDF bytes."""
        self.autosave_values()
        return st.session_state.get("curr_pdf_bytes", b"")
    
    def new_mod(self) -> None:
        """Switch back to landing page."""
        # TODO: Reset the state before transition
        self.change_page("landing")

    def restore_autofiller_responses(self) -> None:
        """Revert to original autofiller responses."""
        # print(st.session_state["curr_vals"])
        # print(st.session_state["autofilled_vals"])
        st.session_state["curr_vals"] = st.session_state.get(
            "autofilled_vals", {})
        st.session_state["curr_pdf_bytes"] = self.fill_pdf_to_bytes()

    def update_values(self) -> None:
        """
        Update the filled entries from user input and save to session state.

        After execution, remain on the query page.
        """
        updated = st.session_state.get("curr_vals", {}).copy()
        for key in self.fields_map:
            updated[key] = {
                "val": st.session_state.get(key, ""),
                "notes": st.session_state.get(f"{key}_notes", ""),
            }

        st.session_state["curr_vals"] = updated
        st.session_state["curr_pdf_bytes"] = self.fill_pdf_to_bytes()
        st.session_state["page"] = "query"

    #
    # --------------------- PDF DOWNLOAD ---------------------
    #
    def fill_pdf_to_bytes(self) -> bytes:
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
                    for key, field_name in self.fields_map_pdf.items():
                        if field_name:
                            val = updated.get(key, {}).get("val", "")
                            writer.update_page_form_field_values(
                                page, {field_name: val})
                    writer.add_page(page)

            pdf_bytes = BytesIO()
            writer.write(pdf_bytes)
            pdf_bytes.seek(0)

            return pdf_bytes.getvalue()

        except Exception as e:
            st.error(f"An error occurred while creating the PDF: {e}")
            return b""

    #
    # --------------------- SERVER REQUEST ---------------------
    #
    def fetch_autofill(self) -> None:
        """
        Get the autofiller responses from the backend, store them in state, and
        then go to the query page.
        """
        mod_id = self.get_curr_mod()

        try:
            response = requests.get(
                "http://backend:8000/run", params={"mod_id": mod_id}
            )
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    data = json.loads(json_data.get("Data", None))
                    if data is None:
                        st.error("No 'Data' field in JSON response.")
                        return
                    st.session_state["autofilled_vals"] = data
                    st.session_state["curr_vals"] = data.copy()
                    # Requires curr_vals in state
                    st.session_state["curr_pdf_bytes"] = self.fill_pdf_to_bytes()
                    self.change_page("query")
                except (json.JSONDecodeError, TypeError) as e:
                    st.error(f"Error processing data: {e}")
            else:
                try:
                    detail = response.json().get("detail", "Unknown error")
                except json.JSONDecodeError:
                    detail = "No JSON to parse."
                st.error(f"Error from server: {detail}")
        except requests.RequestException as exc:
            st.error(f"Error connecting to server: {exc}")


def main():
    """Instantiate and run the streamlit app."""
    app = StreamLitApp()
    app.run()


if __name__ == "__main__":
    main()
