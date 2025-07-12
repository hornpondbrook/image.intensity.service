from flask import Flask, request, jsonify, render_template, g, current_app, has_request_context, Response as FlaskResponse
from PIL import Image
import numpy as np
import io
import os
import logging
import time
import json
import uuid
import hashlib
import redis
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response
from typing import Any, Dict, Tuple
from flask_cors import CORS
from .config import get_config_by_name
import grpc
from .generated import processing_pb2, processing_pb2_grpc
from .shared.image_processing import calculate_average_intensity


def make_error_response(message: str, status_code: int, **kwargs: Any) -> Tuple[FlaskResponse, int]:
    """Creates a standardized JSON error response."""
    payload: Dict[str, Any] = {"error": message}
    if has_request_context() and hasattr(g, 'request_id'):
        payload['request_id'] = g.request_id
    payload.update(kwargs)
    return jsonify(payload), status_code

# --- Structured Logging Setup ---

class JsonFormatter(logging.Formatter):
    """
    Formats log records as structured JSON.
    
    This formatter includes standard log information along with any extra context
    provided, such as a request ID when processing web requests.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if has_request_context() and hasattr(g, 'request_id'):
            log_record['request_id'] = g.request_id
        if hasattr(record, 'extra_info'):
            log_record.update(record.extra_info)
        return json.dumps(log_record)

def setup_logging(app: Flask) -> None:
    """
    Configures structured, JSON-based logging for the Flask application.
    
    Sets up a handler that formats log messages as JSON, making them easier to
    parse and analyze by log management systems. It also sets the log level
    based on the application's debug status.
    
    Args:
        app: The Flask application instance.
    """
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    
    app.logger.handlers = [handler]
    app.logger.setLevel(log_level)
    
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = [handler]
    werkzeug_logger.setLevel(logging.WARNING)

def create_app() -> Flask:
    """
    Creates and configures the Flask application.
    
    This factory function initializes the Flask app, loads configuration from
    environment variables, sets up logging, and registers request hooks,
    routes, and error handlers.
    
    Returns:
        The configured Flask application instance.
    """
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'), static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'), static_url_path='/static')

    # --- CORS ---
    CORS(app)

    # --- Configuration ---
    # Load configuration from environment variable (e.g., 'development', 'production')
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(get_config_by_name(config_name))

    # --- Redis Cache ---
    app.redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        decode_responses=True
    )

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
    def after_request_logging(response: Response) -> Response:
        duration = time.time() - g.start_time
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id

        # Add duration to JSON responses
        if response.is_json:
            try:
                data = response.get_json()
                if isinstance(data, dict):
                    data['duration_ms'] = round(duration * 1000, 2)
                    response.set_data(json.dumps(data))
            except Exception as e:
                current_app.logger.error(f"Failed to add duration to JSON response: {e}")

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

def register_routes_and_handlers(app: Flask) -> None:
    """
    Registers all routes and error handlers for the application.
    
    This function encapsulates the registration of URL routes and error handlers
    to keep the `create_app` factory clean and organized.
    
    Args:
        app: The Flask application instance.
    """
    
    @app.route('/')
    def index():
        """
        Serves the main HTML page for the web interface.
        
        Returns:
            The rendered `index.html` template.
        """
        return render_template('index.html')

    @app.route('/intensity', methods=['POST'])
    def get_image_intensity() -> Tuple[FlaskResponse, int]:
        """
        API endpoint to calculate the average intensity of an uploaded image.
        
        Accepts a POST request with a multipart/form-data image file. The image
        must be in a format specified in the application's configuration (e.g.,
        PNG, JPEG).
        
        Returns:
            A JSON response containing the analysis results, including the
            average intensity, image dimensions, and other metadata.
            On error, returns a JSON object with an error description.
        """
        try:
            if 'image' not in request.files:
                app.logger.warning("Validation failed: No image file provided.")
                return make_error_response("No image file provided. Please upload a file with key 'image'", 400)
            
            file = request.files['image']
            
            if file.filename == '':
                app.logger.warning("Validation failed: No file selected.")
                return make_error_response("No file selected", 400)
            
            image_data = file.read()
            
            if not image_data:
                app.logger.warning(f"Validation failed: Empty file uploaded. Filename: {file.filename}")
                return make_error_response("Empty file uploaded", 400)

            # --- Caching Logic ---
            image_hash = hashlib.sha256(image_data).hexdigest()
            cache_key = f"image_intensity:{image_hash}"

            try:
                cached_result = current_app.redis_client.get(cache_key)
                if cached_result:
                    current_app.logger.info(f"Cache hit for image hash: {image_hash}")
                    response = jsonify(json.loads(cached_result))
                    response.headers['X-Cache'] = 'hit'
                    return response, 200
            except redis.exceptions.RedisError as e:
                current_app.logger.error(f"Redis error on cache GET: {e}")

            current_app.logger.info(f"Cache miss for image hash: {image_hash}")
            
            allowed_formats = current_app.config['ALLOWED_IMAGE_FORMATS']

            try:
                with grpc.insecure_channel(current_app.config['GRPC_SERVER_ADDRESS']) as channel:
                    stub = processing_pb2_grpc.ImageProcessorStub(channel)
                    response = stub.AnalyzeImage(processing_pb2.ImageRequest(image_data=image_data, allowed_formats=allowed_formats))

                result = {
                    'average_intensity': response.average_intensity,
                    'image_size': [response.width, response.height],
                    'original_mode': response.original_mode,
                    'pixel_count': response.pixel_count,
                    'filename': file.filename,
                    'request_id': g.request_id,
                    'image_size_bytes': len(image_data),
                }

                # --- Cache the result ---
                try:
                    current_app.redis_client.setex(
                        cache_key,
                        current_app.config['CACHE_TTL_SECONDS'],
                        json.dumps(result)
                    )
                except redis.exceptions.RedisError as e:
                    current_app.logger.error(f"Redis error on cache SET: {e}")

                app.logger.info(
                    "Successfully calculated image intensity.",
                    extra={'extra_info': {
                        "filename": file.filename,
                        "intensity": result['average_intensity'],
                        "image_size_bytes": len(image_data)
                    }}
                )
                response = jsonify(result)
                response.headers['X-Cache'] = 'miss'
                return response, 200

            except grpc.RpcError as e:
                app.logger.error(f"gRPC error during intensity calculation: {e.details()}")
                if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                    return make_error_response(f"Error processing image: {e.details()}", 400)
                else:
                    return make_error_response(f"Error processing image: {e.details()}", 500)
            
        except ValueError as e:
            app.logger.warning(f"Client error during intensity calculation: {str(e)}")
            return make_error_response(str(e), 400)

            

    @app.errorhandler(413)
    def payload_too_large(e: HTTPException) -> Tuple[FlaskResponse, int]:
        """
        Handles the 413 Payload Too Large error.
        
        This error is triggered when the uploaded file exceeds the maximum
        configured size (`MAX_CONTENT_LENGTH`).
        
        Args:
            e: The HTTPException instance.
        
        Returns:
            A JSON response with an error message and a 413 status code.
        """
        max_size_mb = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        # Note: request.content_length may not be available if the error happens very early
        app.logger.warning(f"File upload failed: Payload too large.")
        return make_error_response(f"File is too large. The maximum allowed size is {max_size_mb:.1f} MB.", 413)

    @app.errorhandler(404)
    def not_found(e: HTTPException) -> Tuple[FlaskResponse, int]:
        """
        Handles 404 Not Found errors.
        
        Returns a JSON response indicating that the requested endpoint does not
        exist and provides a list of available endpoints.
        
        Args:
            e: The HTTPException instance.
        
        Returns:
            A JSON response with an error message and a 404 status code.
        """
        app.logger.warning(f"404 Not Found: {request.path}")
        return make_error_response(
            "Endpoint not found",
            404,
            available_endpoints={
                "GET /": "Serves the web interface.",
                "POST /intensity": "Calculate image intensity"
            }
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException) -> Response:
        """
        Generic handler for all HTTP exceptions.
        
        This function catches any `HTTPException` not explicitly handled and
        formats it into a standardized JSON error response.
        
        Args:
            e: The HTTPException instance.
        
        Returns:
            A Flask Response object with a JSON payload describing the error.
        """
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
