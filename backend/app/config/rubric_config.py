# app/config/rubric_config.py

from app.models.schemas import RubricCategory, PerformanceLevel
from typing import Dict, List

class InterviewRubric:
    """Centralized rubric configuration for interview assessment"""
    
    @staticmethod
    def get_default_rubric() -> List[RubricCategory]:
        return [
            RubricCategory(
                id="introduction_rapport",
                name="Introduction & Rapport",
                weight=15,
                description="Opening, clarity, professionalism, ease/comfort for interviewee",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Professional, clear, and friendly opening that immediately puts interviewee at ease. Sets clear expectations and builds strong rapport.",
                    PerformanceLevel.PROFICIENT: "Polite and professional opening. Sets expectations and builds some comfort with the interviewee.",
                    PerformanceLevel.DEVELOPING: "Somewhat rushed or unclear introduction. Minimal rapport building attempted.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "Abrupt or impersonal introduction. Interviewee appears uneasy or confused about the purpose."
                },
                keywords=["hello", "introduce", "thank you for", "purpose", "appreciate", "comfortable", "questions"]
            ),
            
            RubricCategory(
                id="question_quality",
                name="Question Quality",
                weight=20,
                description="Open-endedness, neutrality, adaptability, probing depth",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Consistently asks open-ended, neutral, and unbiased questions. Adapts questions based on responses and probes deeply for rich insights.",
                    PerformanceLevel.PROFICIENT: "Most questions are open-ended and neutral. Shows some ability to probe when prompted by responses.",
                    PerformanceLevel.DEVELOPING: "Mix of open and closed questions. Some leading questions present. Misses opportunities for deeper exploration.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "Mostly yes/no or leading questions. Lacks depth and fails to explore interesting responses."
                },
                keywords=["tell me", "describe", "explain", "how", "what", "why", "could you", "elaborate", "more about"]
            ),
            
            RubricCategory(
                id="active_listening",
                name="Active Listening & Follow-ups",
                weight=20,
                description="Attentive listening, follow-ups, empathy",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Demonstrates exceptional listening through relevant follow-ups, clarifying questions, and empathetic responses. Never interrupts.",
                    PerformanceLevel.PROFICIENT: "Shows good listening skills with occasional follow-up questions. Rarely interrupts.",
                    PerformanceLevel.DEVELOPING: "Some evidence of listening but misses cues for deeper exploration. Occasional interruptions.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "Frequently interrupts or dominates conversation. Fails to follow up on important points."
                },
                keywords=["I see", "understand", "that must", "sounds like", "clarify", "you mentioned", "earlier you said"]
            ),
            
            RubricCategory(
                id="question_sequence",
                name="Question Sequence (Funnel)",
                weight=15,
                description="Logical flow, smooth transitions, broad-to-specific",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Perfect funnel technique - moves smoothly from general to specific. Transitions are seamless and logical.",
                    PerformanceLevel.PROFICIENT: "Generally logical flow with minor jumps. Most transitions are smooth.",
                    PerformanceLevel.DEVELOPING: "Some illogical jumps in topics. Transitions can be abrupt or unclear.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "No clear sequence. Questions appear random or repetitive."
                },
                keywords=["moving on", "next", "related to", "building on", "let's shift", "another area"]
            ),
            
            RubricCategory(
                id="communication",
                name="Communication",
                weight=10,
                description="Clarity, confidence, engagement",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Clear, confident, and engaging communication. No filler words or awkward pauses. Varied tone maintains interest.",
                    PerformanceLevel.PROFICIENT: "Generally clear communication with occasional lapses. Some filler words but maintains professionalism.",
                    PerformanceLevel.DEVELOPING: "Inconsistent clarity. Noticeable filler words or awkward pauses. Monotone delivery.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "Unclear or mumbled speech. Excessive filler words. Lacks confidence."
                },
                keywords=["um", "uh", "like", "you know", "basically", "actually"]  # Negative indicators
            ),
            
            RubricCategory(
                id="respect_comfort",
                name="Respect & Comfort",
                weight=10,
                description="Respect, consent, comfort, adaptability",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Consistently ensures interviewee comfort. Asks for consent, checks in regularly, adapts approach based on responses.",
                    PerformanceLevel.PROFICIENT: "Generally respectful and polite. Checks comfort at least once during interview.",
                    PerformanceLevel.DEVELOPING: "Basic politeness but misses signals of discomfort. Rarely checks in with interviewee.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "Disregards comfort. Pushes through despite signs of unease or reluctance."
                },
                keywords=["comfortable", "okay to ask", "take your time", "no pressure", "skip", "prefer not"]
            ),
            
            RubricCategory(
                id="wrapup_closure",
                name="Wrap-up & Closure",
                weight=10,
                description="Graceful closing, thanks, final input invitation",
                anchors={
                    PerformanceLevel.EXEMPLARY: "Graceful closing that thanks participant, summarizes key points, and invites final thoughts. Leaves positive impression.",
                    PerformanceLevel.PROFICIENT: "Appropriate ending with thanks. Some attempt to invite final input.",
                    PerformanceLevel.DEVELOPING: "Abrupt or weak closing. Misses opportunity for final input.",
                    PerformanceLevel.NEEDS_IMPROVEMENT: "Ends suddenly without thanks or closure. Leaves interviewee confused."
                },
                keywords=["thank you", "appreciate", "final thoughts", "anything else", "add", "covered everything", "time"]
            )
        ]
    
    @staticmethod
    def get_score_thresholds() -> Dict[str, Dict[PerformanceLevel, range]]:
        """Define score ranges for each performance level"""
        return {
            "default": {
                PerformanceLevel.EXEMPLARY: range(90, 101),  # 90-100%
                PerformanceLevel.PROFICIENT: range(70, 90),  # 70-89%
                PerformanceLevel.DEVELOPING: range(50, 70),  # 50-69%
                PerformanceLevel.NEEDS_IMPROVEMENT: range(0, 50)  # 0-49%
            }
        }
    
    @staticmethod
    def get_edge_case_responses() -> Dict[str, str]:
        """Standard responses for edge cases"""
        return {
            "empty_transcript": "I didn't hear anything in this interview. Please ensure your microphone is working and try again.",
            "too_short": "This interview appears too brief for meaningful assessment. Please conduct a longer interview with at least 5-6 exchanges.",
            "off_topic": "The conversation seems to have gone off-topic. Please focus on interviewing the persona about their background and experiences.",
            "one_sided": "This appears to be a one-sided conversation. Remember to ask questions and allow the interviewee to respond.",
            "technical_issue": "There seems to be a technical issue with the recording. Please check your setup and try again."
        }