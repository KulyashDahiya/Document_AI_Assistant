import os
import pickle
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from io import BytesIO
import pdfplumber
from docx import Document
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Document AI Chatbot",
    version="1.0",
    description="An AI chatbot that allows you to interact with your documents"
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
vector_db_file = "vector_db.pickle"

# Load the FAISS index if it exists
if os.path.exists(vector_db_file):
    with open(vector_db_file, 'rb') as f:
        faiss_index = pickle.load(f)
else:
    faiss_index = None

# Store chunks and metadata
chunks = []  # Each chunk: {"text": ..., "filename": ..., "chunk_id": ..., "page": ...}
CHUNK_SIZE = 512

def chunk_text(text, filename, page=None):
    words = text.split()
    chunked = []
    for i in range(0, len(words), CHUNK_SIZE):
        chunk_text = " ".join(words[i:i + CHUNK_SIZE])
        chunked.append({
            "text": chunk_text,
            "filename": filename,
            "chunk_id": i // CHUNK_SIZE,
            "page": page
        })
    return chunked

def extract_text_from_pdf(pdf_file, filename):
    with pdfplumber.open(BytesIO(pdf_file)) as pdf:
        all_chunks = []
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                all_chunks.extend(chunk_text(text, filename, page=page_num+1))
    return all_chunks

def extract_text_from_docx(docx_file, filename):
    doc = Document(BytesIO(docx_file))
    text = "\n".join([para.text for para in doc.paragraphs])
    return chunk_text(text, filename)

def extract_text_from_txt(txt_file, filename):
    text = txt_file.decode("utf-8")
    return chunk_text(text, filename)

def generate_embeddings(chunk_list):
    return embedding_model.encode([c["text"] for c in chunk_list])

def create_faiss_index(embeddings):
    embedding_matrix = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(embedding_matrix.shape[1])
    index.add(embedding_matrix)
    return index

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'txt']:
            return {"error": "Invalid file type. Please upload a PDF, DOCX, or TXT."}
        file_content = await file.read()
        filename = file.filename
        if file_extension == 'pdf':
            new_chunks = extract_text_from_pdf(file_content, filename)
        elif file_extension == 'docx':
            new_chunks = extract_text_from_docx(file_content, filename)
        elif file_extension == 'txt':
            new_chunks = extract_text_from_txt(file_content, filename)
        if not new_chunks:
            return {"error": "No text extracted from the file."}
        global chunks
        chunks.extend(new_chunks)
        embeddings = generate_embeddings(new_chunks)
        global faiss_index
        if faiss_index is None:
            faiss_index = create_faiss_index(embeddings)
        else:
            faiss_index.add(np.array(embeddings).astype("float32"))
        with open(vector_db_file, 'wb') as f:
            pickle.dump(faiss_index, f)
        return {"message": "Document uploaded and processed successfully."}
    except Exception as e:
        print(f"Error processing the document: {e}")
        return {"error": f"Failed to process the document. Error: {str(e)}"}

@app.post("/query/")
async def query_document(query: dict):
    question = query.get('question')
    if not chunks or faiss_index is None:
        return {"error": "No document has been uploaded or indexed yet."}
    query_embedding = generate_embeddings([{"text": question}])
    D, I = faiss_index.search(np.array(query_embedding).astype("float32"), 5)
    top_chunks = [chunks[i] for i in I[0] if i >= 0 and i < len(chunks)]
    if not top_chunks:
        return {"error": "No relevant chunks found for the query."}
    context = "\n".join([c["text"] for c in top_chunks])
    try:
        model = Ollama(model="llama3")
        prompt = f"Answer the question using the context below. Cite the filename and page/chunk if possible.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        response = model.invoke(prompt)
        citations = [{"filename": c["filename"], "page": c["page"], "chunk_id": c["chunk_id"]} for c in top_chunks]
        return {"answer": response, "citations": citations}
    except Exception as e:
        print(f"Error from Ollama: {e}")
        return {"error": f"Error from Ollama: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
