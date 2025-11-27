# PaperLens Backend - New Version

## Overview

This is the new backend implementation using **Sentence Transformers** for embeddings instead of Google Generative AI embeddings. This eliminates the need for an API key for embeddings and runs everything locally.

## Key Features

- ✅ **Sentence Transformers** for embeddings (no API key needed)
- ✅ **Gemini 2.0 Flash** for LLM (still needs API key)
- ✅ **FAISS** for vector storage
- ✅ **LangChain** for RAG pipeline
- ✅ **Modular architecture** - easy to maintain and extend
- ✅ **Same API endpoints** - frontend works without changes

## Installation

### 1. Create Virtual Environment

```bash
cd backend_new
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The first time you run this, Sentence Transformers will download the model (~80MB). This happens automatically.

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
- Set `GEMINI_API_KEY` (for LLM)
- Set `MONGO_URL` (if not using default)
- Set `FIREBASE_CRED_PATH` (path to your Firebase service account key)

### 4. Run the Server

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

## API Endpoints

All endpoints remain the same as the original backend:

- `GET /api/health` - Health check
- `POST /api/search` - Search papers
- `POST /api/fetch-paper` - Fetch and process paper
- `POST /api/ask-question` - Ask question about paper
- `POST /api/compare-papers` - Compare multiple papers
- `POST /api/user/save-paper` - Save paper to collection
- `GET /api/user/papers` - Get user's saved papers
- `GET /api/user/search-history` - Get search history

## Architecture

```
backend_new/
├── rag/
│   ├── embeddings.py          # Sentence Transformer wrapper
│   ├── rag_pipeline.py        # Main RAG logic
│   └── paper_comparison.py    # Multi-paper comparison
├── services/
│   ├── semantic_scholar_service.py
│   ├── arxiv_service.py
│   └── paper_ranking_service.py
├── utils/
│   ├── pdf_processor.py
│   ├── citation_utils.py
│   ├── confidence_scorer.py
│   └── text_utils.py
├── auth/
│   └── firebase_auth.py
├── models/
│   └── schemas.py
├── routes/
│   └── protected.py
└── main.py
```

## Differences from Original Backend

1. **Embeddings**: Uses Sentence Transformers instead of Google Generative AI
2. **No Embedding API Key**: Embeddings run locally, no API calls
3. **Faster**: No network latency for embedding generation
4. **Lower Cost**: No embedding API costs
5. **Privacy**: Embeddings stay on your server

## Embedding Models

Default model: `all-MiniLM-L6-v2`
- Fast (384 dimensions)
- Good quality
- ~80MB download

To use a better model, set in `.env`:
```
EMBEDDING_MODEL=all-mpnet-base-v2
```
- Slower but better quality (768 dimensions)
- ~420MB download

## Troubleshooting

### Model Download Issues
If the model fails to download, it will automatically fall back to the default model.

### Memory Issues
If you run out of memory, use the smaller model (`all-MiniLM-L6-v2`) instead of `all-mpnet-base-v2`.

### Dependency Conflicts
All dependencies are pinned to specific versions to avoid conflicts. If you encounter issues, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## Testing

Test the health endpoint:
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "embeddings": "sentence-transformers"
}
```

## Frontend Integration

The frontend requires **no changes**. All API endpoints remain the same. Just point your frontend to the new backend URL.

## License

Same as the main project.

