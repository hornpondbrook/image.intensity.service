# Image Intensity Service

## 1. Overview

This project is a Python-based web service built with Flask that calculates the average grayscale intensity of a PNG or JPEG image. It provides both an interactive web interface for manual uploads and a RESTful API for programmatic use.

The intensity is computed by converting the image to grayscale and calculating the mean pixel value, resulting in a value between 0 (black) and 255 (white).

## 2. Features

-   **Interactive Web Interface**: A modern, responsive UI for uploading images directly from the browser, featuring:
    -   **Streamlined Layout**: Input controls (file input, Analyze, Clear buttons) in a single row, with image preview and analysis results displayed side-by-side below.
    -   **Intuitive File Selection**: "Choose image file" prompt directly on the file input.
    -   **Clear Actions**: Dedicated "Analyze" and "Clear" buttons for easy interaction.
    -   **Enhanced Error Display**: Prominent, dismissible alerts for user feedback.
-   **RESTful API**: A straightforward API for integrating the service into other applications.
-   **Multi-Format Support**: Calculates intensity for both PNG and JPEG images.
-   **Client-Side Image Preview**: See a thumbnail of your selected image before you upload it.
-   **Client-Side File Type Validation**: Pre-checks image type (PNG/JPEG) before upload for immediate feedback.
-   **File Size Limit**: Protects the server by rejecting files larger than 5 MB.
-   **Structured JSON Logging**: All events are logged in a machine-readable JSON format, perfect for production monitoring.
-   **Request Tracing**: Each request is assigned a unique ID (`X-Request-ID` header and `request_id` in response body) for improved logging and end-to-end traceability.
-   **Performance Metrics**: The API response includes the request processing time (`duration_ms`) and the raw image size in bytes (`image_size_bytes`).
-   **CORS Enabled**: The API is configured to accept cross-origin requests, allowing it to be called from any web frontend.
-   **Result Caching**: Implemented using Redis to cache image intensity calculation results. Subsequent requests for the same image will be served from the cache, significantly reducing processing time and load on the Image Processor. Responses include an `X-Cache` header (`hit` or `miss`) for observability.
-   **Containerized**: Comes with a `Dockerfile` for easy and consistent deployment.

## 3. Architecture                                                                                                               
                                                                                                                              
The application is designed using a microservices architecture to separate the web-facing API from the core computationa         
logic. This design enhances scalability, performance, and maintainability.                                                       
                                                                                                                              
The system consists of two main services:                                                                                        
                                                                                                                              
1.  **API Gateway**: A public-facing Flask web application that handles all incoming HTTP requests. It is responsible fo         
serving the web interface, validating user input, and managing the RESTful API. It acts as a gRPC client, forwarding             
processing requests to the internal Image Processor service.                                                                     
                                                                                                                              
2.  **Image Processor**: An internal gRPC service dedicated to performing the computationally intensive image analysis.          
receives image data via high-performance gRPC calls, calculates the intensity, and returns the structured result.                
                                                                                                                              
This separation allows the two components to be developed, deployed, and scaled independently.                                   
                                                                                                                              
### System Diagram                                                                                                               
                                                                                                                              
```                                                                                                                              
                                  +-------------------------+                                                                    
                                  |   API Gateway (Flask)   |                                                                    
(Browser, curl, etc.) <----HTTP---->   (Public-Facing)       |                                                                    
                                  |                         |                                                                    
                                  +-----------+-------------+                                                                    
                                      ^       |                                                                                  
                                      |       | gRPC                                                                             
                                Redis |       |                                                                                  
                               (Cache)|       v                                                                                  
                                      |   +-------------------------+                                                              
                                  +---v-------+   |  Image Processor        |                                                      
                                  |  Redis    |   |  (gRPC Service)         |                                                      
                                  +-----------+   |   (Internal)            |                                                      
                                                  +-------------------------+                                                      
```                                                                                                                              
                                                                                                                              
### Communication Flow                                                                                                           
                                                                                                                              
1.  A user uploads an image via the web interface or by calling the `POST /intensity` REST endpoint.                             
2.  The **API Gateway** receives the HTTP request, validates it, extracts the image data and generate cache key of
    SHA-256 hash based on the image data.                                    
