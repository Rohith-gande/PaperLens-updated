"""Confidence scoring system for RAG answers"""
from typing import List
import numpy as np


class ConfidenceScorer:
    """Calculate confidence scores for RAG answers"""

    # Source quality weights
    SOURCE_WEIGHTS = {
        'pdf': 1.0,
        'metadata': 0.5,
        'gemini_reasoning': 0.3
    }

    @staticmethod
    def calculate_confidence(
        source_type: str,
        retrieval_scores: List[float] = None,
        answer_length: int = 0,
        question_length: int = 0,
        chunks_used: int = 0
    ) -> int:
        """Calculate overall confidence score (0-100%)"""

        # Base score from source quality
        source_score = ConfidenceScorer.SOURCE_WEIGHTS.get(source_type, 0.3) * 100

        # Retrieval quality score
        retrieval_score = 0
        if retrieval_scores and len(retrieval_scores) > 0:
            avg_score = np.mean(retrieval_scores)
            retrieval_score = min(avg_score * 100, 100)
        else:
            if source_type in ['metadata', 'gemini_reasoning']:
                retrieval_score = 50

        # Answer completeness score
        completeness_score = 0
        if answer_length > 0 and question_length > 0:
            ratio = answer_length / max(question_length, 1)
            if ratio >= 5 and ratio <= 30:
                completeness_score = 100
            elif ratio < 5:
                completeness_score = ratio * 20
            else:
                completeness_score = max(100 - (ratio - 30) * 2, 50)

        # Chunk usage score
        chunk_score = 0
        if chunks_used > 0:
            chunk_score = min(chunks_used * 20, 100)

        # Weighted combination
        if source_type == 'pdf':
            final_score = (
                source_score * 0.3 +
                retrieval_score * 0.4 +
                completeness_score * 0.2 +
                chunk_score * 0.1
            )
        elif source_type == 'metadata':
            final_score = (
                source_score * 0.4 +
                completeness_score * 0.4 +
                retrieval_score * 0.2
            )
        else:
            final_score = (
                source_score * 0.5 +
                completeness_score * 0.5
            )

        return int(max(0, min(final_score, 100)))

    @staticmethod
    def get_confidence_label(score: int) -> str:
        """Get human-readable confidence label"""
        if score >= 80:
            return "High Confidence"
        elif score >= 60:
            return "Medium-High Confidence"
        elif score >= 40:
            return "Medium Confidence"
        elif score >= 20:
            return "Low-Medium Confidence"
        else:
            return "Low Confidence"

    @staticmethod
    def should_show_disclaimer(score: int, source_type: str) -> bool:
        """Determine if a disclaimer should be shown"""
        if source_type == 'gemini_reasoning':
            return True
        if score < 40:
            return True
        return False

