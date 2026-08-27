"""
Generates a plain-language summary + recommendation for a report's test
results using Gemini (text-only call, same free API key as extraction).
"""

from pydantic import BaseModel, Field

from ocr.gemini_extractor import get_client, GEMINI_MODEL
from google.genai import types


class Insight(BaseModel):
    summary: str = Field(description="2-4 sentence plain-language summary of what the results show")
    recommendation: str = Field(description="2-4 sentence general, non-diagnostic suggestion, always including advice to consult a doctor")


INSIGHT_PROMPT_TEMPLATE = """
You are helping a patient understand their lab report in plain, simple
language. You are NOT a doctor and must not give a diagnosis.

Here are the test results (test name, value, unit, normal range, status):

{results_table}

Write:
1. summary: a short, plain-language explanation of what these results show,
   mentioning which values are outside the normal range and what that
   generally indicates in everyday terms.
2. recommendation: general, non-diagnostic next steps (e.g. lifestyle
   notes, when to consider follow-up), and explicitly recommend the
   patient discuss these results with their doctor.

Keep both fields concise and avoid alarming language.
"""


def _format_results(test_results) -> str:
    lines = []

    for row in test_results:
        lines.append(
            f"- {row['test_name']}: {row['value']} {row['unit']} "
            f"(normal: {row['reference_low']}-{row['reference_high']}) "
            f"[{row['status']}]"
        )

    return "\n".join(lines)


def generate_insight(test_results) -> tuple[str, str]:
    """
    test_results: iterable of sqlite Row / dict objects with keys
    test_name, value, unit, reference_low, reference_high, status

    Returns (summary, recommendation).
    """

    client = get_client()

    prompt = INSIGHT_PROMPT_TEMPLATE.format(
        results_table=_format_results(test_results)
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Insight,
            temperature=0.2,
        ),
    )

    parsed = getattr(response, "parsed", None)

    if parsed is None:
        parsed = Insight.model_validate_json(response.text)

    return parsed.summary, parsed.recommendation
