"""RAG pipeline using Sentence Transformers + Gemini LLM"""
import os
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from rag.embeddings import SentenceTransformerEmbeddings
from utils.pdf_processor import resolve_pdf_url, download_pdf, extract_text_from_pdf
from services.semantic_scholar_service import SemanticScholarService
from services.arxiv_service import search_arxiv_for_paper, ArxivService
from utils.confidence_scorer import ConfidenceScorer
from utils.citation_utils import extract_citation_info

# Initialize embeddings (Sentence Transformers - NO API KEY NEEDED)
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)

# Initialize LLM (Gemini - requires API key from environment)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required. Please set it in your .env file.")

os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
llm = GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.3)

# Text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# Persistent storage directory
VECTORSTORE_DIR = Path("./vectorstores")
VECTORSTORE_DIR.mkdir(exist_ok=True)
METADATA_DIR = Path("./vectorstores/metadata")
METADATA_DIR.mkdir(exist_ok=True)

# In-memory storage (cache)
vector_stores: Dict[str, FAISS] = {}
paper_metadata: Dict[str, Dict] = {}


def get_paper_id_from_url(url: str) -> str:
    """Generate consistent paper ID from URL"""
    return str(abs(hash(url)))


def get_vectorstore_path(paper_id: str) -> Path:
    """Get path for vectorstore file"""
    return VECTORSTORE_DIR / f"{paper_id}"


def get_metadata_path(paper_id: str) -> Path:
    """Get path for metadata file"""
    return METADATA_DIR / f"{paper_id}.json"


def save_vectorstore_to_disk(vectorstore: FAISS, paper_id: str) -> bool:
    """Save vectorstore to disk for persistence"""
    try:
        vectorstore_path = get_vectorstore_path(paper_id)
        vectorstore.save_local(str(vectorstore_path))
        print(f"[SUCCESS] Saved vectorstore to disk: {vectorstore_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save vectorstore: {e}")
        return False


def load_vectorstore_from_disk(paper_id: str) -> Optional[FAISS]:
    """Load vectorstore from disk if it exists"""
    try:
        vectorstore_path = get_vectorstore_path(paper_id)
        if vectorstore_path.exists() and (vectorstore_path / "index.faiss").exists():
            vectorstore = FAISS.load_local(str(vectorstore_path), embeddings, allow_dangerous_deserialization=True)
            print(f"[SUCCESS] Loaded vectorstore from disk: {vectorstore_path}")
            return vectorstore
    except Exception as e:
        print(f"[WARN] Failed to load vectorstore from disk: {e}")
    return None


