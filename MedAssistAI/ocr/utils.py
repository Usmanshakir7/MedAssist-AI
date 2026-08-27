import re


def get_position(box):
    """
    Get center X and Y from EasyOCR bounding box.
    """

    x_values = [float(point[0]) for point in box]
    y_values = [float(point[1]) for point in box]

    x = sum(x_values) / len(x_values)
    y = sum(y_values) / len(y_values)

    return x, y


def clean_text(text):
    """
    Basic OCR text cleaning.
    """

    if text is None:
        return ""

    text = str(text).strip()

    text = text.replace("—", "-")
    text = text.replace("–", "-")

    return text


def normalize_number_text(text):
    """
    Correct common OCR mistakes in numeric values.

    IMPORTANT:
    We do NOT globally replace I/O because that can
    damage normal medical text.
    """

    text = clean_text(text)

    # Common OCR mistakes around numbers
    replacements = {
        "O": "0",
        "o": "0",
        "I": "1",
        "l": "1",
        "@": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def extract_numbers(text):
    """
    Return all numbers found in text.
    """

    text = normalize_number_text(text)

    matches = re.findall(
        r"\d+(?:\.\d+)?",
        text
    )

    return [float(x) for x in matches]


def extract_reference_range(text):
    """
    Extract a reference range.

    Examples:
        13.0-17.0
        40-50
        80-100
        150-400
    """

    text = normalize_number_text(text)

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)",
        text
    )

    if not match:
        return None, None

    low = float(match.group(1))
    high = float(match.group(2))

    if high < low:
        return None, None

    return low, high


def detect_unit(text):
    """
    Detect common CBC units.
    """

    lower = clean_text(text).lower()

    if "%" in lower:
        return "%"

    if "pg" in lower:
        return "pg"

    if "gm/dl" in lower:
        return "g/dL"

    if "g/dl" in lower:
        return "g/dL"

    if "fl" in lower:
        return "fL"

    return ""


def is_reference_range(text):
    """
    Check whether OCR text looks like a reference range.
    """

    low, high = extract_reference_range(text)

    return low is not None and high is not None


def extract_single_number(text):
    """
    Extract one numeric value.

    Reference ranges are ignored.
    """

    if is_reference_range(text):
        return None

    numbers = extract_numbers(text)

    if not numbers:
        return None

    return numbers[0]