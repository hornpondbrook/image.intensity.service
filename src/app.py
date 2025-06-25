from flask import Flask, request, jsonify
from PIL import Image
import numpy as np
import io
import os

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def calculate_average_intensity(image_data):
    """
    Calculate the average intensity of an image.
    
    Args:
        image_data (bytes): Raw image data
        
    Returns:
        dict: Dictionary containing intensity and image info
        
    Raises:
        ValueError: If image processing fails
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Verify it's a PNG
        if image.format != 'PNG':
            raise ValueError(f"Image must be in PNG format. Received: {image.format}")
        
        # Get image dimensions
        width, height = image.size
        
        # Convert to grayscale if not already
        if image.mode != 'L':
            grayscale_image = image.convert('L')
        else:
            grayscale_image = image
        
        # Convert to numpy array and calculate average
        img_array = np.array(grayscale_image)
        average_intensity = float(np.mean(img_array))
        
        return {
            'average_intensity': round(average_intensity, 2),
            'image_size': [width, height],
            'original_mode': image.mode,
            'pixel_count': width * height
        }
    
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

@app.route('/intensity', methods=['POST'])
def get_image_intensity():
    """
    API endpoint to calculate average intensity of a PNG image.
    
    Expected: POST request with PNG image file
    Returns: JSON with average intensity value and image metadata
    """
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({
                "error": "No image file provided. Please upload a file with key 'image'"
            }), 400
        
        file = request.files['image']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                "error": "No file selected"
            }), 400
        
        # Read file data
        image_data = file.read()
        
        if not image_data:
            return jsonify({
                "error": "Empty file uploaded"
            }), 400
        
        # Calculate average intensity
        result = calculate_average_intensity(image_data)
        
        # Add filename to response
        result['filename'] = file.filename
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400
        
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        "error": "File too large. Maximum size allowed is 16MB"
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": {
            "POST /intensity": "Calculate image intensity"
        }
    }), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)