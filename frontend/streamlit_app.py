import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Document AI Assistant", layout="wide")
st.title("📄 Document AI Assistant")

# --- Sidebar for file upload ---
with st.sidebar:
    st.header("Upload Document")
    if "doc_uploaded" not in st.session_state:
        st.session_state.doc_uploaded = False
    uploaded_file = st.file_uploader("Choose a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
    if uploaded_file and not st.session_state.doc_uploaded:
        with st.spinner("Uploading and processing document..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post(f"{BACKEND_URL}/upload/", files=files)
            if response.ok:
                st.success("Document uploaded and processed!")
                st.session_state.doc_uploaded = True
            else:
                st.error(response.json().get("error", "Upload failed."))
    elif st.session_state.doc_uploaded:
        st.success("Document already uploaded. You can now chat with your document.")

# --- Main Chat UI ---
st.markdown("""
<style>
.chat-bubble {
    background: #f1f3f6;
    border-radius: 10px;
    padding: 1em;
    margin-bottom: 0.5em;
    color: #222;
}
.assistant-bubble {
    background: linear-gradient(90deg, #dbeafe 0%, #f0f9ff 100%);
    border-radius: 10px;
    padding: 1em;
    margin-bottom: 0.5em;
    color: #0a3d62;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.citation-box {
    background: #f9fafb;
    border-radius: 6px;
    padding: 0.5em 1em;
    margin: 0.2em 0 0.5em 0.5em;
    font-size: 0.95em;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

st.header("Chat with your documents")
st.write("Ask a question about your documents:")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("", key="user_input", placeholder="Type your question and press Enter...")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    with st.spinner("Getting answer..."):
        payload = {"question": user_input}
        response = requests.post(f"{BACKEND_URL}/query/", json=payload)
        if response.ok:
            data = response.json()
            answer = data.get("answer", "No answer returned.")
            citations = data.get("citations", [])
            st.session_state.chat_history.append((user_input, answer, citations))
        else:
            st.error(response.json().get("error", "Query failed."))

# --- Display chat history ---
st.subheader(":speech_balloon: Conversation")
for q, a, c in st.session_state.chat_history[::-1]:
    st.markdown(f'<div class="chat-bubble"><b>You:</b> {q}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="assistant-bubble"><b>Assistant:</b> {a}</div>', unsafe_allow_html=True)
    if c:
        st.markdown("<div class='citation-box'><b>Citations:</b>", unsafe_allow_html=True)
        for cite in c:
            st.markdown(f"<div class='citation-box'>File: {cite['filename']}, Page: {cite['page']}, Chunk: {cite['chunk_id']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
