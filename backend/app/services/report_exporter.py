# app/services/report_exporter.py

from app.models.schemas import FeedbackReport, PerformanceLevel
from typing import Dict
import html

def generate_html_report(report: FeedbackReport) -> str:
    """Generate HTML version of feedback report"""
    
    # CSS styles
    styles = """
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { color: #333; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .score-card { background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .score-badge { display: inline-block; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
        .exemplary { background: #4CAF50; color: white; }
        .proficient { background: #2196F3; color: white; }
        .developing { background: #FF9800; color: white; }
        .needs-improvement { background: #f44336; color: white; }
        .category { margin: 20px 0; padding: 15px; border-left: 4px solid #2196F3; background: #f9f9f9; }
        .evidence { color: #4CAF50; }
        .suggestion { color: #FF9800; }
        .quote { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 3px solid #666; font-style: italic; }
        .positive-quote { border-left-color: #4CAF50; }
        .negative-quote { border-left-color: #f44336; }
        ul { padding-left: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
    </style>
    """
    
    # Generate performance badge
    def get_badge_class(level: PerformanceLevel) -> str:
        return level.value.lower().replace(" ", "-")
    
    # Header section
    header = f"""
    <div class="header">
        <h1>Interview Feedback Report</h1>
        <p><strong>Generated:</strong> {report.generated_at.strftime('%B %d, %Y at %I:%M %p')}</p>
        <p><strong>Interview Duration:</strong> {report.total_turns} exchanges</p>
        <h2>Overall Performance: <span class="score-badge {get_badge_class(report.overall_level)}">{report.overall_level.value}</span></h2>
        <p><strong>Overall Score:</strong> {report.overall_score:.1f} / 4.0</p>
    </div>
    """
    
    # Summary section
    summary = f"""
    <div class="score-card">
        <h2>Summary</h2>
        <p>{html.escape(report.overall_summary)}</p>
    </div>
    """
    
    # Scores breakdown
    scores_html = "<h2>Detailed Scores</h2>"
    for cat_id, score in report.scores.items():
        cat_name = cat_id.replace("_", " ").title()
        scores_html += f"""
        <div class="category">
            <h3>{cat_name} - <span class="score-badge {get_badge_class(score.level)}">{score.level.value}</span></h3>
            <p><strong>Score:</strong> {score.score}/4 (Weight: {score.weight}%)</p>
            <p>{html.escape(score.description)}</p>
            """
        
        if score.evidence:
            scores_html += "<p class='evidence'><strong>What you did well:</strong></p><ul>"
            for e in score.evidence:
                scores_html += f"<li>{html.escape(e)}</li>"
            scores_html += "</ul>"
        
        if score.suggestions:
            scores_html += "<p class='suggestion'><strong>Areas for improvement:</strong></p><ul>"
            for s in score.suggestions:
                scores_html += f"<li>{html.escape(s)}</li>"
            scores_html += "</ul>"
        
        scores_html += "</div>"
    
    # Strengths and Improvements
    feedback_section = """
    <div class="grid">
        <div class="score-card">
            <h2>Key Strengths</h2>
            <ul>
    """
    for strength in report.strengths:
        feedback_section += f"<li>{html.escape(strength)}</li>"
    
    feedback_section += """
            </ul>
        </div>
        <div class="score-card">
            <h2>Areas for Growth</h2>
            <ul>
    """
    for improvement in report.improvements:
        feedback_section += f"<li>{html.escape(improvement)}</li>"
    
    feedback_section += """
            </ul>
        </div>
    </div>
    """
    
    # Quote highlights
    quotes_section = ""
    if report.quote_highlights:
        quotes_section = "<h2>Notable Moments</h2>"
        for quote in report.quote_highlights:
            quote_class = "positive-quote" if quote.is_positive else "negative-quote"
            quotes_section += f"""
            <div class="quote {quote_class}">
                <p>"{html.escape(quote.quote)}"</p>
                <p><small><strong>Turn {quote.turn_number}</strong> - {html.escape(quote.explanation)}</small></p>
            </div>
            """
    
    # Rubric reference (collapsed by default)
    rubric_section = """
    <details>
        <summary><h2 style="display: inline;">Scoring Rubric Reference</h2></summary>
        <div style="margin-top: 10px;">
    """
    
    for cat_id, levels in report.rubric.items():
        cat_name = cat_id.replace("_", " ").title()
        rubric_section += f"<h3>{cat_name}</h3><ul>"
        for level_desc in levels:
            rubric_section += f"<li>{html.escape(level_desc)}</li>"
        rubric_section += "</ul>"
    
    rubric_section += """
        </div>
    </details>
    """
    
    # Combine all sections
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interview Feedback Report</title>
        {styles}
    </head>
    <body>
        {header}
        {summary}
        {feedback_section}
        {quotes_section}
        {scores_html}
        {rubric_section}
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
            <p>Generated by Interview Feedback System | Confidence Score: {report.confidence_score:.1%}</p>
        </footer>
    </body>
    </html>
    """
    
    return html_content


def generate_pdf_report(report: FeedbackReport) -> bytes:
    """
    Generate PDF version of feedback report.
    
    Note: This requires additional dependencies like reportlab or weasyprint.
    Implementation left as placeholder.
    """
    # This would require:
    # pip install reportlab
    # or
    # pip install weasyprint
    
    raise NotImplementedError("PDF generation requires additional dependencies")


def generate_markdown_report(report: FeedbackReport) -> str:
    """Generate Markdown version of feedback report"""
    
    md = f"""# Interview Feedback Report

**Generated:** {report.generated_at.strftime('%B %d, %Y at %I:%M %p')}  
**Interview Duration:** {report.total_turns} exchanges  
**Overall Performance:** {report.overall_level.value}  
**Overall Score:** {report.overall_score:.1f} / 4.0

## Summary

{report.overall_summary}

## Key Strengths

"""
    
    for strength in report.strengths:
        md += f"- {strength}\n"
    
    md += "\n## Areas for Growth\n\n"
    
    for improvement in report.improvements:
        md += f"- {improvement}\n"
    
    md += "\n## Detailed Scores\n\n"
    
    for cat_id, score in report.scores.items():
        cat_name = cat_id.replace("_", " ").title()
        md += f"### {cat_name}\n\n"
        md += f"**Score:** {score.score}/4 ({score.level.value}) - Weight: {score.weight}%\n\n"
        md += f"{score.description}\n\n"
        
        if score.evidence:
            md += "**What you did well:**\n"
            for e in score.evidence:
                md += f"- {e}\n"
            md += "\n"
        
        if score.suggestions:
            md += "**Areas for improvement:**\n"
            for s in score.suggestions:
                md += f"- {s}\n"
            md += "\n"
    
    if report.quote_highlights:
        md += "## Notable Moments\n\n"
        for quote in report.quote_highlights:
            sentiment = "✓" if quote.is_positive else "✗"
            md += f"{sentiment} **Turn {quote.turn_number}:** \"{quote.quote}\"\n"
            md += f"   - {quote.explanation}\n\n"
    
    md += f"\n---\n\n*Confidence Score: {report.confidence_score:.1%}*\n"
    
    return md