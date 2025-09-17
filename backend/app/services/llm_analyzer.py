# app/services/llm_analyzer.py

import json
import logging
from typing import List, Dict, Optional, Tuple
from app.models.schemas import (
    InterviewTurn, QuoteHighlight, ChatMessage, 
    ChatRequest, SpeakerRole
)
from app.services.openrouter_service import openrouter_service
from app.config.rubric_config import InterviewRubric

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Use LLM for sophisticated interview analysis"""
    
    def __init__(self):
        self.rubric = InterviewRubric.get_default_rubric()
    
    async def extract_quotes(self, turns: List[InterviewTurn], 
                           scores: Dict[str, any]) -> List[QuoteHighlight]:
        """Extract meaningful quotes using LLM"""
        
        # Prepare transcript
        transcript = self._format_transcript(turns)
        
        # Identify categories needing quotes
        strong_categories = [cat_id for cat_id, score in scores.items() 
                           if score.score >= 3]
        weak_categories = [cat_id for cat_id, score in scores.items() 
                          if score.score < 3]
        
        prompt = f"""Analyze this interview transcript and extract specific quotes that demonstrate strengths and areas for improvement.

TRANSCRIPT:
{transcript}

STRONG CATEGORIES (score 3-4): {', '.join(strong_categories)}
WEAK CATEGORIES (score 1-2): {', '.join(weak_categories)}

Extract 2-4 quotes that best illustrate:
1. At least 1 quote showing excellent interviewing (from strong categories)
2. At least 1 quote showing areas for improvement (from weak categories)

For each quote, provide:
- The exact quote (keep it concise, under 50 words)
- The turn number where it appears
- Which category it relates to
- Whether it's positive or negative
- Brief explanation of why it's noteworthy

Format as JSON array with objects containing: quote, turn_number, category, is_positive, explanation"""
        
        try:
            request = ChatRequest(
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3
            )
            
            response = await openrouter_service.generate_text(request)
            
            # Parse LLM response
            quotes_data = self._parse_json_response(response.message)
            
            quotes = []
            for q in quotes_data:
                quotes.append(QuoteHighlight(
                    quote=q["quote"],
                    context=self._get_quote_context(turns, q["turn_number"]),
                    turn_number=q["turn_number"],
                    category=q["category"],
                    is_positive=q["is_positive"],
                    explanation=q["explanation"]
                ))
            
            return quotes
            
        except Exception as e:
            logger.error(f"LLM quote extraction failed: {e}")
            # Fallback to rule-based extraction
            return self._fallback_quote_extraction(turns, scores)
    
    async def generate_summary(self, turns: List[InterviewTurn], 
                             scores: Dict[str, any],
                             overall_score: float) -> str:
        """Generate personalized overall summary"""
        
        transcript_summary = self._create_transcript_summary(turns)
        score_summary = self._create_score_summary(scores)
        
        prompt = f"""Write a 2-3 sentence summary of this interview performance.

CONTEXT:
- Overall score: {overall_score}/4
- Number of exchanges: {len(turns)}
- Score breakdown: {score_summary}

Key observations:
{transcript_summary}

Write a constructive, encouraging summary that:
1. Acknowledges the overall performance level
2. Highlights 1-2 specific strengths
3. Suggests 1 key area for growth
4. Maintains a supportive, educational tone

Keep it concise and actionable."""
        
        try:
            request = ChatRequest(
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.7,
                max_tokens=150
            )
            
            response = await openrouter_service.generate_text(request)
            return response.message.strip()
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._fallback_summary(overall_score, scores)
    
    async def extract_strengths_improvements(self, turns: List[InterviewTurn],
                                           scores: Dict[str, any]) -> Tuple[List[str], List[str]]:
        """Extract specific strengths and improvement areas"""
        
        transcript = self._format_transcript(turns)
        score_details = self._format_score_details(scores)
        
        prompt = f"""Analyze this interview and provide specific, actionable feedback.

TRANSCRIPT:
{transcript}

SCORES AND EVIDENCE:
{score_details}

Based on the evidence, provide:

STRENGTHS (3-5 specific things the interviewer did well):
- Focus on concrete behaviors observed
- Be specific with examples when possible
- Highlight techniques that should be continued

IMPROVEMENTS (3-5 specific areas for growth):
- Provide actionable suggestions
- Focus on technique, not personality
- Suggest specific strategies or phrases to try