3.  The Gateway first check the cache with the key to see if the image has already been processed, if yes, the result will
    be retrieved from the cache and sent to client, for cache miss, it makes a gRPC call to the **Image Processor** service, 
    sending the image data using Protocol Buffers for efficient serialization.                         
4.  The **Image Processor** calculates the average intensity and returns the result to the Gateway.                              
5.  The **API Gateway** formats the result into a JSON response and sends it back to the client.                                 
  
## 4. Getting Started


This section will guide you through running the service.

### Prerequisites

-   Docker and Docker Compose
-   Python 3.10+ and `pip` (for local development)

### Running All Services with Docker Compose (Recommended)

This is the easiest way to get both the API Gateway and the Image Processor services running.

1.  **Build and run the services:**
    ```bash
    docker-compose up --build -d
    ```
    This command builds the Docker images for both `api_gateway` and `image_processor` services (if they haven't been built or if their Dockerfiles have changed) and starts them in detached mode.

2.  **Access the API Gateway:**
    The API Gateway (Flask app) will be available at `http://localhost:5000`.

### Running Locally for Development

For active development on the API Gateway, it's often more convenient to run it directly on your host machine while keeping the Image Processor service containerized.

1.  **Start the Image Processor Service (Dockerized):**
    First, ensure the gRPC image processor service is running in Docker:
    ```bash
    docker-compose up -d image_processor
    ```

2.  **Set up a virtual environment (if not already done):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install development dependencies:**
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Run the API Gateway application locally:**
    Ensure your current working directory is the project root (`image.intensity.service/`).
    ```bash
    PYTHONPATH=$(pwd)/src FLASK_ENV=development python -m src.app
    ```
    The API Gateway will be available at `http://localhost:5000`.

### Stopping Services

-   To stop only the Dockerized `image_processor` service:
    ```bash
    docker-compose down image_processor
    ```
-   To stop all services started by `docker-compose up` and remove their containers:
    ```bash
    docker-compose down
    ```
-   To stop the locally running API Gateway, press `Ctrl+C` in its terminal.

### Cleaning Up Docker Resources

To remove all Docker resources (containers, networks, volumes, and images) associated with this project, you can use the following commands. This is useful for a clean slate or to free up disk space.

1.  **Stop and remove all containers, networks, and volumes:**
    ```bash
    docker-compose down --volumes --rmi all
    ```
    This command stops the running containers, removes the containers, networks, and any anonymous volumes attached to containers. The `--rmi all` flag also removes images used by any service in `docker-compose.yml`.

2.  **Remove dangling images (optional, but recommended for cleanup):**
    Sometimes, Docker might leave behind unused or 'dangling' images. You can remove them with:
    ```bash
    docker image prune
    ```
    Confirm the prompt to proceed.

3.  **Remove all unused Docker networks (optional):**
    ```bash
    docker network prune
    ```

4.  **Remove all unused Docker volumes (optional):**
    ```bash
    docker volume prune
    ```



## 5. Usage

Once the service is running, you can interact with it in two ways:

### Web Interface

Navigate to `http://localhost:5000` in your web browser. The interface allows you to:
-   Choose a PNG or JPEG file from your local machine using the "Choose image file" input.
-   See a preview of the selected image.
-   Click "Analyze" to upload the image and view the calculated intensity results, which include file size and processing time.
-   Click "Clear" to reset the form and results.
-   Receive immediate feedback for invalid file types or other client-side issues.

### API Endpoints

#### `GET /`

-   **Description**: Serves the main web interface.
-   **Response**: `text/html`

#### `POST /intensity`

-   **Description**: Calculates the average intensity of an uploaded PNG or JPEG image.
-   **Request `Content-Type`**: `multipart/form-data`
-   **Request Body**: Must contain a file field named `image`.

-   **Success Response (`200 OK`)**:
    -   **Body**:
        ```json
        {
          "average_intensity": 127.45,
          "filename": "sample.png",
          "image_size": [800, 600],
          "original_mode": "RGB",
          "pixel_count": 480000,
          "duration_ms": 25.5,
          "image_size_bytes": 123456,
          "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
        }
        ```
    -   **Headers**:
        -   `X-Request-ID`: A unique identifier for the request (e.g., `a1b2c3d4-e5f6-7890-1234-567890abcdef`).

-   **Error Responses**:
    -   `400 Bad Request`: For invalid input, such as wrong file format (e.g., GIF, TIFF). The response body includes a `request_id`.
    -   `413 Payload Too Large`: If the uploaded file exceeds the 5 MB size limit. The response body includes a `request_id`.

### API Usage Examples

#### cURL

```bash
# Example with a PNG file
curl -X POST -F "image=@/path/to/your/image.png" http://localhost:5000/intensity

# Example with a JPEG file
curl -X POST -F "image=@/path/to/your/image.jpg" http://localhost:5000/intensity
```

#### Python (`requests`)

```python
import requests

# Example with a PNG file
file_path = 'path/to/your/image.png'
with open(file_path, 'rb') as f:
    files = {'image': (file_path, f, 'image/png')}
    response = requests.post('http://localhost:5000/intensity', files=files)
print(response.json())

# Example with a JPEG file
file_path = 'path/to/your/image.jpg'
with open(file_path, 'rb') as f:
    files = {'image': (file_path, f, 'image/jpeg')}
    response = requests.post('http://localhost:5000/intensity', files=files)
print(response.json())
```

## 6. Configuration

The application can be configured using environment variables. This allows you to customize its behavior without modifying the code.

-   **`FLASK_ENV`**: Sets the application environment. Can be `development`, `production`, or `testing`. Defaults to `development`.
-   **`MAX_CONTENT_LENGTH`**: The maximum file size for uploads, in bytes. Defaults to `5242880` (5 MB).
-   **`ALLOWED_IMAGE_FORMATS`**: A comma-separated list of allowed image formats. Defaults to `PNG,JPEG`.
-   **`SECRET_KEY`**: A secret key for session management and other security features. It is highly recommended to set a strong, unique secret in production.
-   **`REDIS_HOST`**: Hostname or IP address of the Redis server. Defaults to `redis` (for Docker Compose).
-   **`REDIS_PORT`**: Port of the Redis server. Defaults to `6379`.
-   **`CACHE_TTL_SECONDS`**: Time-To-Live (TTL) for cached image intensity results, in seconds. Defaults to `86400` (24 hours).

To set an environment variable, you can use:

```bash
export FLASK_ENV=production
export MAX_CONTENT_LENGTH=10485760  # 10 MB
export REDIS_HOST=localhost
export REDIS_PORT=6379
export CACHE_TTL_SECONDS=3600 # 1 hour
```

## 7. Development

This section contains information for developers contributing to the project.

### Project Structure

```
image-intensity-service/
├── src/
│   ├── __init__.py       # Marks src as a Python package
│   ├── app.py            # Flask application, endpoints, and core logic
│   ├── config.py         # Configuration settings
│   ├── generated/        # Auto-generated gRPC files
│   │   └── __init__.py   # Marks generated as a Python package
│   └── shared/
│       ├── __init__.py   # Marks shared as a Python package
│       └── image_processing.py # Utility module for image processing functions
│   └── utils/
│       └── __init__.py   # Marks utils as a Python package
├── image_processor/
│   ├── Dockerfile        # Dockerfile for the image processor service
│   └── server.py         # gRPC server for image processing
├── protos/
│   └── processing.proto  # Protocol Buffers definition for the gRPC service
├── templates/
│   └── index.html        # Web interface HTML
├── tests/
│   └── test_api.py       # Pytest tests for the API
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development and testing dependencies
├── Dockerfile            # Container configuration for the API gateway
├── docker-compose.yml    # Docker Compose file for running all services
└── README.md             # This file
```

### Caching Implementation Details

To optimize performance for repeated image analysis requests, a caching layer has been integrated using Redis. The caching mechanism works as follows:

1.  **Cache Key Generation**: When an image is uploaded, a SHA-256 hash of its binary content is computed. This hash serves as a unique identifier and the cache key.
2.  **Cache Lookup**: Before processing an image, the API Gateway checks if a result for the computed hash exists in the Redis cache.
3.  **Cache Hit**: If a cached result is found, it is immediately returned to the client. The `X-Cache` response header is set to `hit`.
4.  **Cache Miss**: If no cached result is found, the request is forwarded to the Image Processor service for computation. Once the result is obtained, it is stored in Redis with a configurable Time-To-Live (TTL) for future requests. The `X-Cache` response header is set to `miss`.

This approach significantly reduces latency and computational load for frequently requested images.

### Running Tests

To run the tests, ensure the `image_processor` gRPC service is running (either via `docker-compose up -d image_processor` or as part of `docker-compose up --build -d`).

Then, ensure you have installed the development dependencies (`requirements-dev.txt`) in your local environment.

```bash
# Start "image processor" service in another terminal
docker-compose up -d image_processor

# Run all tests with verbose output
pytest -v

# Run tests with code coverage report
pytest --cov=src --cov-report=html
```

#### Testing Caching with `fakeredis`

To ensure the caching logic works correctly without requiring a running Redis instance during unit tests, `fakeredis` is used. This library provides a drop-in replacement for the `redis-py` client that simulates Redis behavior in memory.

In `tests/test_api.py`, the `app` fixture is patched to use `fakeredis.FakeRedis` instead of the real `redis.Redis` client. This allows tests to interact with a simulated Redis cache.

The `test_caching_logic` function specifically verifies the cache hit and miss scenarios:

1.  **Cache Miss**: The first request for a given image (identified by its SHA-256 hash) will result in a cache miss. The `X-Cache` header in the response is asserted to be `miss`.
2.  **Cache Hit**: A subsequent request for the exact same image will result in a cache hit. The `X-Cache` header in the response is asserted to be `hit`, and the response data is verified to be identical to the first request (excluding dynamic fields like `request_id` and `duration_ms`).

This approach ensures that the caching mechanism correctly identifies and serves cached results, and that the fallback to the Image Processor occurs as expected on a cache miss.

### Testing CORS

To test the CORS functionality:

1.  Run the application locally.
2.  Open the `tests/test_cors.html` file in your web browser.
3.  Open the browser's developer console. You should see a "Success" message with the JSON response from the server, indicating that the CORS request was successful.

### Logging


The application uses structured JSON logging, which is ideal for production environments.
- **Format**: JSON lines sent to standard output.
- **Details**: Each log entry includes a timestamp, level, message, `request_id`, and request context (method, path, IP, duration).
- **Example Log Entry**:
  ```json
  {"timestamp": "2023-10-27T10:30:00,123", "level": "INFO", "message": "Request completed", "name": "src.app", "request_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", "extra_info": {"method": "POST", "path": "/intensity", "status_code": 200, "duration_ms": 54.21}}
  ```

### Core Logic Notes

-   **Intensity Calculation**: The core logic for image intensity calculation is now encapsulated in the `calculate_average_intensity` function within `src/utils/image_processing.py`. This function validates that the image is a PNG or JPEG, converts it to grayscale (`L` mode), transforms it into a NumPy array, and computes the mean.
-   **Input Validation**: The service validates that the file is a PNG or JPEG and is not empty. It also enforces a **5 MB file size limit** via the `MAX_CONTENT_LENGTH` setting.
-   **Error Handling**: The API returns descriptive JSON error messages with appropriate HTTP status codes. All error responses include a `request_id` for traceability. Specific handlers are in place for `400 Bad Request` (client-side validation and image processing errors), `413 Payload Too Large` (file size limits), and `404 Not Found` (unknown endpoints). A centralized `HTTPException` handler catches other HTTP errors, providing consistent JSON responses. Unhandled server-side issues will result in `500 Internal Server Error`.
-   **Code Quality**: The codebase includes type annotations and detailed docstrings for all functions, which improves readability and allows for static analysis.

## 8. Future Enhancements

-   Implement asynchronous processing for large images using a task queue like Celery.
-   Add authentication and rate limiting to the API.
-   Expand test suite to cover more edge cases and the web UI.
-   **Decouple Components**: Refactor the application to use dependency injection. This will decouple components like the image processing logic from the route handlers, making the application more modular, easier to test, and more maintainable.
-   **Improve Error Handling**: Implement a more robust error handling strategy by defining custom exception classes for specific business logic errors (e.g., `InvalidImageFormatError`, `EmptyFileError`). This will allow for more granular error handling and clearer API responses.
-   **Enhance Security**: Strengthen file upload security by validating file types based on their content (e.g., "magic bytes") rather than relying solely on file extensions. This will help prevent malicious file uploads.
-   **Optimize Performance**: Improve memory efficiency by implementing streaming for file uploads. Instead of reading the entire file into memory, process it in chunks to reduce the memory footprint and make the service more resilient to large files.