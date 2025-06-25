# Image Intensity Service

A RESTful API service built with Python Flask that calculates the average intensity of PNG images.

## Overview

This service provides a simple HTTP API that accepts PNG image uploads and returns the calculated average intensity value. The intensity is computed by converting the image to grayscale and calculating the mean pixel value (range: 0-255).

## Architecture & Design

### Core Components

1. **Flask Web Application** (`app.py`)
   - RESTful API endpoints
   - Image processing and validation
   - Error handling and responses

2. **Docker Container** (`Dockerfile`)
   - Containerized deployment
   - Production-ready configuration
   - Optimized image size

### API Design

#### Endpoints

- `POST /intensity` - Calculate image intensity

#### Request Format
```
POST /intensity
Content-Type: multipart/form-data
Body: image file (PNG format)
```

#### Response Format
```json
{
  "average_intensity": 127.5,
  "filename": "example.png",
  "image_size": [800, 600]
}
```

#### Error Responses
```json
{
  "error": "Error message description"
}
```

### Technical Specifications

- **Image Processing**: PIL/Pillow library for robust PNG handling
- **Intensity Calculation**: 
  - Convert image to grayscale (L mode)
  - Calculate mean pixel value using NumPy
  - Return floating-point result (0.0 - 255.0)
- **Input Validation**:
  - File format verification (PNG only)
  - File size limits
  - Empty file detection
- **Error Handling**: Comprehensive validation with appropriate HTTP status codes

### Dependencies

- **Flask**: Web framework for API endpoints
- **Pillow (PIL)**: Image processing and manipulation
- **NumPy**: Numerical calculations for intensity computation

## Implementation Status

- [x] Initial design and architecture
- [x] Flask application implementation
- [x] Requirements specification (requirements.txt, requirements-dev.txt)
- [x] Dockerfile creation
- [x] API testing (test_api.py)
- [x] Documentation completion
- [x] Git configuration (.gitignore)

## Getting Started

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Docker (for containerized deployment)

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd image-intensity-service

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/app.py
```

### Docker Deployment

```bash
# Build the Docker image
docker build -t image-intensity-service .

# Run the container
docker run -p 5000:5000 image-intensity-service
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/test_api.py -v

# Run tests with coverage
pytest tests/test_api.py --cov=src.app

# Run specific test
pytest tests/test_api.py::test_intensity_calculation -v
```

### API Usage Examples

#### Using curl
```bash
# Upload PNG image
curl -X POST -F "image=@sample.png" http://localhost:5000/intensity
```

#### Using Python requests
```python
import requests

# Upload image
with open('sample.png', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:5000/intensity', files=files)
    print(response.json())
```

#### Example Response
```json
{
  "average_intensity": 127.45,
  "filename": "sample.png",
  "image_size": [800, 600],
  "original_mode": "RGB",
  "pixel_count": 480000
}
```

## Development Notes

### Image Intensity Calculation Method

The average intensity is calculated using the following approach:

1. **Format Validation**: Verify the uploaded file is in PNG format
2. **Grayscale Conversion**: Convert the image to grayscale (L mode) if not already
3. **Numerical Processing**: Convert image data to NumPy array
4. **Average Calculation**: Compute the mean of all pixel values
5. **Result**: Return floating-point intensity value (0.0 = black, 255.0 = white)

### Error Handling Strategy

- **400 Bad Request**: Invalid input (wrong format, empty file, missing parameters)
- **500 Internal Server Error**: Processing errors or server issues
- **200 OK**: Successful processing with intensity result

### Security Considerations

- Input validation for file types
- File size limitations
- Memory management for large images
- No persistent file storage (processed in memory)

## Project Structure

```
image-intensity-service/
├── src/
│   └── app.py            # Flask application with API endpoints
├── tests/
│   └── test_api.py       # API tests and unit tests
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development and testing dependencies
├── Dockerfile           # Container configuration
├── .dockerignore        # Docker build exclusions
├── .gitignore          # Git ignore patterns
└── README.md           # Project documentation
```

## Future Enhancements

- Support for additional image formats (JPEG, GIF)
- Batch processing capabilities
- Image metadata extraction
- Advanced intensity metrics (histogram analysis)
- Authentication and rate limiting
- Monitoring and logging integration

---

*Project completed with Flask API service and Docker containerization for PNG image intensity calculation.*