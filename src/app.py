from flask import Flask, request, jsonify, render_template, g, current_app, has_request_context
from PIL import Image
import numpy as np
import io
import os
import logging
import time
import json
import uuid
from werkzeug.exceptions import HTTPException
from config import get_config_by_name

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
        if hasattr(g, 'request_id'):
            log_record['request_id'] = g.request_id
        if hasattr(record, 'extra_info'):
            log_record.update(record.extra_info)
        return json.dumps(log_record)

def setup_logging(app):
    """Configures structured logging for the Flask app."""
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    
    app.logger.handlers = [handler]
    app.logger.setLevel(log_level)
    
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = [handler]
    werkzeug_logger.setLevel(logging.WARNING)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # --- Configuration ---
    # Load configuration from environment variable (e.g., 'development', 'production')
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(get_config_by_name(config_name))

    # --- Logging ---
    setup_logging(app)

    # --- Request Hooks ---
    @app.before_request
    def before_request_logging():
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
        app.logger.info(
            "Incoming request",
            extra={'extra_info': {
                "method": request.method,
                "path": request.path,
                "ip": request.remote_addr
            }}
        )

    @app.after_request
    def after_request_logging(response):
        duration = time.time() - g.start_time
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        app.logger.info(
            "Request completed",
            extra={'extra_info': {
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }}
        )
        return response

    # --- Routes and Error Handlers ---
    register_routes_and_handlers(app)

    return app

def register_routes_and_handlers(app):
    """Register all routes and error handlers for the app."""
    
    @app.route('/')
    def index():
        """Serve the index.html page"""
        return render_template('index.html')

    @app.route('/intensity', methods=['POST'])
    def get_image_intensity():
        """API endpoint to calculate average intensity of a PNG or JPEG image."""
        try:
            if 'image' not in request.files:
                app.logger.warning("Validation failed: No image file provided.")
                return jsonify({"error": "No image file provided. Please upload a file with key 'image'", "request_id": g.request_id}), 400
            
            file = request.files['image']
            
            if file.filename == '':
                app.logger.warning("Validation failed: No file selected.")
                return jsonify({"error": "No file selected", "request_id": g.request_id}), 400
            
            image_data = file.read()
            
            if not image_data:
                app.logger.warning(f"Validation failed: Empty file uploaded. Filename: {file.filename}")
                return jsonify({"error": "Empty file uploaded", "request_id": g.request_id}), 400
            
            result = calculate_average_intensity(image_data)
            result['filename'] = file.filename
            result['request_id'] = g.request_id
            
            app.logger.info(
                "Successfully calculated image intensity.",
                extra={'extra_info': {
                    "filename": file.filename,
                    "intensity": result['average_intensity'],
                    "image_size_bytes": len(image_data)
                }}
            )
            return jsonify(result), 200
            
        except ValueError as e:
            app.logger.warning(f"Client error during intensity calculation: {str(e)}")
            return jsonify({"error": str(e), "request_id": g.request_id}), 400

            

    def calculate_average_intensity(image_data):
        """Calculate the average intensity of an image."""
        try:
            image = Image.open(io.BytesIO(image_data))
            allowed_formats = current_app.config['ALLOWED_IMAGE_FORMATS']
            if image.format not in allowed_formats:
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
            app.logger.error(f"Pillow image processing failed: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing image: {str(e)}")


    @app.errorhandler(413)
    def payload_too_large(e):
        """Handle 413 Payload Too Large error."""
        max_size_mb = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        # Note: request.content_length may not be available if the error happens very early
        app.logger.warning(f"File upload failed: Payload too large.")
        return jsonify({"error": f"File is too large. The maximum allowed size is {max_size_mb:.1f} MB.", "request_id": g.request_id if hasattr(g, 'request_id') else None}), 413

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        app.logger.warning(f"404 Not Found: {request.path}")
        return jsonify({
            "error": "Endpoint not found",
            "request_id": g.request_id,
            "available_endpoints": {
                "GET /": "Serves the web interface.",
                "POST /intensity": "Calculate image intensity"
            }
        }), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle all HTTP exceptions, returning a JSON error message."""
        # Get the response object from the exception
        response = e.get_response()

        req_id = None
        if has_request_context() and hasattr(g, 'request_id'):
            req_id = g.request_id
        
        # Create a JSON response
        response.data = json.dumps({
            "code": e.code,
            "name": e.name,
            "description": e.description,
            "request_id": req_id,
        })
        response.content_type = "application/json"

        # Log the exception with appropriate level
        log_level = "warning" if 400 <= e.code < 500 else "error"
        log_method = getattr(current_app.logger, log_level)

        extra_info = {"description": e.description}
        if has_request_context():
            extra_info.update({
                "path": request.path,
                "method": request.method,
            })
        
        log_method(
            f"HTTP Exception: {e.code} {e.name}",
            extra={'extra_info': extra_info}
        )
        
        return response

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
