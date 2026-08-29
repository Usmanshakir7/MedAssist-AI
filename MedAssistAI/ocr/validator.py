def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_status(value, low, high):
    value = _number(value)
    low = _number(low)
    high = _number(high)
    if value is None or low is None or high is None:
        return "Unknown"
    if low > high:
        low, high = high, low
    if value < low:
        return "Low"
    if value > high:
        return "High"
    return "Normal"


def validate_and_normalize(tests):
    cleaned = []
    for row in tests or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("test_name") or "").strip()
        if not name:
            continue
        value = _number(row.get("value"))
        low = _number(row.get("reference_low"))
        high = _number(row.get("reference_high"))
        if low is not None and high is not None and low > high:
            low, high = high, low
        cleaned.append({
            "test_name": name,
            "value": value,
            "unit": str(row.get("unit") or "").strip(),
            "reference_low": low,
            "reference_high": high,
            "status": _compute_status(value, low, high),
        })
    return cleaned
