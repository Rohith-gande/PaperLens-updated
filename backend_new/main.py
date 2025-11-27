"""
PaperLens Backend - Clean & Modular FastAPI Application
Core features: Search, Fetch, Ask Question, Compare Papers
Using Sentence Transformers for embeddings (no API key needed)
"""
import os
import math
from datetime import datetime, timezone
from typing import Optional, Dict

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Auth
from auth.firebase_auth import verify_token
from routes.protected import router as protected_router

# Models
from models.schemas import (
    SearchRequest,
    FetchPaperRequest,
    QuestionRequest,
    ComparisonRequest,
    SavePaperRequest
)

# Services
from services.semantic_scholar_service import SemanticScholarService
from services.paper_ranking_service import rank_papers

# RAG
from rag.rag_pipeline import (
    process_paper_with_source_priority,
    answer_question_with_rag,
    get_paper_id_from_url,
    vector_stores,
    paper_metadata
)
from rag.paper_comparison import compare_multiple_papers

load_dotenv()

app = FastAPI(title="PaperLens API", version="2.1.0")

# -----------------------
# MongoDB Setup
# -----------------------
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'research_assistant')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

# -----------------------
# CORS
# -----------------------
origins = [os.getenv('FRONTEND_URL', 'http://localhost:3000'), os.getenv('VITE_FRONTEND_URL', '')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Include protected routes
# -----------------------
app.include_router(protected_router)


# ============================================================
# CORE API ENDPOINTS
# ============================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.1.0", "embeddings": "sentence-transformers"}


@app.post("/api/search")
async def search_papers(request: SearchRequest, decoded=Depends(verify_token)):
    """
    Search research papers using Semantic Scholar API
    Returns ranked list of papers
    """
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Fetch papers from Semantic Scholar
        papers = await SemanticScholarService.search_papers(query, limit=20)

        # Rank papers by relevance using Sentence Transformers
        ranked_papers = rank_papers(query, papers, top_k=20)

        # Handle pagination (default 5 per page)
        try:
            page = max(1, int(request.page))
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = max(1, min(5, int(request.page_size)))
        except (TypeError, ValueError):
            page_size = 5

        total = len(ranked_papers)
        total_pages = math.ceil(total / page_size) if total else 1
        page = min(page, total_pages) if total else 1

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paged_results = ranked_papers[start_index:end_index]

        # Save search to user history
        user_id = decoded['uid']
        await db.searches.insert_one({
            "user_id": user_id,
            "query": query,
            "results": ranked_papers,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {
            "results": paged_results,
            "meta": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fetch-paper")
async def fetch_paper(request: FetchPaperRequest, decoded=Depends(verify_token)):
    """
    Fetch and process a research paper (PDF or URL)
    Creates vectorstore for RAG pipeline using Sentence Transformers
    """
    pdf_url = request.pdf_url
    paper_title = request.paper_title
    incoming_info = request.paper_info or {}

    if not pdf_url:
        raise HTTPException(status_code=400, detail="PDF URL is required")

    try:
        paper_id = get_paper_id_from_url(pdf_url)

        # Check if paper is already processed (in memory or on disk)
        from rag.rag_pipeline import get_or_load_vectorstore, load_metadata_from_disk
        existing_vectorstore = get_or_load_vectorstore(paper_id)
        
        if existing_vectorstore:
            # Paper already processed, return success without re-processing
            existing_metadata = load_metadata_from_disk(paper_id)
            if existing_metadata:
                # Determine source type
                test_docs = existing_vectorstore.similarity_search("test", k=1)
                source_type = 'metadata' if test_docs and len(test_docs[0].page_content) < 1000 else 'pdf'
                
                message = f"✅ Paper already loaded! I'm ready to answer questions about '{paper_title}'."
                return {
                    "success": True,
                    "paper_id": paper_id,
                    "source_type": source_type,
                    "message": message,
                    "cached": True
                }

        # Merge incoming paper_info with required fields
        paper_info = {
            'url': pdf_url,
            'title': paper_title,
            'authors': incoming_info.get('authors', ''),
            'year': incoming_info.get('year', ''),
            'abstract': incoming_info.get('abstract', ''),
            'external_ids': incoming_info.get('external_ids') or incoming_info.get('externalIds', {})
        }

        # Process paper with source priority pipeline
        vector_store, source_type = process_paper_with_source_priority(paper_info, paper_id)

        if vector_store:
            # User-friendly messages - don't reveal source details
            if source_type == 'pdf':
                message = f"✅ Paper loaded successfully! I've analyzed '{paper_title}' and I'm ready to answer your questions."
            else:
                message = f"✅ Paper information loaded! I'm ready to help you with '{paper_title}'."
            
            return {
                "success": True,
                "paper_id": paper_id,
                "source_type": source_type,  # Internal use only
                "message": message,
                "cached": False
            }
        else:
            return {
                "success": False,
                "paper_id": paper_id,
                "source_type": source_type,
                "message": "Unable to load paper content. Please check if the paper URL is accessible."
            }

    except Exception as e:
        print(f"[ERROR] Fetch paper failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask-question")
async def ask_question(request: QuestionRequest, decoded=Depends(verify_token)):
    """
    Ask a question about a specific paper using RAG pipeline
    Returns answer (confidence removed from response)
    """
    pdf_url = request.pdf_url
    question = request.question
    paper_info = request.paper_info

    if not pdf_url or not question:
        raise HTTPException(status_code=400, detail="PDF URL and question are required")

    try:
        paper_id = get_paper_id_from_url(pdf_url)

        # Get paper metadata if not provided
        if not paper_info:
            from rag.rag_pipeline import paper_metadata, load_metadata_from_disk
            paper_info = paper_metadata.get(paper_id) or load_metadata_from_disk(paper_id)

        # Answer question using RAG
        result = await answer_question_with_rag(paper_id, question, paper_info)

        # Save to Q&A history in MongoDB (persistent storage)
        user_id = decoded['uid']
        try:
            await db.qa_history.insert_one({
                "user_id": user_id,
                "paper_id": paper_id,
                "pdf_url": pdf_url,
                "question": question,
                "answer": result['answer'],
                "source_type": result['source_type'],
                "citation": result.get('citation', ''),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            print(f"[SUCCESS] Saved Q&A to history for user {user_id}")
        except Exception as e:
            print(f"[WARN] Failed to save Q&A history: {e}")
            # Don't fail the request if history save fails

        # Remove confidence from response
        response = {
            'answer': result['answer'],
            'source_type': result.get('source_type', ''),
            'citation': result.get('citation', '')
        }
        
        return response

    except Exception as e:
        print(f"[ERROR] Ask question failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare-papers")
async def compare_papers(request: ComparisonRequest, decoded=Depends(verify_token)):
    """
    Compare multiple research papers using RAG
    Returns comprehensive comparison with citations
    """
    # Derive paper_ids from provided papers_info URLs
    derived_ids = []
    if request.papers_info:
        for info in request.papers_info:
            url = info.get('url')
            if url:
                derived_ids.append(get_paper_id_from_url(url))

    # Fallback to provided IDs if no papers_info
    paper_ids = derived_ids if len(derived_ids) >= 2 else (request.paper_ids or [])

    if not paper_ids or len(paper_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 papers required for comparison")

    if not request.comparison_query:
        raise HTTPException(status_code=400, detail="Comparison query is required")

    try:
        result = await compare_multiple_papers(paper_ids, request.papers_info, request.comparison_query)

        # Save comparison to history
        user_id = decoded['uid']
        await db.comparisons.insert_one({
            "user_id": user_id,
            "paper_ids": paper_ids,
            "comparison_query": request.comparison_query,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Remove confidence from response if present
        response = {
            'comparison': result.get('comparison', ''),
            'sources_used': result.get('sources_used', []),
            'papers_analyzed': result.get('papers_analyzed', []),
            'papers_count': result.get('papers_count', 0)
        }

        return response

    except Exception as e:
        print(f"[ERROR] Compare papers failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# USER DATA ENDPOINTS
# ============================================================

@app.post("/api/user/save-paper")
async def save_paper(request: SavePaperRequest, decoded=Depends(verify_token)):
    """Save paper to user's collection"""
    user_id = decoded['uid']
    paper = request.paper

    try:
        existing = await db.user_papers.find_one({"user_id": user_id, "paper.url": paper.get('url')})
        if existing:
            return {"success": True, "message": "Paper already in history"}

        await db.user_papers.insert_one({
            "user_id": user_id,
            "paper": paper,
            "saved_at": datetime.now(timezone.utc).isoformat()
        })
        return {"success": True, "message": "Paper saved successfully"}

    except Exception as e:
        print(f"[ERROR] Save paper failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/papers")
async def get_user_papers(decoded=Depends(verify_token)):
    """Get user's saved papers"""
    user_id = decoded['uid']

    try:
        papers = await db.user_papers.find({"user_id": user_id}).sort("saved_at", -1).to_list(length=100)
        for paper in papers:
            paper['_id'] = str(paper['_id'])
        return {"papers": papers}

    except Exception as e:
        print(f"[ERROR] Get user papers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/search-history")
async def get_search_history(decoded=Depends(verify_token)):
    """Get user's search history"""
    user_id = decoded['uid']

    try:
        searches = await db.searches.find({"user_id": user_id}).sort("timestamp", -1).limit(20).to_list(length=20)
        for search in searches:
            search['_id'] = str(search['_id'])
        return {"searches": searches}

    except Exception as e:
        print(f"[ERROR] Get search history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

