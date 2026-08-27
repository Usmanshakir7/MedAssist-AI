import easyocr


# Load OCR reader only once
reader = easyocr.Reader(
    ["en"],
    gpu=False
)


def extract_text(file_path):
    """
    Extract text, coordinates and confidence from an image.
    """

    results = reader.readtext(file_path)

    ocr_results = []

    for result in results:

        box = result[0]
        text = result[1]
        confidence = result[2]

        ocr_results.append({
            "text": text,
            "confidence": float(confidence),
            "box": box
        })

    return ocr_results