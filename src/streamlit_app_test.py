import streamlit as st
import connect

# Hardcoded fields with helper text
fields = {
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

def autofill_fields(mod_id, pi_name, df):
    autofilled_values = {}
    
    # Filter the DataFrame for the relevant rows
    filtered_df = df[(df['displayIdentifier'] == mod_id) & (df['ModificationCategory'] == "Schedule changes")]
    # st.write(filtered_df)

    if filtered_df.empty:
        st.error(f"No data found for MODID {mod_id}")
        return {key: "No data available" for key in fields}

    # Extract scalar values for calculations
    authorized_amount = filtered_df['AuthorizedAmount'].iloc[0]
    billed_to_date_amount = filtered_df['BilledToDateAmount'].iloc[0]

    for key in fields:
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
            #
            autofilled_values[key] = "TBD"
        elif key == "Temporary Request?":
            # Get from extension form
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

def get_all_data():
    conn = connect.get_connection()
    print("Executing query")
    df = connect.fetch_query_result("./sql/intial_query.sql", conn)
    print(df.head)
    return df

# Streamlit App
st.title("Editable Form - Extension Review Matrix")

# Step 1: Collect initial inputs
st.subheader("Identifying Information")
col1, col2 = st.columns(2)
with col1:
    pi_name = st.text_input("PI Name:", value="", key="pi_name")
with col2:
    mod_id = st.text_input("MOD/Worktag ID:", value="", key="mod_id")

# Step 2: Process inputs and autofill fields
if pi_name and mod_id:  # Ensure both fields are filled before processing
    st.success("Processing autofill values...")
    df = get_all_data()
    autofilled_values = autofill_fields(mod_id, pi_name, df)
    
    # Step 3: Display autofilled fields
    st.subheader("Edit the fields below")
    for field, helper_text in fields.items():
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
if st.button("Download as PDF"):
    st.write("This will allow the form to be downloaded as a PDF (functionality to be implemented).")
