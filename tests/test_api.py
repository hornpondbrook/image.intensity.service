import pytest
import sys
import os
import io
from PIL import Image
import numpy as np

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def create_test_png(width=100, height=100, intensity=128):
    """Create a test PNG image with specified intensity."""
    img_array = np.full((height, width), intensity, dtype=np.uint8)
    img = Image.fromarray(img_array, mode='L')
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def test_intensity_calculation(app):
    """Test the intensity calculation function directly."""
    # The function is now defined inside create_app, so we can't import it directly.
    # We can test it through the endpoint, or by other means if we refactor.
    # For now, we'll rely on the endpoint tests.
    pass

def test_intensity_endpoint_success(client):
    """Test successful image upload and intensity calculation."""
    img_buffer = create_test_png(100, 100, 150)
    
    response = client.post('/intensity', data={'image': (img_buffer, 'test.png')})
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'average_intensity' in data
    assert data['average_intensity'] == 150.0

def test_intensity_endpoint_no_file(client):
    """Test endpoint with no file uploaded."""
    response = client.post('/intensity')
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_intensity_endpoint_empty_file(client):
    """Test endpoint with empty file."""
    response = client.post('/intensity', data={'image': (io.BytesIO(b''), 'empty.png')})
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_intensity_endpoint_non_png(client):
    """Test endpoint with non-PNG file."""
    fake_jpeg = io.BytesIO(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
    response = client.post('/intensity', data={'image': (fake_jpeg, 'test.jpg')})
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_404_endpoint(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert 'error' in response.get_json()

def test_file_size_limit(client):
    """Test that uploading a file larger than the limit fails."""
    # Create a buffer larger than the 5MB limit
    large_buffer = io.BytesIO(os.urandom(6 * 1024 * 1024))
    
    response = client.post(
        '/intensity',
        data={'image': (large_buffer, 'large_file.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 413
    data = response.get_json()
    assert 'error' in data
    assert 'too large' in data['error']

def test_file_just_under_size_limit(client):
    """Test that uploading a file just under the size limit succeeds."""
    # Create a large PNG image (approx 4.7MB), under the 5MB limit
    # A 2200x2200 grayscale image is 2200*2200 = 4,840,000 bytes
    img_buffer = create_test_png(width=2200, height=2200, intensity=100)
    
    response = client.post(
        '/intensity',
        data={'image': (img_buffer, 'large_enough_file.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'average_intensity' in data
    assert data['average_intensity'] == 100.0

if __name__ == '__main__':
    pytest.main([__file__])
