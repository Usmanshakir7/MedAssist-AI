import os
from anthropic import Anthropic

# Reads the API key from the ANTHROPIC_API_KEY environment variable.
# Set it before launching the app, e.g.:
#   export ANTHROPIC_API_KEY="sk-ant-..."   (macOS/Linux)
#   setx ANTHROPIC_API_KEY "sk-ant-..."     (Windows)
_client = None


def get_client():
    global _client

    if _client is None:
        _client = Anthropic()

    return _client


MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a patient-facing medical report explainer inside a \
health tracking app called MedAssist AI. You are given a list of lab test \
results (name, value, unit, reference range, status).

Write a plain-language, reassuring but accurate explanation for a general \
audience with no medical background. For each abnormal (Low/High) result, \
briefly note what the test measures and why a value outside range can \
happen, without diagnosing any condition. For normal results, keep it brief.

You are NOT a doctor and must not diagnose, prescribe, or tell the person \
to start/stop any medication. Always close with a short recommendation \
section suggesting they discuss these results with a healthcare provider, \
especially for anything abnormal.

Respond in EXACTLY this format, with no extra commentary:

SUMMARY:
<a few short paragraphs explaining the results in plain language>

RECOMMENDATION:
<2-4 short bullet points with practical next steps / questions for a doctor>
"""


def _format_results(test_results):

    lines = []

    for r in test_results:

        value = r["value"] if r["value"] is not None else "N/A"
        unit = r["unit"] or ""
        low = r["reference_low"]
        high = r["reference_high"]
        ref = f"{low}-{high}" if low is not None and high is not None else "N/A"

        lines.append(
            f"- {r['test_name']}: {value} {unit} "
            f"(reference range: {ref}, status: {r['status']})"
        )

    return "\n".join(lines)


def generate_insights(test_results):
    """
    test_results: list of sqlite3.Row / dicts with keys
    test_name, value, unit, reference_low, reference_high, status
    (this is exactly what get_test_results_by_report returns)

    Returns (summary, recommendation) as plain strings.
    Raises whatever exception the API call raises so the caller
    (the Streamlit view) can show it to the user.
    """

    report_text = _format_results(test_results)

    client = get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Lab results:\n{report_text}"}
        ],
    )

    full_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    summary = full_text
    recommendation = ""

    if "RECOMMENDATION:" in full_text:
        parts = full_text.split("RECOMMENDATION:", 1)
        summary = parts[0].replace("SUMMARY:", "").strip()
        recommendation = parts[1].strip()
    else:
        summary = full_text.replace("SUMMARY:", "").strip()

    return summary, recommendation
