# app/services/feedback_service.py

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

from app.models.schemas import (
    FeedbackInput, FeedbackReport, CategoryScore, 
    PerformanceLevel, SpeakerRole, InterviewTurn
)
from app.config.rubric_config import InterviewRubric
from app.services.scoring_engine import ScoringEngine
from app.services.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)

CHITCHAT_PATTERNS = [
        r"\b(hello|hi|hey)\b",
        r"\b(can you hear me|am i audible|mic|microphone|testing|test|check)\b",
    ]

def _is_chitchat(text: str) -> bool:
        t = text.lower()
        return any(re.search(p, t) for p in CHITCHAT_PATTERNS)

class FeedbackService:
    """Main service for generating interview feedback reports"""
    
    def __init__(self):
        self.rubric = InterviewRubric()
        self.scoring_engine = ScoringEngine()
        self.llm_analyzer = LLMAnalyzer()
        self.edge_responses = InterviewRubric.get_edge_case_responses()
    
    async def generate_feedback(self, feedback_input: FeedbackInput) -> FeedbackReport:
        # Validate input
        validation_error = self._validate_interview(feedback_input)
        if validation_error:
            return self._create_error_report(validation_error, feedback_input)

        try:
            # Sort turns once for stable downstream calcs
            turns = sorted(
                feedback_input.interview_turns,
                key=lambda t: (
                    t.timestamp is None,           # None at the end
                    t.timestamp if t.timestamp is not None else float("inf"),
                    (t.turn_number or 0)
                ),
            )

            # Silence detection
            student_turns = [t for t in turns if t.speaker == SpeakerRole.STUDENT]
            silence_warning = self._check_for_silence(student_turns)

            # Duration (safe, monotonic)
            duration = None
            if turns[0].timestamp is not None and turns[-1].timestamp is not None:
                duration = max(0.0, turns[-1].timestamp - turns[0].timestamp)

            # Rule-based scoring
            scores = self.scoring_engine.score_interview(turns) or {}

            # Avoid empty dict explosions later
            if not scores:
                # minimal scaffold from rubric
                scores = {
                    cat.id: CategoryScore(
                        category_id=cat.id,
                        score=1,
                        level=PerformanceLevel.NEEDS_IMPROVEMENT,
                        weight=cat.weight,
                        description="Insufficient evidence to score",
                        evidence=[],
                        suggestions=[],
                    )
                    for cat in self.rubric.get_default_rubric()
                }

            overall_score = self._calculate_overall_score(scores)
            overall_level = self._score_to_level(overall_score)

            # LLM analysis (with fallbacks)
            try:
                summary = await self.llm_analyzer.generate_summary(turns, scores, overall_score)
                strengths, improvements = await self.llm_analyzer.extract_strengths_improvements(turns, scores)
                quotes = await self.llm_analyzer.extract_quotes(turns, scores)
            except Exception as e:
                logger.warning(f"LLM analysis failed, using fallbacks: {e}")
                summary = self._generate_fallback_summary(overall_score, scores)
                strengths, improvements = self._extract_fallback_feedback(scores)
                quotes = []

            # Bubble up the silence hint to the user
            if silence_warning:
                improvements = [silence_warning] + (improvements or [])

            # Rubric reference
            rubric_dict = {
                cat.id: [f"{level.value}: {anchor}" for level, anchor in cat.anchors.items()]
                for cat in self.rubric.get_default_rubric()
            }

            report = FeedbackReport(
                generated_at=datetime.utcnow(),
                persona_id=feedback_input.persona_id,
                total_turns=len(turns),
                duration_seconds=duration,
                scores=scores,
                overall_score=overall_score,
                overall_level=overall_level,
                overall_summary=summary,
                strengths=(strengths or [])[:5],
                improvements=(improvements or [])[:5],
                quote_highlights=(quotes or [])[:4],
                rubric=rubric_dict,
                analysis_method="hybrid",
                confidence_score=self._calculate_confidence(turns, scores),
            )
            return report

        except Exception as e:
            logger.error(f"Feedback generation failed: {e}", exc_info=True)
            raise


    def _validate_interview(self, feedback_input: FeedbackInput) -> Optional[str]:
        turns = feedback_input.interview_turns
        if not turns:
            return ("I didn't hear anything in this interview. Please ensure your microphone "
                    "is working and speak clearly.")

        student_turns = [t for t in turns if t.speaker == SpeakerRole.STUDENT]
        persona_turns = [t for t in turns if t.speaker == SpeakerRole.PERSONA]

        # keep very permissive “structure” checks
        if len(student_turns) < 3:
            return self.edge_responses["too_short"]
        if len(persona_turns) < 2:
            return self.edge_responses["one_sided"]

        # very light content checks (no hard keywords):
        contenty_students = [t for t in student_turns if t.text and len(t.text.strip()) > 3]
        total_chars = sum(len(t.text.strip()) for t in contenty_students)
        question_like = sum(1 for t in contenty_students if "?" in t.text)
        if total_chars < 60 or (question_like / max(1, len(contenty_students))) < 0.2:
            return self.edge_responses["off_topic"]

        return None
    
    
    def _check_for_silence(self, turns: List[InterviewTurn]) -> Optional[str]:
        if not turns or turns[0].timestamp is None:
            return None

        for i in range(1, len(turns)):
            if turns[i].timestamp is not None and turns[i - 1].timestamp is not None:
                gap = turns[i].timestamp - turns[i - 1].timestamp
                if gap > 30.0:
                    return ("There was a long pause in the interview. Please continue speaking "
                            "to maintain engagement.")
        return None
    
    def _calculate_overall_score(self, scores: Dict[str, CategoryScore]) -> float:
        """Calculate weighted overall score"""
        total_weighted = sum(score.score * score.weight for score in scores.values())
        total_weight = sum(score.weight for score in scores.values())
        return total_weighted / total_weight if total_weight > 0 else 0
    
    def _score_to_level(self, score: float) -> PerformanceLevel:
        """Convert numeric score to performance level"""
        if score >= 3.5:
            return PerformanceLevel.EXEMPLARY
        elif score >= 2.5:
            return PerformanceLevel.PROFICIENT
        elif score >= 1.5:
            return PerformanceLevel.DEVELOPING
        else:
            return PerformanceLevel.NEEDS_IMPROVEMENT
    
    def _calculate_confidence(self, turns: List[InterviewTurn], 
                            scores: Dict[str, CategoryScore]) -> float:
        """Calculate confidence in the assessment"""
        
        # Base confidence on amount of data
        base_confidence = min(len(turns) / 20, 1.0) * 0.5
        
        # Add confidence based on evidence found
        evidence_count = sum(len(s.evidence) for s in scores.values())
        evidence_confidence = min(evidence_count / 20, 1.0) * 0.5
        
        return base_confidence + evidence_confidence
    
    def _generate_fallback_summary(self, overall_score: float, scores: Dict[str, CategoryScore]) -> str:
        level_text = self._score_to_level(overall_score).value.lower()

        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1].score, reverse=True)
            strongest = sorted_scores[0][0].replace("_", " ")
            weakest = sorted_scores[-1][0].replace("_", " ")
            tail = f"You demonstrated particular strength in {strongest}, while {weakest} presents an opportunity for growth. "
        else:
            tail = ""

        summary = (
            f"Your interview performance is at a {level_text} level with an overall score of {overall_score:.1f}/4. "
            f"{tail}Review the detailed feedback below to continue improving your interviewing skills."
        )
        return summary

    
    def _extract_fallback_feedback(self, scores: Dict[str, CategoryScore]) -> tuple:
        """Extract strengths and improvements from scores"""
        
        strengths = []
        improvements = []
        
        for category_id, score in scores.items():
            # Add evidence as strengths for high scores
            if score.score >= 3:
                strengths.extend(score.evidence[:2])
            
            # Add suggestions as improvements
            if score.suggestions:
                improvements.extend(score.suggestions[:2])
        
        # Add generic items if needed
        if not strengths:
            strengths = ["Completed the interview", "Asked multiple questions"]
        
        if not improvements:
            improvements = ["Practice more open-ended questions", "Work on active listening"]
        
        return strengths, improvements
    
    def _create_error_report(self, error_message: str, 
                           feedback_input: FeedbackInput) -> FeedbackReport:
        """Create an error report with helpful guidance"""
        
        # Create minimal scores
        scores = {}
        for cat in self.rubric.get_default_rubric():
            scores[cat.id] = CategoryScore(
                category_id=cat.id,
                score=1,
                level=PerformanceLevel.NEEDS_IMPROVEMENT,
                weight=cat.weight,
                description="Unable to assess due to interview issues",
                evidence=[],
                suggestions=["Please conduct a proper interview"]
            )
        
        return FeedbackReport(
            generated_at=datetime.utcnow(),
            persona_id=feedback_input.persona_id,
            total_turns=len(feedback_input.interview_turns),
            duration_seconds=None,
            scores=scores,
            overall_score=1.0,
            overall_level=PerformanceLevel.NEEDS_IMPROVEMENT,
            overall_summary=error_message,
            strengths=[],
            improvements=["Conduct a complete interview with the persona",
                         "Ask at least 5-6 questions about their background",
                         "Listen to responses before asking follow-up questions"],
            quote_highlights=[],
            rubric={cat.id: [] for cat in self.rubric.get_default_rubric()},
            analysis_method="error",
            confidence_score=0.0
        )

# Singleton instance
feedback_service = FeedbackService()