from .utils import (
    get_position,
    clean_text,
    extract_single_number,
    extract_reference_range,
    detect_unit,
)


CBC_TESTS = {
    "HB": "Hemoglobin",
    "HEMOGLOBIN": "Hemoglobin",

    "RBC": "RBC",

    "HCT": "HCT",
    "HEMATOCRIT": "HCT",

    "MCV": "MCV",
    "MCH": "MCH",
    "MCHC": "MCHC",

    "WBC": "WBC",
    "WHITEBLOODCELL": "WBC",

    "PLATELETS": "Platelets",
    "PLATELET": "Platelets",

    "NEUTROPHILS": "Neutrophils",
    "NEUTROPHIL": "Neutrophils",

    "LYMPHOCYTES": "Lymphocytes",
    "LYMPHOCYTE": "Lymphocytes",

    "MONOCYTES": "Monocytes",
    "MONOCYTE": "Monocytes",

    "EOSINOPHILS": "Eosinophils",
    "EOSINOPHIL": "Eosinophils",

    "BASOPHILS": "Basophils",
    "BASOPHIL": "Basophils",
}


def normalize_test_name(text):
    """
    Convert OCR test text to standard CBC name.
    """

    text = clean_text(text).upper()

    # Remove spaces and common OCR symbols
    text = text.replace(" ", "")
    text = text.replace("_", "")
    text = text.replace("%", "")

    # OCR-specific corrections
    corrections = {
        "NEUTROPHILS%U": "NEUTROPHILS",
        "LYMPHOCYTES%U": "LYMPHOCYTES",
        "LYMPHOCYTES%": "LYMPHOCYTES",
        "EOSINOPHILS%U": "EOSINOPHILS",
        "BASOPHILS%U": "BASOPHILS",
        "BASOPHILS": "BASOPHILS",
        "BASOPHILS": "BASOPHILS",
    }

    if text in corrections:
        text = corrections[text]

    return CBC_TESTS.get(text)


def prepare_items(ocr_results):
    """
    Convert raw EasyOCR output into usable items.
    """

    items = []

    for item in ocr_results:

        text = clean_text(item.get("text", ""))

        if not text:
            continue

        box = item.get("box")

        if not box:
            continue

        x, y = get_position(box)

        confidence = float(
            item.get("confidence", 0)
        )

        items.append({
            "text": text,
            "x": x,
            "y": y,
            "confidence": confidence
        })

    return items


def find_test_items(items):
    """
    Find all CBC test labels.
    """

    tests = []

    for item in items:

        test_name = normalize_test_name(
            item["text"]
        )

        if test_name:

            tests.append({
                "test_name": test_name,
                "x": item["x"],
                "y": item["y"],
                "confidence": item["confidence"]
            })

    return tests


def find_closest_item(
    items,
    test_y,
    min_x,
    max_x,
    max_y_distance=35
):
    """
    Find the OCR item closest to the test's Y position
    inside a specific X column.
    """

    candidates = []

    for item in items:

        if not (
            min_x <= item["x"] <= max_x
        ):
            continue

        y_difference = abs(
            item["y"] - test_y
        )

        if y_difference <= max_y_distance:

            candidates.append(
                (
                    y_difference,
                    item
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x[0],
            -x[1]["confidence"]
        )
    )

    return candidates[0][1]


def find_result(
    items,
    test_y
):
    """
    Find result value in the RESULT column.

    For your report the result column is approximately:
        X = 550-750

    """

    candidates = []

    for item in items:

        # Result column
        if not (
            500 <= item["x"] <= 750
        ):
            continue

        y_difference = abs(
            item["y"] - test_y
        )

        if y_difference > 30:
            continue

        value = extract_single_number(
            item["text"]
        )

        if value is None:
            continue

        candidates.append({
            "value": value,
            "unit": detect_unit(item["text"]),
            "y_difference": y_difference,
            "confidence": item["confidence"],
            "text": item["text"]
        })

    if not candidates:
        return None

    # Closest Y first
    candidates.sort(
        key=lambda x: (
            x["y_difference"],
            -x["confidence"]
        )
    )

    return candidates[0]


def find_reference(
    items,
    test_y
):
    """
    Find reference range in the reference column.

    For your report:
        X ≈ 900-1100
    """

    candidates = []

    for item in items:

        if not (
            850 <= item["x"] <= 1150
        ):
            continue

        y_difference = abs(
            item["y"] - test_y
        )

        if y_difference > 35:
            continue

        low, high = extract_reference_range(
            item["text"]
        )

        if low is None:
            continue

        candidates.append({
            "low": low,
            "high": high,
            "y_difference": y_difference,
            "confidence": item["confidence"],
            "text": item["text"]
        })

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x["y_difference"],
            -x["confidence"]
        )
    )

    return candidates[0]


def parse_ocr_results(ocr_results):

    items = prepare_items(
        ocr_results
    )

    tests = find_test_items(
        items
    )

    parsed = []

    # Prevent duplicate test names
    used_tests = set()

    for test in tests:

        test_name = test["test_name"]
        test_y = test["y"]

        # If same test appears twice, keep first
        if test_name in used_tests:
            continue

        used_tests.add(test_name)

        result = find_result(
            items,
            test_y
        )

        reference = find_reference(
            items,
            test_y
        )

        value = None
        unit = ""

        if result:

            value = result["value"]
            unit = result["unit"]

        reference_low = None
        reference_high = None

        if reference:

            reference_low = reference["low"]
            reference_high = reference["high"]

        parsed.append({
            "test_name": test_name,
            "value": value,
            "unit": unit,
            "reference_low": reference_low,
            "reference_high": reference_high
        })

    return parsed