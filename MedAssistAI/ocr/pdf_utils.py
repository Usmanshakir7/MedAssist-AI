import fitz  # PyMuPDF


def pdf_to_images(pdf_path, output_dir, zoom=2.0):
    """
    Rasterize every page of a PDF into a PNG image so it can be
    run through the same OCR pipeline used for JPG/PNG uploads.

    Returns a list of output image paths, one per page, in order.
    """

    doc = fitz.open(pdf_path)

    matrix = fitz.Matrix(zoom, zoom)

    image_paths = []

    base_name = pdf_path.rsplit(".", 1)[0]

    for page_number in range(len(doc)):

        page = doc.load_page(page_number)

        pix = page.get_pixmap(matrix=matrix)

        image_path = f"{base_name}_page{page_number + 1}.png"

        pix.save(image_path)

        image_paths.append(image_path)

    doc.close()

    return image_paths
