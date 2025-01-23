import streamlit as st
import pandas as pd 
import requests

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
            "Has the project previously been extended?": "",
            "Is this an NIH 2nd+ extension?": "Yes - Ensure that the Budget, Progress Report, and Programmatic Justification are included as 3 separate PDFs.",
            "Is the request to extend within Sponsor’s required timeframe?": "No - Extension requires Sponsor approval.",
            "Is this a federal contract?": "Yes - Extension requires Sponsor approval.",
            "Fixed Price terms?": "",
            "Paid in full?": "",
            "All deliverables submitted?": "No - Extension requires Sponsor approval. Review fixed price terms.",
            "FAR clause 52.222-54 (e-verify)?": "Yes - Forward E-verify process to your campus contact & state in MOD comments that e-verify is required."
        }

    def get_pi_name_mod_id(self):
        # Retrieve PI Name and MOD ID from Streamlit session state
        pi_name = st.session_state.get("pi_name", "")
        mod_id = st.session_state.get("mod_id", "")
        return pi_name, mod_id
    
    def validate_input(self):
        # Validate the input fields when the "Proceed" button is clicked
        pi_name, mod_id = self.get_pi_name_mod_id()
        if not pi_name.strip():
            st.error("PI Name is required.")
        elif not mod_id.strip():
            st.error("MOD ID is required.")
        else:
            st.success("Inputs are valid. Proceeding...")
            # Display the PI Name and MOD ID
            self.run_app()

    def instantiate_landing_page(self):
        # Display the title of the Streamlit app
        st.title("Editable Form - Extension Review Matrix")

        # Step 1: Collect initial inputs
        st.subheader("Identifying Information")
        col1, col2 = st.columns(2)
        with col1:
            pi_name = st.text_input("PI Name:", value="", key="pi_name")
        with col2:
            mod_id = st.text_input("MOD/Worktag ID:", value="", key="mod_id")
        st.button("Proceed", key = "ProceedButton", on_click=self.run_app)

    def autofill_fields(self, mod_id, pi_name, df):
        autofilled_values = {}

        # Filter the DataFrame for the relevant rows
        filtered_df = df[(df['displayIdentifier'] == mod_id) & (df['ModificationCategory'] == "Schedule changes")]
        # st.write(filtered_df)

        if filtered_df.empty:
            st.error(f"No data found for MODID {mod_id}")
            return {key: "No data available" for key in self.fields}

        # Extract scalar values for calculations
        authorized_amount = filtered_df['AuthorizedAmount'].iloc[0]
        billed_to_date_amount = filtered_df['BilledToDateAmount'].iloc[0]

        for key in self.fields:
            if key == "SFI Current?":
                autofilled_values[key] = "TBD" 
            elif key == "Remaining Balance $$":
                autofilled_values[key] = authorized_amount - billed_to_date_amount
            elif key == "Is the award in deficit?":
                if (authorized_amount - billed_to_date_amount) < 0:
                    autofilled_values[key] = "Y"
                else:
                    autofilled_values[key] = "N"
            elif key == "Is the balance greater than 25% of the total award?":
                if (authorized_amount - billed_to_date_amount) / authorized_amount > 0.25:
                    autofilled_values[key] = "Y"
                else:
                    autofilled_values[key] = "N"
            elif key == "Award lines listed or 'extend all' indicated?":
                autofilled_values[key] = "TBD"
            elif key == "Temporary Request?":
                autofilled_values[key] = "TBD"
            elif key == "New Cost Share?":
                autofilled_values[key] = "TBD"
            elif key == "Human Subjects?":
                if filtered_df['isHumanSubjects'].iloc[0] == "Y":
                    autofilled_values[key] = 'Y'
                else:
                    autofilled_values[key] = 'N'
            elif key == "Animal Use?":
                if filtered_df['isAnimalUse'].iloc[0] == "Y":
                    autofilled_values[key] = 'Y'
                else:
                    autofilled_values[key] = 'N'
            elif key == "Prior Approval required?":
                autofilled_values[key] = "TBD"
            elif key == "Has the project previously been extended?":
                autofilled_values[key] = "TBD"
            elif key == "Is this an NIH 2nd+ extension?":
                autofilled_values[key] = "TBD"
            elif key == "Is the request to extend within Sponsor’s required timeframe?":
                autofilled_values[key] = "TBD"
            elif key == "Is this a federal contract?":
                autofilled_values[key] = "TBD"
            elif key == "Fixed Price terms?":
                autofilled_values[key] = "TBD"
            elif key == "Paid in full?":
                autofilled_values[key] = "TBD"
            elif key == "All deliverables submitted?":
                autofilled_values[key] = "TBD"
            elif key == "FAR clause 52.222-54 (e-verify)?":
                autofilled_values[key] = "TBD"

        return autofilled_values
    
    def instantiate_fillable_page(self, pi_name, mod_id, data):
        if pi_name and mod_id:  # Ensure both fields are filled before processing
            st.success("Processing autofill values...")
            autofilled_values = self.autofill_fields(mod_id, pi_name, data)
            
            # Step 3: Display autofilled fields
            st.subheader("Edit the fields below")
            for field, helper_text in self.fields.items():
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.markdown(f"**{field}**")
                    if helper_text:
                        st.markdown(f"<small>{helper_text}</small>", unsafe_allow_html=True)
                with col2:
                    st.text_input(label="", value=autofilled_values[field], key=field, placeholder="Enter value")
                with col3:
                    st.button("Upload documents", key=f"upload_{field}")

            # Add a dummy button at the end for downloading as PDF
            st.markdown("---")
            if st.button("Download as PDF", key="DownloadPDF"):
                st.write("This will allow the form to be downloaded as a PDF (functionality to be implemented).")

    def instantiate_error_page(self):
        # Display an error message if the service encounters an error
        st.error("The service has encountered an error. Please try again later.")

    def run_app(self):
        # Run the Streamlit app after validation
        pi_name, mod_id = self.get_pi_name_mod_id()
        response = requests.get(f"http://localhost:8000/run", params={"pi_name": pi_name, "mod_id": mod_id}).json()
        try:
            data = pd.read_json(response['Data'])
            self.instantiate_fillable_page(pi_name, mod_id, data)
        except:
            self.instantiate_error_page()

    def run(self):
        # Initialize the landing page
        self.instantiate_landing_page()

if __name__ == "__main__":
    # Instantiate and run the Streamlit app
    streamlit_app = StreamLitApp()
    streamlit_app.run()
