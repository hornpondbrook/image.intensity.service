import pytest
import sys
import os
import io
from PIL import Image
import numpy as np

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app, calculate_average_intensity

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_test_png(width=100, height=100, intensity=128):
    """Create a test PNG image with specified intensity."""
    # Create a grayscale image with uniform intensity
    img_array = np.full((height, width), intensity, dtype=np.uint8)
    img = Image.fromarray(img_array, mode='L')
    
    # Save to bytes buffer as PNG
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def test_intensity_calculation():
    """Test the intensity calculation function directly."""
    # Test with known intensity
    test_intensity = 100
    img_buffer = create_test_png(50, 50, test_intensity)
    
    result = calculate_average_intensity(img_buffer.getvalue())
    
    assert abs(result['average_intensity'] - test_intensity) < 1.0
    assert result['image_size'] == [50, 50]
    assert result['pixel_count'] == 2500

def test_intensity_endpoint_success(client):
    """Test successful image upload and intensity calculation."""
    # Create test image
    img_buffer = create_test_png(100, 100, 150)
    
    # Upload image
    response = client.post('/intensity', data={
        'image': (img_buffer, 'test.png')
    })
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'average_intensity' in data
    assert 'image_size' in data
    assert 'filename' in data
    assert data['filename'] == 'test.png'

def test_intensity_endpoint_no_file(client):
    """Test endpoint with no file uploaded."""
    response = client.post('/intensity')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_intensity_endpoint_empty_file(client):
    """Test endpoint with empty file."""
    response = client.post('/intensity', data={
        'image': (io.BytesIO(b''), 'empty.png')
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_intensity_endpoint_non_png(client):
    """Test endpoint with non-PNG file."""
    # Create a simple JPEG-like buffer (this will fail PNG validation)
    fake_jpeg = io.BytesIO(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
    
    response = client.post('/intensity', data={
        'image': (fake_jpeg, 'test.jpg')
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_404_endpoint(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent')
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'available_endpoints' in data

def test_extreme_intensities():
    """Test with extreme intensity values (black and white)."""
    # Test pure black (0)
    black_img = create_test_png(10, 10, 0)
    result = calculate_average_intensity(black_img.getvalue())
    assert result['average_intensity'] == 0.0
    
    # Test pure white (255)
    white_img = create_test_png(10, 10, 255)
    result = calculate_average_intensity(white_img.getvalue())
    assert result['average_intensity'] == 255.0

if __name__ == '__main__':
    pytest.main([__file__])