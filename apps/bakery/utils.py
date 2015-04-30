import re

import png_bakery


PNG_SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10]
SVG_SIGNATURE = 'http://www.w3.org/2000/svg'
HEADER_LENGTH = 256


def check_image_type(imageFile):
    header = imageFile.read(HEADER_LENGTH)
    if [ord(char) for char in header[:len(PNG_SIGNATURE)]] == PNG_SIGNATURE:
        return 'PNG'
    elif re.compile(SVG_SIGNATURE).search(str(header)):
        return 'SVG'


def unbake(imageFile):
    """
    Return the openbadges content contained in a baked image.
    """
    image_type = check_image_type(imageFile)
    imageFile.seek(0)
    if image_type == 'PNG':
        return png_bakery.unbake(imageFile)
    elif image_type == 'SVG':
        raise NotImplementedError("SVG UNBAKING COMING SOON.")


def bake(imageFile, assertion_json_string):
    """
    Embeds a serialized representation of a badge instance in an image file.
    """
    image_type = check_image_type(imageFile)
    imageFile.seek(0)  # reset pointer to the beginning of the file
    if image_type == 'PNG':
        return png_bakery.bake(imageFile, assertion_json_string)
    elif image_type == 'SVG':
        raise NotImplementedError("SVG BAKING COMING SOON.")
