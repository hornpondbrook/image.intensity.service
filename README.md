# Image Intensity Service

## 1. Overview

This project is a Python-based web service built with Flask that calculates the average grayscale intensity of a PNG image. It provides both an interactive web interface for manual uploads and a RESTful API for programmatic use.

The intensity is computed by converting the image to grayscale and calculating the mean pixel value, resulting in a value between 0 (black) and 255 (white).

## 2. Features

-   **Interactive Web Interface**: A simple, clean UI for uploading images directly from the browser.
-   **RESTful API**: A straightforward API for integrating the service into other applications.
-   **Client-Side Image Preview**: See a thumbnail of your selected image before you upload it.
-   **Structured JSON Logging**: All events are logged in a machine-readable JSON format, perfect for production monitoring.
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
-   Choose a PNG file from your local machine.
-   See a preview of the selected image.
-   Upload the image and view the calculated intensity results.

### API Endpoints

#### `GET /`

-   **Description**: Serves the main web interface.
-   **Response**: `text/html`

#### `POST /intensity`

-   **Description**: Calculates the average intensity of an uploaded PNG image.
-   **Request `Content-Type`**: `multipart/form-data`
-   **Request Body**: Must contain a file field named `image`.

-   **Success Response (`200 OK`)**:
    ```json
    {
      "average_intensity": 127.45,
      "filename": "sample.png",
      "image_size": [800, 600],
      "original_mode": "RGB",
      "pixel_count": 480000
    }
    ```

-   **Error Response (`400 Bad Request`)**:
    ```json
    {
      "error": "Image must be in PNG format. Received: JPEG"
    }
    ```

### API Usage Examples

#### cURL

```bash
curl -X POST -F "image=@/path/to/your/image.png" http://localhost:5000/intensity
```

#### Python (`requests`)

```python
import requests

file_path = 'path/to/your/image.png'

with open(file_path, 'rb') as f:
    files = {'image': (file_path, f, 'image/png')}
    response = requests.post('http://localhost:5000/intensity', files=files)

print(response.json())
```

## 5. Development

This section contains information for developers contributing to the project.

### Project Structure

```
image-intensity-service/
├── src/
│   └── app.py            # Flask application, endpoints, and core logic
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

### Logging

The application uses structured JSON logging, which is ideal for production environments.
- **Format**: JSON lines sent to standard output.
- **Details**: Each log entry includes a timestamp, level, message, and request context (method, path, IP, duration).
- **Example Log Entry**:
  ```json
  {"timestamp": "2023-10-27T10:30:00,123", "level": "INFO", "message": "Request completed", "name": "src.app", "extra_info": {"method": "POST", "path": "/intensity", "status_code": 200, "duration_ms": 54.21, "response_mimetype": "application/json"}}
  ```

### Core Logic Notes

-   **Intensity Calculation**: The core logic resides in the `calculate_average_intensity` function. It first validates that the image is a PNG, converts it to grayscale (`L` mode), transforms it into a NumPy array, and computes the mean.
-   **Error Handling**: The API returns descriptive JSON error messages with appropriate HTTP status codes (e.g., `400` for client errors, `500` for server errors).

## 6. Future Enhancements

-   Add an explicit limit for image file size.
-   Support for additional image formats (e.g., JPEG).
-   Implement asynchronous processing for large images using a task queue like Celery.
-   Add authentication and rate limiting to the API.
-   Expand test suite to cover more edge cases and the web UI.