import streamlit as st
import json
import pandas as pd 
import requests
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime

class StreamLitApp:
    """
    StreamLitApp Class for the Streamlit Application, from landing page to autofilling fields.
    Functionality for user input validation, autofilling fields, and displaying the editable form.
    """
    def __init__(self):
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
            "Review Notes" : "Enter any additional notes here."
        }
        self.fields_map = {
            "ri1" : "SFI Current?",
            "ri2": "Remaining Balance $$",
            "ri3" : "Is the award in deficit?",
            "ri4" : "Is the balance greater than 25% of the total award?",
            "ri5" : "Award lines listed or 'extend all' indicated?",
            "ri6" : "Temporary Request?",
            "ri7" : "New Cost Share?",
            "ri8" : "Human Subjects?",
            "ri9" : "Animal Use?",
            "ri10" : "Prior Approval required?",
            "ri11" : "Has the project previously been extended? Is this an NIH 2nd+ extension?",
            "ri12" : "Is the request to extend within Sponsor’s required timeframe?",
            "ri13" : "Is this a federal contract?",
            "ri14" : "FAR clause 52.222-54 (e-verify)?",
            "ri15" : "Fixed Price terms?",
            "ri16" : "Paid in full?",
            "ri17" : "All deliverables submitted?",
            "review_notes" : "Review Notes"
        }
        self.fields_map_pdf = {
            "pi_name": "PI Name",
            "mod_id": "MOD/Worktag ID",
            "ri1" : "SFI",
            "ri2" : "RemBal",
            "ri3" : "Deficit?",
            "ri4" : "Greater than 25%?",
            "ri5" : "Award lines",
            "ri6" : "TempReq",
            "ri7" : "CostShare",
            "ri8" : "HumSub",
            "ri9" : "AnimalUse",
            "ri10" : "PriorApp",
            "ri11" : "PrevExt?",
            "ri12" : "ExtendInTime?",
            "ri13" : "FedContract?",
            "ri14" : "FAR clause 5222254",
            "ri15" : "Fixed Price terms",
            "ri16" : "Paid in full",
            "ri17" : "All deliverables  submitted",
            "review_notes" : "Review Notes"
        }

        self.page = st.session_state.get("page", "auth")

    def change_page(self, page, mod_id=None, data=None):
        if page != "query":
            st.session_state["page"] = page
            st.rerun()
        else:
            st.session_state["page"] = page
            st.session_state["mod_id"] = mod_id
            st.session_state["data"] = data
            st.rerun()

    def get_mfa_message(self):
        # Retrieve the MFA message from the API
        response = requests.get("http://localhost:8000/prompt_azure_mfa/")
        if response.status_code == 200:
            self.auth_message = response.json()["auth_message"]
            st.session_state["auth_message"] = self.auth_message
            st.session_state["show_proceed"] = True
        else:
            st.error("Failed to retrieve MFA message.")

    def get_user_auth(self):
        # Retrieve the access token from the API
        response = requests.get("http://localhost:8000/acquire_access_token/")
        if response.status_code == 200:
            self.change_page("landing")
        else:
            st.error("Failed to acquire access token.")

    def instantiate_auth_page(self):
        placeholder = st.empty()
        with placeholder.container():
            st.title("Authenticate for Sharepoint")
            st.button("Authenticate With 2FA", key="authenticate", on_click=self.get_mfa_message)
            st.text(st.session_state.get("auth_message", ""))
            
            if st.session_state.get("show_proceed", False):
                st.button("Proceed", key="ProceedButtonAuth", on_click=self.get_user_auth)
        
        st.text("Please only click proceed upon successful multifactor authentication.")

    def instantiate_landing_page(self):
        # Create a placeholder
        placeholder = st.empty()

        # Use the placeholder to display content
        with placeholder.container():
            # Display the title of the Streamlit app
            st.title("Editable Form - Extension Review Matrix")

            # Step 1: Collect initial inputs
            st.subheader("Identifying Information")
            mod_id = st.text_input("MOD/Worktag ID:", value="", key="mod_id")
            st.button("Proceed", key="ProceedButtonLanding", on_click=self.run_app)
    
    def instantiate_query_page(self, mod_id, data):
        # Create a placeholder
        placeholder = st.empty()

        # Use the placeholder to display content
        with placeholder.container():
            # Prefill text boxes with session state data
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("MOD/Worktag ID:", value=mod_id, key="mod_id_query")
            with col2:
                st.text_input("PI Name:", value=data["pi_name"]["val"], key="pi_name")
            if mod_id:  # Ensure both fields are filled before processing
                st.success("Populating Extension Review Matrix Template...")            
                # Step 3: Display autofilled fields
                st.subheader("Edit the fields below")
                for ri_field, field in self.fields_map.items():
                    col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
                    with col1:
                        st.markdown(f"**{field}**")
                    with col2:
                        st.text_input("", value=data[ri_field]["val"], key=ri_field)
                    with col3:
                        helper_text = self.fields[field]
                        if helper_text:
                            st.text(helper_text)
                    with col4:
                        st.text_input("Autofiller Notes", value=data[ri_field]["notes"], key=f"{ri_field}_notes")

                st.button("Update Values", key="UpdateButton", on_click=self.update_values(data["pi_name"]))
                st.button("Download PDF", key="DownloadPDFButton", on_click=self.download_prefilled_pdf)

    def get_mod_id(self):
        # Retrieve MOD/Worktag ID from session state
        return st.session_state.get("mod_id", "")

    def update_values(self, pi_name):
        # Update the values in the database with the new values
        mod_id = self.get_mod_id()
        updated_values = {}
        for key in self.fields_map:
            updated_values[key] = st.session_state[key]
        updated_values["pi_name"] = pi_name
        updated_values["mod_id"] = mod_id
        return updated_values

    # def download_prefilled_pdf(self):
    #     mod_id = self.get_mod_id()
    #     pi_name = st.session_state.get("pi_name", "")
    #     updated_values = self.update_values(pi_name)
    #     pdf_template = PdfReader(open("./assets/extension_review_matrix.pdf", "rb"))
    #     writer = PdfWriter()
    #     for page in pdf_template.pages:
    #         writer.add_page(page)
    #         for key, value in self.fields_map_pdf.items():
    #             update_dict = {value: updated_values[key]}
    #             if value:
    #                 writer.update_page_form_field_values(page, update_dict)
    #     filename = f"./assets/Extension_Review_Matix_{pi_name}_{mod_id}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    #     with open(filename, "wb") as f:
    #         writer.write(f)
    #     st.text(f"Your PDF has been downloaded with filename {filename}.")
    #     st.button("Click here to continue with", key="ContinueButton", on_click=self.change)

    def download_prefilled_pdf(self):
        """
        Downloads and writes a new PDF populated with updated values.
        Includes print() statements for debugging and Streamlit messages.
        """
        try:
            print("Starting the PDF creation process...")
            st.info("Starting the PDF creation process...")

            # Retrieve necessary data
            mod_id = self.get_mod_id()
            pi_name = st.session_state.get("pi_name", "")
            updated_values = self.update_values(pi_name)

            print(f"Retrieved mod_id: {mod_id}")
            print(f"PI name: {pi_name}")
            print(f"Updated values for PDF fields: {updated_values}")

            # Template path
            template_path = "./assets/extension_review_matrix.pdf"
            st.write(f"Reading PDF template from: {template_path}")
            print(f"Reading PDF template from {template_path}")

            # Use a 'with' block so file remains open while we're working with PyPDF2
            with open(template_path, "rb") as template_file:
                pdf_template = PdfReader(template_file)
                writer = PdfWriter()

                # Update and add each page within the same 'with' block
                for idx, page in enumerate(pdf_template.pages):
                    print(f"Processing page {idx + 1} of {len(pdf_template.pages)}...")
                    
                    for key, pdf_field_name in self.fields_map_pdf.items():
                        if pdf_field_name:
                            value_to_update = updated_values.get(key, "")
                            print(f"Updating field '{pdf_field_name}' with value '{value_to_update}'")
                            writer.update_page_form_field_values(page, {pdf_field_name: value_to_update})

                    # After updating, add the page to the writer
                    writer.add_page(page)

                # Once all pages are updated, generate the output filename
                filename = (
                    f"./assets/Extension_Review_Matrix_{pi_name}_"
                    f"{mod_id}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
                )

                st.write(f"Writing filled PDF to: {filename}")
                print(f"Writing filled PDF to: {filename}")

                with open(filename, "wb") as output_file:
                    writer.write(output_file)

            st.success(f"Your PDF has been created and saved as: {filename}")
            print("PDF creation completed successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            st.error(f"An error occurred while creating the PDF: {e}")

        st.button(
            "Click here to continue",
            key="ContinueButton",
            on_click=self.change_page("landing")
        )


    def run_app(self):
        mod_id = self.get_mod_id()
        try:
            response = requests.get("http://localhost:8000/run", params={"mod_id": mod_id})
            # print("Status code:", response.status_code)  # Debug
            # print("JSON response:", response.json())       # Debug
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    # Make sure 'Data' exists
                    data = json.loads(json_data.get("Data", None))
                    if data is None:
                        st.error("No 'Data' field in JSON response.")
                        return
                    print(type(data))

                    st.session_state["mod_id"] = mod_id
                    st.session_state["data"] = data
                    self.change_page("query", mod_id=mod_id, data=data)
                except Exception as e:
                    st.error(f"Error processing data: {e}")
            else:
                # If we do get a response but with an error code, show details
                try:
                    st.error(f"Error from server: {response.json().get('detail', 'Unknown error')}")
                except:
                    st.error("Error from server, and no JSON to parse.")

        except Exception as exc:
            # This means the request outright failed (connection issue, server not running, etc.)
            st.error(f"Error connecting to server: {exc}")

    def run(self):
        st.set_page_config(layout="wide")
        # Run the Streamlit app
        if self.page == "auth":
            self.instantiate_auth_page()
        elif self.page == "landing":
            self.instantiate_landing_page()
        elif self.page == "query":
            mod_id = st.session_state.get("mod_id")
            data = st.session_state.get("data")
            self.instantiate_query_page(mod_id, data)

if __name__ == "__main__":
    # Instantiate and run the Streamlit app
    streamlit_app = StreamLitApp()
    streamlit_app.run()