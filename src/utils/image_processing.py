import io
import numpy as np
from PIL import Image
import logging
from typing import List, Dict, Any

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def calculate_average_intensity(image_data: bytes, allowed_formats: List[str]) -> Dict[str, Any]:
    """Calculate the average intensity of an image.

    Args:
        image_data (bytes): The raw image data.
        allowed_formats (list): A list of allowed image formats (e.g., ['PNG', 'JPEG']).

    Returns:
        dict: A dictionary containing average intensity, image size, original mode, and pixel count.

    Raises:
        ValueError: If the image format is not allowed or if there's an error processing the image.
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        if image.format not in allowed_formats:
            logger.warning(f"Image format not allowed: {image.format}. Allowed: {', '.join(allowed_formats)}")
            raise ValueError(f"Image must be in one of the following formats: {', '.join(allowed_formats)}. Received: {image.format}")
        
        width, height = image.size
        
        grayscale_image = image.convert('L') if image.mode != 'L' else image
        
        img_array = np.array(grayscale_image)
        average_intensity = float(np.mean(img_array))
        
        return {
            'average_intensity': round(average_intensity, 2),
            'image_size': [width, height],
            'original_mode': image.mode,
            'pixel_count': width * height
        }
    
    except Exception as e:
        logger.error(f"Pillow image processing failed: {str(e)}", exc_info=True)
        raise ValueError(f"Error processing image: {str(e)}")