# Document AI Assistant

An AI-powered assistant that lets you upload documents (PDF, DOCX, TXT) and chat with them using natural language. The backend uses FastAPI, FAISS, and local Ollama LLMs (via LangChain) for retrieval-augmented generation. The frontend is built with Streamlit for a modern, interactive chat experience.

## Features
- Upload PDF, DOCX, or TXT files
- Embeds and indexes document content for fast semantic search
- Ask questions about your documents and get answers with citations
- Uses local Ollama LLM (e.g., Llama 3) for context-aware answers
- Modern Streamlit chat UI

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd "Document AI Assistant"
```

### 2. Create and activate a Python virtual environment
```bash
python3 -m venv ai-env
source ai-env/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the FastAPI backend
```bash
cd backend
uvicorn app:app --reload --host localhost --port 8000
```

### 5. Start the Streamlit frontend (in a new terminal)
```bash
cd frontend
streamlit run streamlit_app.py
```

### 6. (Optional) Start Ollama with your desired model
Make sure you have Ollama installed and running locally with a model like Llama 3:
```bash
ollama run llama3
```

## Usage
1. Open the Streamlit app in your browser (usually at http://localhost:8501)
2. Upload a document in the sidebar
3. Ask questions in the chat interface
4. Get answers with citations to the source document

## Project Structure
```
Document AI Assistant/
├── backend/
│   └── app.py           # FastAPI backend
├── frontend/
│   └── streamlit_app.py # Streamlit frontend
├── requirements.txt     # Python dependencies
├── company_policies.pdf # Example document
└── ...
```

## Notes
- The backend uses FAISS for vector search and Sentence Transformers for embeddings.
- Ollama must be running locally for LLM responses.
- Documents are only processed once per upload; you can ask unlimited questions after uploading.

## License
MIT License
