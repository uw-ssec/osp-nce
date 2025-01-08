import streamlit as st

# Hardcoded fields from the PDF with helper text
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

# Streamlit App
st.title("Editable Form - Extension Review Matrix")

# Bring identifying fields to the top
st.subheader("Identifying Information")
col1, col2 = st.columns(2)
with col1:
    st.text_input("PI Name:", value="", key="PI Name:")
with col2:
    st.text_input("MOD/Worktag ID:", value="", key="MOD/Worktag ID:")

# Table-like layout for other fields
st.subheader("Edit the fields below")
for field, helper_text in fields.items():
    col1, col2, col3 = st.columns([1, 2, 1])  # Add a third column for the "Upload documents" button
    with col1:
        st.markdown(f"**{field}**")
        if helper_text:
            st.markdown(f"<small>{helper_text}</small>", unsafe_allow_html=True)
    with col2:
        st.text_input(label="", value="NA", key=field, placeholder="Enter value")  # Placeholder aligns input box
    with col3:
        st.button("Upload documents", key=f"upload_{field}")

# Add a dummy button at the end for downloading as PDF
st.markdown("---")
if st.button("Download as PDF"):
    st.write("This will allow the form to be downloaded as a PDF (functionality to be implemented).")
