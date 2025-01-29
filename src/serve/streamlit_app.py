import streamlit as st
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
            "Fixed Price terms?": "",
            "Paid in full?": "",
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
            "ri14" : "Fixed Price terms?",
            "ri15" : "Paid in full?",
            "ri16" : "All deliverables submitted?",
            "ri17" : "FAR clause 52.222-54 (e-verify)?",
            "notes" : "Review Notes"
        }
        self.fields_map_pdf = {
            "ri1" : "SFI",
            "ri2" : "RemBal",
            "ri3" : "Deficit",
            "ri4" : "Bal25",
            "ri5" : "AwardLines",
            "ri6" : "TempReq",
            "ri7" : "NewCS",
            "ri8" : "HumanSub",
            "ri9" : "AnimalUse",
            "ri10" : "PriorApp",
            "ri11" : "PrevExt",
            "ri12" : "ExtTime",
            "ri13" : "FedContract",
            "ri14" : "FixedPrice",
            "ri15" : "PaidFull",
            "ri16" : "Deliverables",
            "ri17" : "EVerify",
            "notes" : "ReviewNotes"
        }

        self.page = st.session_state.get("page", "auth")

    def change_page(self, page, mod_id=None, data=None):
        if page != "query":
            st.session_state["page"] = page
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
                st.button("Proceed", key="proceed", on_click=self.get_user_auth)
        
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
            col1, col2 = st.columns(2)
            with col1:
                pi_name = st.text_input("PI Name:", value="", key="pi_name")
            with col2:
                mod_id = st.text_input("MOD/Worktag ID:", value="", key="mod_id")
            st.button("Proceed", key="ProceedButton", on_click=self.change_page(""))
    
    def instantiate_query_page(self, mod_id, data):
        # Create a placeholder
        placeholder = st.empty()

        # Use the placeholder to display content
        with placeholder.container():
            if mod_id:  # Ensure both fields are filled before processing
                st.success("Processing your request...")            
                # Step 3: Display autofilled fields
                st.subheader("Edit the fields below")
                for rl_field, field in self.fields_map.items():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.markdown(f"**{field}**")
                        helper_text = self.fields[field]
                        if helper_text:
                            st.text(helper_text)
                        st.text_input("", value=data.get(rl_field, ""), key=self.fields_map[field])
                st.button("Update Values", key="UpdateButton", on_click=self.update_values)
                st.button("Download PDF", key="DownloadPDFButton", on_click=self.download_prefilled_pdf)

    def get_mod_id(self):
        # Retrieve PI Name and MOD/Worktag ID from user input
        mod_id = st.text_input("MOD ID")
        return mod_id

    def update_values(self):
        # Update the values in the database with the new values
        pi_name, mod_id = self.get_mod_id()
        updated_values = {}
        for key in self.fields_map:
            updated_values[key] = st.session_state[self.fields_map[key]]
        updated_values["PI Name"] = pi_name
        updated_values["MOD/Worktag ID"] = mod_id
        return updated_values

    def download_prefilled_pdf(self):
        pi_name, mod_id = self.get_pi_name_mod_id()
        updated_values = self.update_values()
        pdf_template = PdfReader(open("assets/extension_review_matrix.pdf", "rb"))
        writer = PdfWriter()
        for page in pdf_template.pages:
            writer.add_page(page)
            for key, value in self.fields_map_pdf.items():
                update_dict = {value: updated_values[key]}
                if value:
                    writer.update_page_form_field_values(page, update_dict)
        writer.write("assets/extension_review_matrix_filled.pdf")
        filename = f"Extension_Review_Matix_{pi_name}_{mod_id}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        with open(filename, "wb") as f:
            writer.write(f)
        st.text(f"Your PDF has been downloaded with filename {filename}.")
        st.button("Click here to continue with", key="ContinueButton", on_click=self.instantiate_landing_page)

    def run_app(self):
        # Run the Streamlit app after validation
        mod_id = self.get_mod_id()
        response = requests.get(f"http://localhost:8000/run", params={"mod_id": mod_id})
        if response.status_code == 200:
            try:
                data = pd.read_json(response.json()['Data'])
                st.session_state["mod_id"] = mod_id
                st.session_state["data"] = data
                self.change_page("query")
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
        else:
            st.error(f"Error from server: {response.json().get('detail', 'Unknown error')}")

    def run(self):
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