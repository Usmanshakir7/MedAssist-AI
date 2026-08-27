"""
Validates and normalizes the structured JSON coming back from Gemini
before it gets written to SQLite.

Even though Gemini's response is schema-constrained, it can still return
things like a missing status or a range where low > high, so we re-derive
what we can with plain math instead of trusting the model blindly.
"""


def _compute_status(value, low, high):
    """
    Recompute status from the numbers instead of trusting the model's
    own status field. If we don't have enough info, mark it Unknown so
    it's obvious in the UI rather than silently wrong.
    """

    if value is None or low is None or high is None:
        return "Unknown"

    if low > high:
        low, high = high, low

    if value < low:
        return "Low"

    if value > high:
        return "High"

    return "Normal"


def validate_and_normalize(tests: list[dict]) -> list[dict]:
    """
    Takes the raw list of test dicts from ExtractedReport and returns a
    cleaned list ready for save_test_results(). Rows with no test_name
    are dropped; rows with no numeric value are kept (status Unknown)
    since the user may still want to see/edit them.
    """

    cleaned = []

    for row in tests:

        test_name = (row.get("test_name") or "").strip()

        if not test_name:
            continue

        value = row.get("value")
        unit = (row.get("unit") or "").strip()
        low = row.get("reference_low")
        high = row.get("reference_high")

        if low is not None and high is not None and low > high:
            low, high = high, low

        status = _compute_status(value, low, high)

        cleaned.append({
            "test_name": test_name,
            "value": value,
            "unit": unit,
            "reference_low": low,
            "reference_high": high,
            "status": status,
        })

    return cleaned
