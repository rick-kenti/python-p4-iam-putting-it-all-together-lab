# testing/conftest.py
import pytest
from sqlalchemy import text
from app import create_app
from config import db as _db

@pytest.fixture(scope="session")
def app():
    """Create application for the tests."""
    _app = create_app(test_config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True
    })
    
    # Create tables
    with _app.app_context():
        _db.create_all()
    
    yield _app
    
    # Clean up
    with _app.app_context():
        _db.drop_all()

@pytest.fixture(scope="function")
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture(scope="function")
def db(app):
    """Create database fixture."""
    with app.app_context():
        yield _db

@pytest.fixture(scope="function")
def session(app, db):
    """Creates a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Bind session to connection
        session = db.session
        session.execute(text("BEGIN"))
        
        yield session
        
        transaction.rollback()
        connection.close()