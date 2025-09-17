// empathy-interview-frontend\src\adapters\feedback.js

const titleCase = (s) => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export function normalizeReport(report) {
  if (!report) return { categories: [], strengths: [], improvements: [], quotes: [], overall: {} };

  const categories = Object.values(report.scores || {}).map((s) => ({
    id: s.category_id,
    name: titleCase(s.category_id),
    score: Number(s.score || 0),
    level: s.level,
    weight: s.weight,
    description: s.description,
    evidence: s.evidence || [],
    suggestions: s.suggestions || [],
  }));

  return {
    categories,
    strengths: Array.isArray(report.strengths) ? report.strengths : [],
    improvements: Array.isArray(report.improvements) ? report.improvements : [],
    quotes: Array.isArray(report.quote_highlights) ? report.quote_highlights : [],
    overall: {
      score: report.overall_score,
      level: report.overall_level,
      summary: report.overall_summary,
      totalTurns: report.total_turns,
      durationSeconds: report.duration_seconds,
    },
  };
}