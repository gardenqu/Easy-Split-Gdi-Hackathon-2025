import pytest
from app import app as flask_app 
from config import TestingConfig
from extensions import db
from models import User, Receipt, BillSplit
from unittest.mock import MagicMock, patch
from datetime import datetime
import io
from app import app, db

@pytest.fixture(scope='session')
def app():
    # Configure the app for testing
    flask_app.config.from_object(TestingConfig)
    
    with flask_app.app_context():
        # Create tables in database
        db.create_all()
        yield flask_app
        # Drop tables after the session is done
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def session(app):
    with app.app_context():
        # Clean up database for each test function
        db.session.remove()
        db.drop_all()
        db.create_all()
        db.session.commit()
        return db.session

@pytest.fixture
def mock_user():
    """Create a real test user in the database"""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com'
            )
            # user set_password method
            if hasattr(user, 'set_password'):
                user.set_password('testpassword')
            db.session.add(user)
            db.session.commit()
        return user

@pytest.fixture
def auth_headers(mock_user):
    """Provides valid authentication headers with a real JWT token"""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        access_token = create_access_token(identity=str(mock_user.id))
        return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def mock_db_operations(mocker):
    """Mocks database session commits/rollbacks for routes that don't need real DB"""
    mocker.patch('app.db.session.add')
    mocker.patch('app.db.session.commit')
    mocker.patch('app.db.session.rollback')

@pytest.fixture
def mock_extract_data(mocker):
    """Mocks the external receipt data extraction function."""
    return mocker.patch(
        'app.extract_receipt_data', 
        return_value={'store_name': 'MockStore', 'total': 12.34, 'subtotal': 10.00, 'tax': 2.34, 'date': '2025-01-01'}
    )

@pytest.fixture
def mock_image_io(mocker):
    """Mocks PIL/Image saving and the temporary file operations."""
    mock_image_open = mocker.patch('PIL.Image.open')
    mock_image_instance = mock_image_open.return_value
    mock_image_instance.convert.return_value.save = MagicMock()
    mocker.patch('os.path.join', return_value='mocked_file_path.jpg')
    mocker.patch('app.datetime', MagicMock(utcnow=MagicMock(return_value=datetime(2025, 1, 1))))
    return mock_image_open
