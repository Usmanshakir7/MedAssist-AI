from PIL import Image, ImageEnhance


def preprocess_image(input_path, output_path):

    image = Image.open(input_path)

    # Convert to grayscale
    image = image.convert("L")

    # Increase size
    width, height = image.size

    image = image.resize(
        (width * 2, height * 2)
    )

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)

    image = enhancer.enhance(2.0)

    # Save processed image
    image.save(output_path)

    return output_path