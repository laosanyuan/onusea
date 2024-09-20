from PIL import Image

def get_image_size(image_path: str) -> tuple[int, int]:
    """获取图片size

    Args:
        image_path (str): 图片路径

    Returns:
        tuple[int, int]: width,height
    """
    with Image.open(image_path) as img:
        width, height = img.size
    return width, height