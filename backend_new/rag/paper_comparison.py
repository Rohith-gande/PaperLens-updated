"""Multi-paper comparison using RAG with Sentence Transformers"""
import asyncio
from typing import List, Dict
from langchain_google_genai import GoogleGenerativeAI
import os

from rag.rag_pipeline import vector_stores, paper_metadata
from utils.citation_utils import extract_citation_info
from utils.confidence_scorer import ConfidenceScorer

# Initialize Gemini LLM
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required. Please set it in your .env file.")

llm = GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.3)


async def compare_multiple_papers(
    paper_ids: List[str],
    papers_info: List[Dict],
    comparison_query: str
) -> Dict:
    """
    Compare multiple papers on a specific aspect using RAG

    Returns:
        {
            'comparison': str,
            'confidence': int,
            'sources_used': List[str],
            'papers_analyzed': List[Dict]
        }
    """
    try:
        if not paper_ids or len(paper_ids) < 2:
            return {
                'comparison': "Error: At least 2 papers required for comparison",
                'sources_used': [],
                'papers_analyzed': []
            }

        # Collect data from each paper
        paper_contexts = []
        papers_analyzed = []
        all_source_types = []
        all_retrieval_scores = []

        for i, paper_id in enumerate(paper_ids):
            vectorstore = vector_stores.get(paper_id)

            if not vectorstore:
                continue

            paper_info = papers_info[i] if i < len(papers_info) else paper_metadata.get(paper_id, {})
            citation = extract_citation_info(paper_info)

            # Determine source type
            test_docs = vectorstore.similarity_search("test", k=1)
            source_type = 'metadata' if test_docs and len(test_docs[0].page_content) < 1000 else 'pdf'

            # Retrieve relevant chunks for the comparison query
            relevant_docs = vectorstore.similarity_search(comparison_query, k=3)

            if relevant_docs:
                context = "\n".join([doc.page_content for doc in relevant_docs])
                scores = [0.8] * len(relevant_docs)  # Placeholder scores

                paper_contexts.append({
                    'paper_id': paper_id,
                    'title': paper_info.get('title', ''),
                    'citation': citation,
                    'source_type': source_type,
                    'context': context,
                    'retrieval_scores': scores
                })

                papers_analyzed.append({
                    'title': paper_info.get('title', ''),
                    'citation': citation,
                    'source_type': source_type
                })

                all_source_types.append(source_type)
                all_retrieval_scores.extend(scores)

        if len(paper_contexts) < 2:
            return {
                'comparison': "Error: Could not load enough papers for comparison. Please ensure papers are fetched first.",
                'sources_used': [],
                'papers_analyzed': []
            }

        # Build comparison prompt (removed source quality mentions)
        comparison_context = ""
        for i, pc in enumerate(paper_contexts, 1):
            comparison_context += f"\n{'='*60}\n"
            comparison_context += f"PAPER {i}: {pc['title']}\n"
            comparison_context += f"Citation: {pc['citation']}\n"
            comparison_context += f"\nRelevant Excerpts:\n{pc['context']}\n"

        prompt = f"""You are PaperLens, an AI research assistant. Compare and contrast the following research papers based on the user's query. Provide a clear, well-structured comparison that helps users understand the similarities and differences.

{comparison_context}

{'='*60}

Comparison Query: {comparison_query}

Instructions:
1. Provide a comprehensive yet clear comparison with:
   - An executive summary (2-3 sentences)
   - Key similarities and differences (use bullet points)
   - Methodological approaches (if relevant)
   - Main findings and conclusions
   - Strengths and limitations of each approach
   - Any contradictions or agreements

2. Use inline citations for each claim: {', '.join([pc['citation'] for pc in paper_contexts])}

3. Structure your comparison clearly with sections and headings

4. Use language that is accessible but maintains scientific accuracy

5. Keep the comparison comprehensive but readable (aim for 400-600 words)

6. Be objective and evidence-based

Comparison:"""

        # Call Gemini for synthesis
        response = await asyncio.to_thread(llm.invoke, prompt)
        comparison_text = response.strip()

        # Calculate confidence based on sources (keep internal but don't return)
        source_quality_order = ['pdf', 'metadata', 'gemini_reasoning']
        best_source = min(
            all_source_types,
            key=lambda s: source_quality_order.index(s) if s in source_quality_order else 99
        )

        confidence = ConfidenceScorer.calculate_confidence(
            source_type=best_source,
            retrieval_scores=all_retrieval_scores if all_retrieval_scores else None,
            answer_length=len(comparison_text),
            question_length=len(comparison_query),
            chunks_used=len(paper_contexts) * 3
        )

        # NO METADATA WARNING - removed for clean UX

        return {
            'comparison': comparison_text,
            'sources_used': list(set(all_source_types)),  # Internal tracking only
            'papers_analyzed': papers_analyzed,
            'papers_count': len(paper_contexts)
        }

    except Exception as e:
        print(f"[ERROR] Multi-paper comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'comparison': f"Error during comparison: {str(e)}",
            'sources_used': [],
            'papers_analyzed': []
        }

