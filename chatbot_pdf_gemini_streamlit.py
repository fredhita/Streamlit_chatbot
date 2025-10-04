import streamlit as st
from google import genai
from langchain.text_splitter import CharacterTextSplitter
import fitz  # PyMuPDF

# --- 1. Page Configuration and Title ---
st.title("PDF Reader!📑")
st.caption("Upload a PDF and ask me anything about it!🧐")

# --- 2. Sidebar for Settings ---
with st.sidebar:
    st.subheader("Settings")
    google_api_key = st.text_input("Google AI API Key", type="password")
    

    st.subheader("Upload PDF")
    uploaded_pdf = st.file_uploader("Choose a PDF file", type="pdf")
    reset_button = st.button("Reset Conversation", help="Clear all messages and start fresh")

# --- 3. API Key and Client Initialization ---
if not google_api_key:
    st.info("Please add your Google AI API key and upload a PDF file in the sidebar to start chatting.", icon="👈🏻")
    st.stop()

if ("genai_client" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        st.session_state.genai_client = genai.Client(api_key=google_api_key)
        st.session_state._last_key = google_api_key
        st.session_state.pop("chat", None)
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"Invalid API Key: {e}")
        st.stop()

# --- 4. Chat History Management ---
if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.genai_client.chats.create(model="gemini-2.5-flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("chat", None)
    st.session_state.pop("messages", None)
    st.session_state.pop("pdf_chunks", None)
    st.rerun()

# --- 5. Handle PDF Upload ---
if uploaded_pdf is not None:
    pdf_bytes = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text")

    # Split text jadi chunk kecil biar lebih rapi
    splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(text)

    st.session_state.pdf_chunks = chunks
    st.success(f"PDF loaded! Ask me anything!")

# --- 6. Display Past Messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. Handle User Input and API Communication ---
prompt = st.chat_input("Type your message here...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Jika ada PDF, tambahkan context dari PDF ke prompt
        if "pdf_chunks" in st.session_state and st.session_state.pdf_chunks:
            context_text = "\n\n".join(st.session_state.pdf_chunks[:5])  # ambil 5 chunk pertama
            full_prompt = f"Answer based on this PDF context if relevant:\n{context_text}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        response = st.session_state.chat.send_message(full_prompt)
        answer = response.text if hasattr(response, "text") else str(response)

    except Exception as e:
        answer = f"An error occurred: {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
