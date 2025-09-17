# app/services/scoring_engine.py

import re
import logging
from typing import List, Dict, Tuple, Optional
from collections import Counter
from app.models.schemas import (
    InterviewTurn, CategoryScore, PerformanceLevel, 
    SpeakerRole, QuoteHighlight
)
from app.config.rubric_config import InterviewRubric

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Hybrid scoring engine using rules and patterns"""
    
    def __init__(self):
        self.rubric = {cat.id: cat for cat in InterviewRubric.get_default_rubric()}
        self.thresholds = InterviewRubric.get_score_thresholds()["default"]
    
    def _handle_no_audio_response(self, turns: List[InterviewTurn]) -> str:
        """Handle cases where no meaningful audio was captured"""
        student_turns = [t for t in turns if t.speaker == SpeakerRole.STUDENT]
        
        # Check for blank/empty transcripts
        if not student_turns or all(len(t.text.strip()) < 3 for t in student_turns):
            return "I didn't hear anything. Please ensure your microphone is working and try speaking clearly."
        
        # Check for irrelevant chatter
        interview_keywords = ["name", "background", "experience", "tell", "describe", "work", "what", "how", "why"]
        all_text = " ".join(t.text.lower() for t in student_turns)
        
        if not any(keyword in all_text for keyword in interview_keywords):
            return "I don't understand your question. Please ask me about my background, experience, or related topics."
        
        return None

    def score_interview(self, turns: List[InterviewTurn]) -> Dict[str, CategoryScore]:
        """Score all rubric categories"""
        student_turns = [t for t in turns if t.speaker == SpeakerRole.STUDENT]
        
        if not student_turns:
            raise ValueError("No student turns found in transcript")
        
        scores = {}
        for category_id, category in self.rubric.items():
            score, evidence, suggestions = self._score_category(
                category_id, student_turns, turns
            )
            level = self._score_to_level(score)
            
            scores[category_id] = CategoryScore(
                category_id=category_id,
                score=self._percentage_to_rubric_score(score),
                level=level,
                weight=category.weight,
                description=category.anchors[level],
                evidence=evidence,
                suggestions=suggestions
            )
        
        return scores
    
    def _score_category(self, category_id: str, student_turns: List[InterviewTurn], 
                       all_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score a specific category with evidence"""
        
        if category_id == "introduction_rapport":
            return self._score_introduction(student_turns, all_turns)
        elif category_id == "question_quality":
            return self._score_question_quality(student_turns)
        elif category_id == "active_listening":
            return self._score_active_listening(student_turns, all_turns)
        elif category_id == "question_sequence":
            return self._score_sequence(student_turns)
        elif category_id == "communication":
            return self._score_communication(student_turns)
        elif category_id == "respect_comfort":
            return self._score_respect(student_turns)
        elif category_id == "wrapup_closure":
            return self._score_wrapup(student_turns, all_turns)
        else:
            return 50, [], ["Category not implemented"]
    
    def _score_introduction(self, student_turns: List[InterviewTurn], 
                           all_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score introduction and rapport building"""
        score = 50  # Base score
        evidence = []
        suggestions = []
        
        if not student_turns:
            return 0, ["No introduction found"], ["Start with a proper introduction"]
        
        first_turn = student_turns[0].text.lower()
        
        # Check for greeting
        greetings = ["hello", "hi", "good morning", "good afternoon", "welcome"]
        if any(g in first_turn for g in greetings):
            score += 15
            evidence.append("Includes proper greeting")
        else:
            suggestions.append("Start with a warm greeting")
        
        # Check for introduction
        if "my name" in first_turn or "i'm" in first_turn:
            score += 10
            evidence.append("Introduces themselves")
        else:
            suggestions.append("Introduce yourself by name")
        
        # Check for purpose statement
        purpose_words = ["interview", "ask", "questions", "talk", "discuss", "learn"]
        if any(w in first_turn for w in purpose_words):
            score += 15
            evidence.append("Explains interview purpose")
        else:
            suggestions.append("Clearly state the purpose of the interview")
        
        # Check for comfort/permission
        comfort_words = ["comfortable", "okay", "ready", "questions before"]
        if any(w in first_turn for w in comfort_words):
            score += 10
            evidence.append("Checks interviewee comfort")
        else:
            suggestions.append("Ask if the interviewee is comfortable proceeding")
        
        return min(score, 100), evidence, suggestions
    
    def _score_question_quality(self, student_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score the quality of questions asked"""
        score = 0
        evidence = []
        suggestions = []
        
        open_ended_count = 0
        closed_ended_count = 0
        leading_count = 0
        
        open_patterns = [
            r"^(tell me|describe|explain|how|what|why|could you)",
            r"(tell me|describe|explain) (about|your|the)",
            r"(thoughts|feelings|experience|opinion) (on|about)",
            r"elaborate|expand|more detail"
        ]
        
        closed_patterns = [
            r"^(is|are|do|does|did|can|will|have|has|were|was)",
            r"(yes or no|correct|right|true)"
        ]
        
        leading_patterns = [
            r"don't you think",
            r"wouldn't you say",
            r"isn't it true",
            r"surely",
            r"obviously"
        ]
        
        for turn in student_turns:
            text = turn.text.lower().strip()
            
            # Skip very short utterances
            if len(text.split()) < 3:
                continue
            
            is_open = any(re.search(p, text) for p in open_patterns)
            is_closed = any(re.search(p, text) for p in closed_patterns)
            is_leading = any(re.search(p, text) for p in leading_patterns)
            
            if is_leading:
                leading_count += 1
            elif is_open:
                open_ended_count += 1
            elif is_closed:
                closed_ended_count += 1
        
        total_questions = open_ended_count + closed_ended_count + leading_count
        
        if total_questions > 0:
            open_ratio = open_ended_count / total_questions
            score = open_ratio * 80  # Base on open-ended ratio
            
            if open_ratio > 0.7:
                evidence.append(f"Excellent use of open-ended questions ({open_ended_count}/{total_questions})")
            elif open_ratio > 0.5:
                evidence.append(f"Good mix of question types ({open_ended_count} open-ended)")
            else:
                suggestions.append("Use more open-ended questions starting with 'How', 'What', 'Why'")
            
            if leading_count > 0:
                score -= leading_count * 5
                suggestions.append(f"Avoid leading questions ({leading_count} found)")
            
            # Bonus for probing
            probing_words = ["more", "elaborate", "example", "specifically", "detail"]
            probing_count = sum(1 for t in student_turns if any(w in t.text.lower() for w in probing_words))
            if probing_count > 2:
                score += 20
                evidence.append(f"Good use of probing questions ({probing_count} instances)")
        
        return min(max(score, 0), 100), evidence, suggestions
    
    def _score_active_listening(self, student_turns: List[InterviewTurn], 
                               all_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score active listening and follow-ups"""
        score = 50
        evidence = []
        suggestions = []
        
        # Check for acknowledgments
        ack_patterns = ["i see", "i understand", "that's interesting", "thank you for sharing"]
        ack_count = sum(1 for t in student_turns if any(p in t.text.lower() for p in ack_patterns))
        
        if ack_count > 2:
            score += 20
            evidence.append(f"Shows acknowledgment ({ack_count} times)")
        elif ack_count == 0:
            suggestions.append("Acknowledge what the interviewee shares")
        
        # Check for references to previous answers
        reference_patterns = ["you mentioned", "earlier you said", "going back to", "you talked about"]
        ref_count = sum(1 for t in student_turns if any(p in t.text.lower() for p in reference_patterns))
        
        if ref_count > 0:
            score += 30
            evidence.append(f"References previous answers ({ref_count} times)")
        else:
            suggestions.append("Reference earlier responses to show you're listening")
        
        return min(score, 100), evidence, suggestions
    
    def _score_sequence(self, student_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score the logical sequence of questions"""
        score = 70  # Base score
        evidence = []
        suggestions = []
        
        # Check for transition phrases
        transitions = ["moving on", "next", "another", "now", "let's talk about"]
        transition_count = sum(1 for t in student_turns if any(tr in t.text.lower() for tr in transitions))
        
        if transition_count > 2:
            score += 20
            evidence.append(f"Good use of transitions ({transition_count} found)")
        elif transition_count == 0:
            score -= 20
            suggestions.append("Use transition phrases between topics")
        
        # Simple check for funnel technique (questions getting more specific)
        question_lengths = [len(t.text.split()) for t in student_turns if "?" in t.text]
        if len(question_lengths) > 3:
            # Check if questions tend to get longer (more specific) over time
            first_half_avg = sum(question_lengths[:len(question_lengths)//2]) / (len(question_lengths)//2)
            second_half_avg = sum(question_lengths[len(question_lengths)//2:]) / (len(question_lengths) - len(question_lengths)//2)
            
            if second_half_avg > first_half_avg * 1.2:
                score += 10
                evidence.append("Questions become more detailed over time")
        
        return min(score, 100), evidence, suggestions
    
    def _score_communication(self, student_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score communication clarity and confidence"""
        score = 80  # Start high, deduct for issues
        evidence = []
        suggestions = []
        
        # Count filler words
        filler_words = ["um", "uh", "like", "you know", "basically", "actually", "literally"]
        total_words = sum(len(t.text.split()) for t in student_turns)
        filler_count = sum(t.text.lower().count(f) for t in student_turns for f in filler_words)
        
        filler_ratio = filler_count / max(total_words, 1)
        
        if filler_ratio < 0.02:
            evidence.append("Minimal filler words")
        elif filler_ratio < 0.05:
            score -= 10
            evidence.append("Some filler words present")
        else:
            score -= 30
            suggestions.append(f"Reduce filler words ({filler_count} found)")
        
        # Check for complete sentences
        incomplete_count = sum(1 for t in student_turns if t.text.strip().endswith("...") or t.text.count("...") > 0)
        if incomplete_count > 2:
            score -= 20
            suggestions.append("Complete your thoughts before moving on")
        
        return max(score, 0), evidence, suggestions
    
    def _score_respect(self, student_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score respect and comfort checking"""
        score = 60
        evidence = []
        suggestions = []
        
        # Check for permission/comfort language
        comfort_phrases = ["comfortable", "okay if", "happy to", "prefer", "take your time", "no pressure"]
        comfort_count = sum(1 for t in student_turns if any(p in t.text.lower() for p in comfort_phrases))
        
        if comfort_count > 1:
            score += 30
            evidence.append(f"Checks comfort level ({comfort_count} times)")
        elif comfort_count == 1:
            score += 15
            evidence.append("Some comfort checking")
        else:
            suggestions.append("Check if interviewee is comfortable with questions")
        
        # Check for polite language
        polite_words = ["please", "thank you", "appreciate", "would you mind"]
        polite_count = sum(1 for t in student_turns if any(p in t.text.lower() for p in polite_words))
        
        if polite_count > 3:
            score += 10
            evidence.append("Consistently polite language")
        
        return min(score, 100), evidence, suggestions
    
    def _score_wrapup(self, student_turns: List[InterviewTurn], 
                     all_turns: List[InterviewTurn]) -> Tuple[float, List[str], List[str]]:
        """Score the interview closing"""
        score = 0
        evidence = []
        suggestions = []
        
        if len(student_turns) < 2:
            return 0, ["No proper closing found"], ["End with thanks and final thoughts invitation"]
        
        last_turns = " ".join(t.text.lower() for t in student_turns[-2:])
        
        # Check for thanks
        if "thank" in last_turns:
            score += 40
            evidence.append("Thanks the interviewee")
        else:
            suggestions.append("Always thank the interviewee for their time")
        
        # Check for final thoughts invitation
        final_phrases = ["anything else", "final thoughts", "add anything", "missed anything", "other questions"]
        if any(p in last_turns for p in final_phrases):
            score += 30
            evidence.append("Invites final thoughts")
        else:
            suggestions.append("Ask if they have anything else to add")
        
        # Check for summary or next steps
        if "summary" in last_turns or "next steps" in last_turns or "follow up" in last_turns:
            score += 30
            evidence.append("Mentions next steps or summary")
        
        return min(score, 100), evidence, suggestions
    
    def _score_to_level(self, score: float) -> PerformanceLevel:
        """Convert percentage score to performance level"""
        for level, range_obj in self.thresholds.items():
            if int(score) in range_obj:
                return level
        return PerformanceLevel.NEEDS_IMPROVEMENT
    
    def _percentage_to_rubric_score(self, percentage: float) -> int:
        """Convert percentage to 1-4 rubric score"""
        if percentage >= 90:
            return 4
        elif percentage >= 70:
            return 3
        elif percentage >= 50:
            return 2
        else:
            return 1