def save_metadata_to_disk(paper_id: str, paper_info: Dict) -> bool:
    """Save paper metadata to disk"""
    try:
        import json
        metadata_path = get_metadata_path(paper_id)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(paper_info, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save metadata: {e}")
        return False


def load_metadata_from_disk(paper_id: str) -> Optional[Dict]:
    """Load paper metadata from disk"""
    try:
        import json
        metadata_path = get_metadata_path(paper_id)
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load metadata: {e}")
    return None


def get_or_load_vectorstore(paper_id: str) -> Optional[FAISS]:
    """Get vectorstore from memory or load from disk"""
    # Check in-memory cache first
    if paper_id in vector_stores:
        return vector_stores[paper_id]
    
    # Try loading from disk
    vectorstore = load_vectorstore_from_disk(paper_id)
    if vectorstore:
        vector_stores[paper_id] = vectorstore
        # Also load metadata if available
        metadata = load_metadata_from_disk(paper_id)
        if metadata:
            paper_metadata[paper_id] = metadata
        return vectorstore
    
    return None


def create_vectorstore_from_text(text: str, paper_id: str, paper_info: Dict) -> FAISS:
    """Create FAISS vectorstore from text using Sentence Transformers"""
    # Split text into chunks
    chunks = text_splitter.split_text(text)

    # Create Document objects with metadata
    documents = [
        Document(
            page_content=chunk,
            metadata={
                'paper_id': paper_id,
                'title': paper_info.get('title', ''),
                'authors': paper_info.get('authors', ''),
                'year': paper_info.get('year', ''),
                'chunk_index': i
            }
        )
        for i, chunk in enumerate(chunks)
    ]

    # Create FAISS vectorstore with Sentence Transformer embeddings
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save to disk for persistence
    save_vectorstore_to_disk(vectorstore, paper_id)
    save_metadata_to_disk(paper_id, paper_info)

    print(f"[SUCCESS] Created vectorstore with {len(chunks)} chunks for paper: {paper_info.get('title', 'Unknown')}")

    return vectorstore


def process_paper_with_source_priority(paper_info: Dict, paper_id: str) -> Tuple[Optional[FAISS], str]:
    """
    Process paper using source priority pipeline:
    1. Check if already processed (in memory or disk)
    2. Direct PDF from provided URL
    3. Semantic Scholar PDF
    4. arXiv PDF
    5. Metadata only
    """
    title = paper_info.get('title', '')
    authors = paper_info.get('authors', '')
    abstract = paper_info.get('abstract', '')
    paper_url = paper_info.get('url', '')

    print(f"[INFO] Processing paper: {title}")

    # Check if paper is already processed
    existing_vectorstore = get_or_load_vectorstore(paper_id)
    if existing_vectorstore:
        print(f"[INFO] Paper already processed, using cached vectorstore")
        existing_metadata = paper_metadata.get(paper_id) or load_metadata_from_disk(paper_id)
        if existing_metadata:
            # Determine source type from existing metadata
            test_docs = existing_vectorstore.similarity_search("test", k=1)
            source_type = 'metadata' if test_docs and len(test_docs[0].page_content) < 1000 else 'pdf'
            return existing_vectorstore, source_type

    # Priority 0: Direct PDF from provided URL
    resolved_from_url = resolve_pdf_url(paper_url)
    direct_pdf = paper_info.get('pdf_url') or resolved_from_url

    if direct_pdf:
        pdf_content = download_pdf(direct_pdf)
        if pdf_content:
            text = extract_text_from_pdf(pdf_content)
            if text and len(text) > 500:
                vectorstore = create_vectorstore_from_text(text, paper_id, paper_info)
                vector_stores[paper_id] = vectorstore
                paper_metadata[paper_id] = paper_info
                print("[SUCCESS] Processed direct PDF")
                return vectorstore, 'pdf'

    # Priority 1: Semantic Scholar PDF
    print("[STEP 1] Trying Semantic Scholar PDF...")
    s2_pdf_url = SemanticScholarService.get_paper_pdf_url(
        paper_url,
        paper_info.get('external_ids') or paper_info.get('externalIds'),
        title
    )

    if s2_pdf_url:
        pdf_content = download_pdf(s2_pdf_url)
        if pdf_content:
            text = extract_text_from_pdf(pdf_content)
            if text and len(text) > 500:
                vectorstore = create_vectorstore_from_text(text, paper_id, paper_info)
                vector_stores[paper_id] = vectorstore
                paper_metadata[paper_id] = paper_info
                print("[SUCCESS] Processed Semantic Scholar PDF")
                return vectorstore, 'pdf'

    print("[INFO] Semantic Scholar PDF not available")

    # Priority 2: arXiv PDF
    print("[STEP 2] Trying arXiv PDF...")
    arxiv_paper = search_arxiv_for_paper(title, authors)

    # Check external IDs for arXiv ID
    if not arxiv_paper:
        ex = paper_info.get('externalIds') or paper_info.get('external_ids') or {}
        arxiv_id = ex.get('ArXiv') or ex.get('ARXIV') or ex.get('arxiv')
        if arxiv_id:
            arxiv_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            arxiv_paper = {'pdf_url': arxiv_pdf_url}

    if arxiv_paper and arxiv_paper.get('pdf_url'):
        arxiv_pdf_url = arxiv_paper['pdf_url']
        pdf_content = ArxivService.download_pdf(arxiv_pdf_url)

        if pdf_content:
            text = extract_text_from_pdf(pdf_content)
            if text and len(text) > 500:
                vectorstore = create_vectorstore_from_text(text, paper_id, paper_info)
                vector_stores[paper_id] = vectorstore
                paper_metadata[paper_id] = paper_info
                print("[SUCCESS] Processed arXiv PDF")
                return vectorstore, 'pdf'

    print("[INFO] arXiv PDF not available")

    # Priority 3: Metadata only
    print("[STEP 3] Using metadata only (title + abstract)")
    if abstract:
        metadata_text = f"Title: {title}\n\nAbstract: {abstract}\n\nAuthors: {authors}"
        vectorstore = create_vectorstore_from_text(metadata_text, paper_id, paper_info)
        vector_stores[paper_id] = vectorstore
        paper_metadata[paper_id] = paper_info
        print("[SUCCESS] Using metadata only")
        return vectorstore, 'metadata'

    print("[WARN] Insufficient data to process paper")
    paper_metadata[paper_id] = paper_info
    save_metadata_to_disk(paper_id, paper_info)
    return None, 'no_source'


async def answer_question_with_rag(
    paper_id: str,
    question: str,
    paper_info: Dict = None
) -> Dict:
    """
    Answer question using RAG pipeline with Sentence Transformers + Gemini LLM
    Returns user-friendly, clear answers
    """
    try:
        # Get vectorstore from memory or disk
        vectorstore = get_or_load_vectorstore(paper_id)

        if not vectorstore:
            return {
                'answer': "I'm ready to help! Please make sure the paper is loaded first.",
                'source_type': 'error',
                'citation': ''
            }

        # Get paper metadata
        if not paper_info:
            paper_info = paper_metadata.get(paper_id) or load_metadata_from_disk(paper_id) or {}

        citation = extract_citation_info(paper_info)
        source_type = 'pdf'  # We'll determine this based on what we stored

        # Check if it's metadata-only by checking document count
        docs = vectorstore.similarity_search(question, k=1)
        if docs and len(docs[0].page_content) < 1000:
            source_type = 'metadata'

        # Retrieve relevant documents using similarity_search
        relevant_docs = vectorstore.similarity_search(question, k=5)  # Increased to 5 for better context

        if not relevant_docs:
            return {
                'answer': "I couldn't find specific information about this in the paper. Could you try rephrasing your question or asking about a different aspect?",
                'source_type': source_type,
                'citation': citation
            }

        # Create context from relevant documents
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # Improved prompt for user-friendly answers
        if source_type == 'pdf':
            prompt_template = f"""You are PaperLens, a helpful AI research assistant. Your goal is to provide clear, understandable answers based on the research paper.

CONTEXT FROM PAPER:
{{context}}

USER'S QUESTION:
{{question}}

INSTRUCTIONS:
1. Provide a clear, well-structured answer that a general reader can understand
2. Use simple language when possible, but maintain scientific accuracy
3. Structure your answer with:
   - A brief direct answer (1-2 sentences)
   - Key points or details (2-4 bullet points or short paragraphs)
   - Any important context or limitations
4. When referencing the paper, use this citation: {citation}
5. If the context doesn't fully answer the question, acknowledge this clearly
6. Keep the answer concise but comprehensive (aim for 150-300 words)
7. Use examples or analogies if they help explain complex concepts

Answer:"""
        else:
            # For metadata-only, be more careful
            prompt_template = f"""You are PaperLens, a helpful AI research assistant. You're answering based on the paper's abstract and title.

PAPER INFORMATION:
{{context}}

USER'S QUESTION:
{{question}}

INSTRUCTIONS:
1. Provide a helpful answer based on the available information
2. Be clear about what you can and cannot answer given the limited information
3. Use simple, understandable language
4. When referencing, use this citation: {citation}
5. Keep the answer concise (100-200 words)
6. If the question requires details not in the abstract, politely explain this

Answer:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        # Create the prompt with context and question
        formatted_prompt = PROMPT.format(context=context, question=question)
        
        # Call LLM directly
        response = await asyncio.to_thread(llm.invoke, formatted_prompt)
        answer = response.strip() if isinstance(response, str) else str(response).strip()

        # Calculate retrieval scores
        retrieval_scores = []
        for doc in relevant_docs:
            score = len(set(question.lower().split()) & set(doc.page_content.lower().split())) / max(len(question.split()), 1)
            retrieval_scores.append(score)

        # Calculate confidence (keep internal but don't return)
        confidence = ConfidenceScorer.calculate_confidence(
            source_type=source_type,
            retrieval_scores=retrieval_scores if retrieval_scores else None,
            answer_length=len(answer),
            question_length=len(question),
            chunks_used=len(relevant_docs)
        )

        return {
            'answer': answer,
            'source_type': source_type,  # Still tracked but not shown to user
            'citation': citation
        }

    except Exception as e:
        print(f"[ERROR] RAG pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'answer': "I encountered an error while processing your question. Please try again or rephrase your question.",
            'source_type': 'error',
            'citation': ''
        }

