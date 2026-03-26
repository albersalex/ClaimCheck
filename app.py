import streamlit as st

st.set_page_config(page_title="The Science Sentry", page_icon="🔬")

st.title("🔬 The Science Sentry")
st.subheader("Junior High Science Verification Tool")

st.markdown("""
This app helps students verify scientific claims against classroom PDFs using AI. 
*Currently in Portfolio Demo Mode.*
""")

# Sidebar for instructions
with st.sidebar:
    st.header("How to use")
    st.write("1. Upload a Unit PDF (e.g., Photosynthesis).")
    st.write("2. Enter a claim you heard.")
    st.write("3. The AI cross-references the text.")

uploaded_file = st.file_uploader("Upload Classroom PDF", type="pdf")
claim = st.text_input("Enter scientific claim (e.g. 'Humans breathe CO2')")

if st.button("Verify Claim"):
    if uploaded_file and claim:
        with st.spinner('Analyzing document...'):
            # In a full version, this is where the LangChain logic lives
            st.success(f"Analysis Complete for: '{claim}'")
            st.info("Verification: Based on the uploaded document, this claim requires further evidence. (Demo logic active)")
    else:
        st.warning("Please provide both a PDF and a claim.")
