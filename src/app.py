from flask import Flask, request, jsonify, render_template, g
from PIL import Image
import numpy as np
import io
import os
import logging
import time
import json

# --- Structured Logging Setup ---

class JsonFormatter(logging.Formatter):
    """Formats log records as JSON."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if hasattr(record, 'extra_info'):
            log_record.update(record.extra_info)
        return json.dumps(log_record)

def setup_logging(app):
    """Configures structured logging for the Flask app."""
    log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    
    # Use a custom JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    
    # Configure app logger
    app.logger.handlers = [handler]
    app.logger.setLevel(log_level)
    
    # Configure Werkzeug logger to be less verbose
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = [handler]
    werkzeug_logger.setLevel(logging.WARNING) # Quieter in production

app = Flask(__name__, template_folder='../templates')
setup_logging(app)


# --- Request Hooks for Logging ---

@app.before_request
def before_request_logging():
    """Log request details and start timer."""
    g.start_time = time.time()
    app.logger.info(
        "Incoming request",
        extra={'extra_info': {
            "method": request.method,
            "path": request.path,
            "ip": request.remote_addr,
            "headers": dict(request.headers)
        }}
    )

@app.after_request
def after_request_logging(response):
    """Log response details and total processing time."""
    duration = time.time() - g.start_time
    app.logger.info(
        "Request completed",
        extra={'extra_info': {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_mimetype": response.mimetype
        }}
    )
    return response


# --- Application Routes ---

@app.route('/')
def index():
    """Serve the index.html page"""
    return render_template('index.html')


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
        app.logger.error(f"Pillow image processing failed: {str(e)}", exc_info=True)
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
            app.logger.warning("Validation failed: No image file provided.")
            return jsonify({
                "error": "No image file provided. Please upload a file with key 'image'"
            }), 400
        
        file = request.files['image']
        
        # Check if file was selected
        if file.filename == '':
            app.logger.warning("Validation failed: No file selected.")
            return jsonify({
                "error": "No file selected"
            }), 400
        
        # Read file data
        image_data = file.read()
        
        if not image_data:
            app.logger.warning(f"Validation failed: Empty file uploaded. Filename: {file.filename}")
            return jsonify({
                "error": "Empty file uploaded"
            }), 400
        
        # Calculate average intensity
        result = calculate_average_intensity(image_data)
        
        # Add filename to response
        result['filename'] = file.filename
        
        app.logger.info(
            "Successfully calculated image intensity.",
            extra={'extra_info': {
                "filename": file.filename,
                "intensity": result['average_intensity']
            }}
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        app.logger.warning(f"Client error during intensity calculation: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 400
        
    except Exception as e:
        app.logger.error(f"Internal server error: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    app.logger.warning(f"404 Not Found: {request.path}")
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": {
            "GET /": "Serves the web interface.",
            "POST /intensity": "Calculate image intensity"
        }
    }), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Set debug mode based on environment variable
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') == 'development'
    
    # Re-setup logging in case debug status changed
    setup_logging(app)
    
    app.run(host='0.0.0.0', port=port)
