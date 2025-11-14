import io
import pytest
from PIL import Image
from unittest.mock import patch
from parse_model import extract_receipt_data
from app import app
import os


# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'


@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()


def create_test_image(format="JPEG"):
    """Return an in-memory image file."""
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes


# 1. Missing file test
def test_no_file_provided(client):
    response = client.post('/api/process-receipt')

    assert response.status_code == 400
    assert response.get_json()['error'] == 'No image file provided'


# 2. Empty filename test
def test_empty_filename(client):
    data = {
        'image': (io.BytesIO(b''), '')
    }
    response = client.post('/api/process-receipt', data=data)

    assert response.status_code == 400
    assert response.get_json()['error'] == 'No file selected'


# 3. Unsupported MIME type
def test_unsupported_file_type(client):
    fake_file = io.BytesIO(b'not an image')
    data = {
        'image': (fake_file, 'test.txt')
    }
    response = client.post('/api/process-receipt', data=data)

    assert response.status_code == 415
    assert "Unsupported file type" in response.get_json()['error']


@patch('app.extract_receipt_data')  # Patch where it's imported and used
def test_valid_image(mock_extract, client):
    mock_extract.return_value = {"store": "Walmart", "total": 12.34}

    test_img = create_test_image("JPEG")
    data = {
        'image': (test_img, 'receipt.jpg')
    }

    response = client.post(
        '/api/process-receipt',
        data=data,
        content_type='multipart/form-data'
    )

    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data['success'] is True
    assert json_data['data'] == {"store": "Walmart", "total": 12.34}

    mock_extract.assert_called_once()