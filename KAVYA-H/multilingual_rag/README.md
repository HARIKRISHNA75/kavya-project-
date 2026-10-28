# Multilingual Multi-Document RAG Web App

A complete Flask-based Retrieval-Augmented Generation (RAG) application that supports multiple documents (PDF, DOCX, TXT) and answers questions in multiple languages.

## Features

- Upload multiple PDF, DOCX, and TXT files
- Limit each upload batch to 5 MB total
- Extract text while preserving document names and PDF page numbers
- Chunk documents and create multilingual embeddings
- Retrieve relevant chunks only from uploaded documents
- Filter retrieval to one indexed document or search across all documents
- Select the answer language independently from the question language, including English, Telugu, Tamil, Malayalam, Hindi, and more
- Answers generated **only** when the user clicks "Run Retrieval"
- Clearly structured answers with document-grounded definitions, process steps, and relevant details
- Displays only the final answer, without source documents, page numbers, citations, or retrieved excerpts
- States clearly when documents lack sufficient information
- Clean, responsive frontend (HTML/CSS/JavaScript)
- Modular Flask backend

## Project Structure

```
multilingual_rag/
├── app.py                 # Main Flask application
├── requirements.txt
├── README.md
├── .env.example
├── modules/
│   ├── __init__.py
│   ├── extractor.py       # PDF / DOCX / TXT extraction
│   ├── chunker.py
│   ├── embedder.py
│   ├── retriever.py
│   └── generator.py       # LLM answer generation
├── static/
│   ├── css/style.css
│   └── js/script.js
└── templates/
    └── index.html
```

## Setup Instructions

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> The first run downloads the multilingual embedding model (~470 MB).

### 3. Configure the LLM

Answer generation requires an LLM. Copy `.env.example` to `.env` and configure an API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Using Ollama (fully local):** Install Ollama and download a model, then configure:

```env
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=your-downloaded-multilingual-model
```

The `.env` file is local configuration and is ignored by Git.

An API key must be configured for answer generation. If it is missing, the query returns an error instead of showing retrieved document excerpts.
Choose an LLM model capable of answering in the selected output languages; responses in supported non-Latin scripts are checked before being returned.

### 4. Run the application

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

## Usage

1. Upload one or more PDF, DOCX, or TXT files (up to 5 MB total per upload).
2. Click **Upload & Process**.
3. Enter your question in any language.
4. Select the answer language. You can change it for every question, independently of the question language.
5. Optionally select a document in **Search in**, then click **Run Retrieval** to generate a detailed, grounded answer.
6. View only the final answer in the selected language.

## Supported Languages for Answers

- English
- Telugu (తెలుగు)
- Malayalam (മലയാളം)
- Tamil (தமிழ்)
- Hindi (हिन्दी)
- Kannada (ಕನ್ನಡ)
- Urdu (اردو)
- Spanish, French, German, Chinese, Arabic
- Other

## Notes

- Answers are never generated automatically after upload or while typing — only on "Run Retrieval".
- Retrieval is limited to the documents you have uploaded.
- The selected output language can differ from the language used to ask the question.
- Only the final answer is displayed; source metadata and retrieved excerpts are not returned by the query endpoint.
- If the documents do not contain enough information, the system states this clearly.