Format as two JSON arrays: "strengths" and "improvements" """
        
        try:
            request = ChatRequest(
                model="deepseek/deepseek-chat-v3.1:free",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=400
            )
            
            response = await openrouter_service.generate_text(request)
            result = self._parse_json_response(response.message)
            
            return result.get("strengths", []), result.get("improvements", [])
            
        except Exception as e:
            logger.error(f"LLM strength/improvement extraction failed: {e}")
            return self._fallback_strengths_improvements(scores)
    
    def _format_transcript(self, turns: List[InterviewTurn]) -> str:
        """Format transcript for LLM consumption"""
        lines = []
        for i, turn in enumerate(turns):
            speaker = "STUDENT" if turn.speaker == SpeakerRole.STUDENT else "PERSONA"
            lines.append(f"Turn {i+1} [{speaker}]: {turn.text}")
        return "\n".join(lines)
    
    def _create_transcript_summary(self, turns: List[InterviewTurn]) -> str:
        """Create a brief summary of transcript characteristics"""
        student_turns = [t for t in turns if t.speaker == SpeakerRole.STUDENT]
        
        total_questions = sum(1 for t in student_turns if "?" in t.text)
        avg_length = sum(len(t.text.split()) for t in student_turns) / len(student_turns) if student_turns else 0
        
        return f"""- Total questions asked: {total_questions}
- Average question length: {avg_length:.1f} words
- Interview duration: {len(turns)} turns"""
    
    def _create_score_summary(self, scores: Dict[str, any]) -> str:
        """Summarize scores for context"""
        items = []
        for cat_id, score in scores.items():
            items.append(f"{cat_id}: {score.level} ({score.score}/4)")
        return ", ".join(items)
    
    def _format_score_details(self, scores: Dict[str, any]) -> str:
        """Format detailed scores with evidence"""
        lines = []
        for cat_id, score in scores.items():
            lines.append(f"\n{cat_id.upper()}:")
            lines.append(f"Score: {score.score}/4 ({score.level})")
            if score.evidence:
                lines.append("Evidence: " + "; ".join(score.evidence))
            if score.suggestions:
                lines.append("Needs: " + "; ".join(score.suggestions))
        return "\n".join(lines)
    
    def _parse_json_response(self, response: str) -> any:
        """Safely parse JSON from LLM response"""
        # Try to extract JSON from response
        import re
        
        # Look for JSON arrays or objects
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON response")
        
        # Try parsing the whole response
        try:
            return json.loads(response)
        except:
            return {}
    
    def _get_quote_context(self, turns: List[InterviewTurn], turn_number: int) -> str:
        """Get surrounding context for a quote"""
        idx = turn_number - 1  # Convert to 0-indexed
        context_parts = []
        
        # Previous turn
        if idx > 0:
            context_parts.append(f"[Before] {turns[idx-1].text[:50]}...")
        
        # Next turn
        if idx < len(turns) - 1:
            context_parts.append(f"[After] {turns[idx+1].text[:50]}...")
        
        return " ".join(context_parts)
    
    def _fallback_quote_extraction(self, turns: List[InterviewTurn], 
                                  scores: Dict[str, any]) -> List[QuoteHighlight]:
        """Rule-based fallback for quote extraction"""
        quotes = []
        student_turns = [(i, t) for i, t in enumerate(turns) 
                        if t.speaker == SpeakerRole.STUDENT]
        
        # Find a good open-ended question
        for i, turn in student_turns:
            if any(phrase in turn.text.lower() for phrase in ["tell me", "describe", "how do you"]):
                quotes.append(QuoteHighlight(
                    quote=turn.text[:100],
                    context="",
                    turn_number=i + 1,
                    category="question_quality",
                    is_positive=True,
                    explanation="Good example of open-ended questioning"
                ))
                break
        
        # Find a weak spot
        for i, turn in student_turns:
            if len(turn.text.split()) < 5 and "?" in turn.text:
                quotes.append(QuoteHighlight(
                    quote=turn.text,
                    context="",
                    turn_number=i + 1,
                    category="question_quality",
                    is_positive=False,
                    explanation="Very brief question - could be expanded"
                ))
                break
        
        return quotes
    
    def _fallback_summary(self, overall_score: float, scores: Dict[str, any]) -> str:
        """Generate summary without LLM"""
        level = "excellent" if overall_score >= 3.5 else "good" if overall_score >= 2.5 else "developing"
        
        strong = [k for k, v in scores.items() if v.score >= 3]
        weak = [k for k, v in scores.items() if v.score < 3]
        
        summary = f"Your interviewing skills are at a {level} level overall. "
        
        if strong:
            summary += f"You show particular strength in {strong[0].replace('_', ' ')}. "
        
        if weak:
            summary += f"Focus on improving your {weak[0].replace('_', ' ')} for better results."
        
        return summary
    
    def _fallback_strengths_improvements(self, scores: Dict[str, any]) -> Tuple[List[str], List[str]]:
        """Extract strengths/improvements without LLM"""
        strengths = []
        improvements = []
        
        for cat_id, score in scores.items():
            if score.evidence:
                for e in score.evidence[:2]:  # Top 2 evidence items
                    if score.score >= 3:
                        strengths.append(e)
            
            if score.suggestions:
                for s in score.suggestions[:2]:  # Top 2 suggestions
                    improvements.append(s)
        
        return strengths[:5], improvements[:5]
