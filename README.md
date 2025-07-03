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
-   **Containerized**: Comes with a `Dockerfile` for easy and consistent deployment.

## 3. Getting Started


This section will guide you through running the service.

### Prerequisites

-   Docker
-   Python 3.8+ and `pip` (for local development)

### Running with Docker (Recommended)

Using Docker is the simplest way to get the service running.

1.  **Build the image:**
    ```bash
    docker build -t image-intensity-service .
    ```

2.  **Run the container:**
    ```bash
    docker run -p 5000:5000 image-intensity-service
    ```

The service will be available at `http://localhost:5000`.

### Running Locally for Development

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd image-intensity-service
    ```

2.  **Set up a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Run the application:**
    ```bash
    FLASK_ENV=development python src/app.py
    ```

The service will be available at `http://localhost:5000`.

## 4. Usage

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

## 5. Configuration

The application can be configured using environment variables. This allows you to customize its behavior without modifying the code.

-   **`FLASK_ENV`**: Sets the application environment. Can be `development`, `production`, or `testing`. Defaults to `development`.
-   **`MAX_CONTENT_LENGTH`**: The maximum file size for uploads, in bytes. Defaults to `5242880` (5 MB).
-   **`ALLOWED_IMAGE_FORMATS`**: A comma-separated list of allowed image formats. Defaults to `PNG,JPEG`.
-   **`SECRET_KEY`**: A secret key for session management and other security features. It is highly recommended to set a strong, unique secret in production.

To set an environment variable, you can use:

```bash
export FLASK_ENV=production
export MAX_CONTENT_LENGTH=10485760  # 10 MB
```

## 6. Development

This section contains information for developers contributing to the project.

### Project Structure

```
image-intensity-service/
├── src/
│   ├── app.py            # Flask application, endpoints, and core logic
│   └── utils/
│       └── image_processing.py # Utility module for image processing functions
├── templates/
│   └── index.html        # Web interface HTML
├── tests/
│   └── test_api.py       # Pytest tests for the API
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development and testing dependencies
├── Dockerfile            # Container configuration
└── README.md             # This file
```

### Running Tests

Ensure you have installed the development dependencies (`requirements-dev.txt`).

```bash
# Run all tests with verbose output
pytest -v

# Run tests with code coverage report
pytest --cov=src --cov-report=html
```
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

## 6. Future Enhancements

-   Implement asynchronous processing for large images using a task queue like Celery.
-   Add authentication and rate limiting to the API.
-   Expand test suite to cover more edge cases and the web UI.