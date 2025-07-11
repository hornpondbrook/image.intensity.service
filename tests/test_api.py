import pytest
import sys
import os
import io
from PIL import Image
import numpy as np
from unittest.mock import patch
import fakeredis

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import create_app, get_config_by_name

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Patch redis.Redis with fakeredis.FakeRedis before creating the app
    with patch('redis.Redis', fakeredis.FakeRedis):
        app = create_app()
        app.config.from_object(get_config_by_name('testing'))
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

def create_test_jpeg(width=100, height=100, intensity=128):
    """Create a test JPEG image with specified intensity."""
    img_array = np.full((height, width), intensity, dtype=np.uint8)
    img = Image.fromarray(img_array, mode='L')
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    return img_buffer

def test_intensity_calculation(app):
    """Test the intensity calculation function directly."""
    # The function is now defined inside create_app, so we can't import it directly.
    # We can test it through the endpoint, or by other means if we refactor.
    # For now, we'll rely on the endpoint tests.
    pass

def test_intensity_endpoint_success_png(client):
    """Test successful PNG image upload and intensity calculation."""
    img_buffer = create_test_png(100, 100, 150)
    
    response = client.post('/intensity', data={'image': (img_buffer, 'test.png')})
    
    assert response.status_code == 200
    assert 'X-Request-ID' in response.headers
    data = response.get_json()
    assert 'average_intensity' in data
    assert data['average_intensity'] == 150.0
    assert 'request_id' in data

def test_intensity_endpoint_success_jpeg(client):
    """Test successful JPEG image upload and intensity calculation."""
    img_buffer = create_test_jpeg(100, 100, 180)
    
    response = client.post('/intensity', data={'image': (img_buffer, 'test.jpg')})
    
    assert response.status_code == 200
    assert 'X-Request-ID' in response.headers
    data = response.get_json()
    assert 'average_intensity' in data
    # JPEG compression can cause slight variations in intensity
    assert abs(data['average_intensity'] - 180.0) < 2.0
    assert 'request_id' in data

def test_caching_logic(client):
    """Test that caching works as expected."""
    # 1. First request: Cache Miss
    response_miss = client.post('/intensity', data={'image': (create_test_png(50, 50, 100), 'test_cache.png')})
    assert response_miss.status_code == 200
    assert response_miss.headers['X-Cache'] == 'miss'
    data_miss = response_miss.get_json()
    assert data_miss['average_intensity'] == 100.0

    # 2. Second request: Cache Hit
    response_hit = client.post('/intensity', data={'image': (create_test_png(50, 50, 100), 'test_cache.png')})
    assert response_hit.status_code == 200
    assert response_hit.headers['X-Cache'] == 'hit'
    data_hit = response_hit.get_json()
    assert data_hit['average_intensity'] == 100.0

    # 3. Ensure the data is the same (except for request_id and duration)
    data_miss.pop('request_id', None)
    data_miss.pop('duration_ms', None)
    data_hit.pop('request_id', None)
    data_hit.pop('duration_ms', None)
    assert data_miss == data_hit

def test_intensity_endpoint_no_file(client):
    """Test endpoint with no file uploaded."""
    response = client.post('/intensity')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data

def test_intensity_endpoint_empty_file(client):
    """Test endpoint with empty file."""
    response = client.post('/intensity', data={'image': (io.BytesIO(b''), 'empty.png')})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data

def test_intensity_endpoint_unsupported_format(client):
    """Test endpoint with an unsupported image format (GIF)."""
    fake_gif = io.BytesIO(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
    response = client.post('/intensity', data={'image': (fake_gif, 'test.gif')})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data

def test_404_endpoint(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data

def test_file_size_limit(client):
    """Test that uploading a file larger than the limit fails."""
    # TestingConfig sets the limit to 500 KB
    large_buffer = io.BytesIO(os.urandom(501 * 1024))
    
    response = client.post(
        '/intensity',
        data={'image': (large_buffer, 'large_file.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 413
    data = response.get_json()
    assert 'error' in data
    assert 'too large' in data['error']
    assert 'request_id' in data

def test_file_just_under_size_limit(client):
    """Test that uploading a file just under the size limit succeeds."""
    # TestingConfig sets the limit to 500 KB
    # Create a PNG just under the limit (e.g., 499 KB)
    # A 700x700 grayscale image is 490,000 bytes
    img_buffer = create_test_png(width=700, height=700, intensity=100)
    
    response = client.post(
        '/intensity',
        data={'image': (img_buffer, 'large_enough_file.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    assert 'X-Request-ID' in response.headers
    data = response.get_json()
    assert 'average_intensity' in data
    assert data['average_intensity'] == 100.0
def test_generic_http_exception_handler(client):
    """Test the generic HTTPException handler for a 405 Method Not Allowed error."""
    response = client.get('/intensity')  # Send GET to a POST-only endpoint
    
    assert response.status_code == 405
    data = response.get_json()
    assert data['code'] == 405
    assert data['name'] == "Method Not Allowed"
    assert 'description' in data
    assert 'request_id' in data

    assert 'request_id' in data
    
if __name__ == '__main__':
    pytest.main([__file__])
