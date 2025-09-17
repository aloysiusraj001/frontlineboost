# app/api/routes/feedback.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging

from app.config.rubric_config import InterviewRubric
from app.utils.auth import api_key_auth
from app.models.schemas import FeedbackInput, FeedbackReport
from app.services.feedback_service import feedback_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/report", response_model=FeedbackReport)
async def generate_feedback_report(
    payload: FeedbackInput,
    auth=Depends(api_key_auth)
) -> FeedbackReport:
    """
    Generate comprehensive feedback report for an interview.
    
    Analyzes the interview transcript and provides:
    - Scores for each rubric category
    - Overall performance summary
    - Specific strengths and areas for improvement
    - Quote highlights demonstrating key points
    - Detailed rubric for reference
    """
    try:
        logger.info(f"Generating feedback for persona {payload.persona_id} "
                   f"with {len(payload.interview_turns)} turns")
        
        # Generate feedback
        report = await feedback_service.generate_feedback(payload)
        
        logger.info(f"Feedback generated successfully. Overall score: {report.overall_score}")
        
        return report
        
    except ValueError as e:
        logger.error(f"Validation error in feedback generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in feedback generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate feedback report"
        )

@router.get("/rubric")
async def get_scoring_rubric(
    auth=Depends(api_key_auth)
) -> Dict:
    """
    Get the complete scoring rubric used for evaluation.
    
    Returns the categories, weights, and performance level descriptions.
    """
    from app.config.rubric_config import InterviewRubric
    
    rubric_data = {
        "categories": [],
        "performance_levels": ["Exemplary", "Proficient", "Developing", "Needs Improvement"],
        "scoring_scale": {
            "min": 1,
            "max": 4
        }
    }
    
    for category in InterviewRubric.get_default_rubric():
        rubric_data["categories"].append({
            "id": category.id,
            "name": category.name,
            "weight": category.weight,
            "description": category.description,
            "anchors": {level.value: anchor for level, anchor in category.anchors.items()}
        })
    
    return rubric_data

@router.post("/report/export/{format}")
async def export_feedback_report(
    format: str,
    report: FeedbackReport,
    auth=Depends(api_key_auth)
) -> Dict:
    """
    Export feedback report in specified format.
    
    Supported formats: json, html, pdf (pdf requires additional setup)
    """
    if format not in ["json", "html", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}"
        )
    
    if format == "json":
        return report.dict()
    
    elif format == "html":
        # Generate HTML report
        from app.services.report_exporter import generate_html_report
        html_content = generate_html_report(report)
        return {"html": html_content}
    
    elif format == "pdf":
        # PDF generation would require additional dependencies
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF export not yet implemented"
        )

# Health check for feedback service
@router.get("/health")
async def feedback_health_check() -> Dict:
    """Check if feedback service is operational"""
    return {
        "service": "feedback",
        "status": "healthy",
        "rubric_categories": len(InterviewRubric.get_default_rubric()),
        "analysis_methods": ["rule-based", "llm", "hybrid"]
    }