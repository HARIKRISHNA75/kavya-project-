import os
import uuid
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from modules.extractor import extract_text
from modules.chunker import chunk_text
from modules.embedder import MultilingualEmbedder
from modules.retriever import retrieve
from modules.generator import LANGUAGE_NAMES, generate_answer

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["UPLOAD_FOLDER"] = "uploads"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES + 64 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("vectorstore", exist_ok=True)

# Global embedder (in production you may want per-session storage)
embedder = MultilingualEmbedder()


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def get_index_documents(chunks):
    documents_by_id = {}
    source_counts = {}
    for chunk in chunks:
        source = chunk["source"]
        document_id = chunk.get("document_id", source)
        if document_id not in documents_by_id:
            source_counts[source] = source_counts.get(source, 0) + 1
            documents_by_id[document_id] = {
                "id": document_id,
                "name": source,
                "number": source_counts[source],
            }

    for document in documents_by_id.values():
        if source_counts[document["name"]] > 1:
            document["label"] = f'{document["name"]} ({document["number"]})'
        else:
            document["label"] = document["name"]
        del document["number"]

    return list(documents_by_id.values())


@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "The total upload limit is 5 MB."}), 413


@app.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files selected"}), 400

    total_size = 0
    for file in files:
        file.stream.seek(0, os.SEEK_END)
        total_size += file.stream.tell()
        file.stream.seek(0)
    if total_size > MAX_UPLOAD_BYTES:
        return jsonify({"error": "The total upload limit is 5 MB."}), 413

    all_docs = []
    uploaded_names = []

    try:
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                document_id = uuid.uuid4().hex
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                file.save(filepath)

                docs = extract_text(filepath, filename)
                for doc in docs:
                    doc["document_id"] = document_id
                all_docs.extend(docs)
                uploaded_names.append(filename)

                # clean up temporary file after extraction
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            else:
                return jsonify({"error": f"Unsupported file type: {file.filename}"}), 400

        if not all_docs:
            return jsonify({"error": "No extractable text found in the uploaded files."}), 400

        chunks = chunk_text(all_docs)
        embedder.build_index(chunks)
        embedder.save()

        return jsonify({
            "message": f"Successfully processed {len(uploaded_names)} document(s).",
            "chunks": len(chunks)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    language = data.get("language", "en")
    requested_document_id = data.get("document_id")
    document_id = requested_document_id.strip() if isinstance(requested_document_id, str) else ""

    if not question:
        return jsonify({"error": "Please enter a question."}), 400
    if not isinstance(language, str) or language not in LANGUAGE_NAMES:
        return jsonify({"error": "Please select a supported answer language."}), 400

    if not embedder.is_ready():
        # try to load previous index
        try:
            embedder.load()
        except Exception:
            return jsonify({"error": "No documents have been uploaded yet. Please upload documents first."}), 400

    try:
        if document_id:
            available_documents = get_index_documents(embedder.chunks)
            if document_id not in {document["id"] for document in available_documents}:
                return jsonify({"error": "The selected document is not in the current index. Please select it again."}), 400

        contexts = retrieve(
            embedder,
            question,
            top_k=8,
            document_id=document_id or None,
        )
        answer = generate_answer(question, contexts, language)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def status():
    ready = embedder.is_ready()
    if not ready:
        try:
            embedder.load()
            ready = True
        except Exception:
            ready = False
    return jsonify({
        "ready": ready,
        "num_chunks": len(embedder.chunks) if ready else 0,
        "documents": get_index_documents(embedder.chunks) if ready else [],
        "llm_configured": bool(os.getenv("OPENAI_API_KEY")),
        "llm_model": os.getenv("OPENAI_MODEL") if os.getenv("OPENAI_API_KEY") else None,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
