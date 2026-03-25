import streamlit as st
import tempfile
import os

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClaimCheck",
    page_icon="✅",
    layout="centered",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("✅ ClaimCheck")
st.subheader("Verify scientific claims against your source document")
st.markdown(
    "Upload a scientific paper or report, enter a claim, and the AI will "
    "tell you whether the document supports it — with evidence."
)
st.divider()

# ── Sidebar: API key ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your key is never stored. It is used only for this session.",
    )
    st.markdown("---")
    st.markdown(
        "**How it works**\n\n"
        "1. Your PDF is split into overlapping chunks.\n"
        "2. Each chunk is embedded and stored in a vector index.\n"
        "3. Your claim is used to retrieve the most relevant chunks.\n"
        "4. An LLM evaluates whether those chunks support your claim."
    )

# ── Helper: build RAG chain (cached per PDF + key) ───────────────────────────
@st.cache_resource(show_spinner=False)
def build_qa_chain(pdf_bytes: bytes, api_key: str) -> RetrievalQA:
    """Load PDF, embed chunks, and return a RetrievalQA chain."""
    # Write PDF bytes to a temp file so PyPDFLoader can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()
    finally:
        os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    docs = splitter.split_documents(pages)

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    vectorstore = FAISS.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are ClaimCheck, a rigorous scientific fact-checker.

A user has provided the following scientific claim:
"{question}"

Using ONLY the excerpts from the source document below, determine whether the
claim is SUPPORTED, CONTRADICTED, or INSUFFICIENT (the document does not
contain enough information to judge).

Respond with:
1. A verdict: **SUPPORTED**, **CONTRADICTED**, or **INSUFFICIENT EVIDENCE**
2. A clear explanation (2-4 sentences) citing the relevant parts of the text.
3. The most relevant quote(s) from the document (keep each under 50 words).

Do not use any knowledge outside the provided excerpts.

---
Document excerpts:
{context}
---
""",
    )

    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0,
        openai_api_key=api_key,
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template},
    )
    return chain


# ── Main UI ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📄 Upload PDF")
    uploaded_file = st.file_uploader(
        "Choose a scientific paper or report",
        type=["pdf"],
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.success(f"Loaded: **{uploaded_file.name}**")

with col2:
    st.markdown("### 🧪 Scientific Claim")
    claim = st.text_area(
        "Enter the claim you want to verify",
        placeholder="e.g. 'The study found a statistically significant reduction in blood pressure.'",
        height=120,
        label_visibility="collapsed",
    )

st.markdown("")
check_btn = st.button("🔍 Check Claim", use_container_width=True, type="primary")

# ── Processing ────────────────────────────────────────────────────────────────
if check_btn:
    if not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not uploaded_file:
        st.error("Please upload a PDF document.")
    elif not claim.strip():
        st.error("Please enter a scientific claim to verify.")
    else:
        with st.spinner("Building document index and evaluating claim…"):
            try:
                pdf_bytes = uploaded_file.read()
                qa_chain = build_qa_chain(pdf_bytes, openai_api_key)
                result = qa_chain.invoke({"query": claim})
                answer = result.get("result", "No response returned.")

                st.divider()
                st.markdown("### 📋 Verdict")

                # Color the verdict card based on outcome
                if "SUPPORTED" in answer.upper() and "NOT SUPPORTED" not in answer.upper():
                    st.success(answer)
                elif "CONTRADICTED" in answer.upper():
                    st.error(answer)
                else:
                    st.warning(answer)

            except Exception as e:
                st.error(f"Something went wrong: {e}")