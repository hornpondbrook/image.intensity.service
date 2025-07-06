import io
import numpy as np
from PIL import Image
import logging
from typing import List, Dict, Any

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def calculate_average_intensity(image_data: bytes, allowed_formats: List[str]) -> Dict[str, Any]:
    """
    Calculates the average pixel intensity of an image.
    
    This function first validates the image format against a list of allowed
    formats. It then converts the image to grayscale ('L' mode) to ensure a
    consistent intensity calculation across different image types (e.g., RGB,
    RGBA). The average intensity is computed from the pixel values of the
    grayscale image.
    
    Args:
        image_data: The raw binary data of the image.
        allowed_formats: A list of uppercase strings representing the
            allowed image formats (e.g., ['PNG', 'JPEG']).
    
    Returns:
        A dictionary containing the calculated average intensity, image
        dimensions, the original color mode of the image, and the total
        pixel count.
    
    Raises:
        ValueError: If the image format is not in the allowed list or if
            the image data is corrupted or cannot be processed.
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