# testing/models_testing/user_test.py
import pytest
from models import db, User
from sqlalchemy.exc import IntegrityError

class TestUser:
    def test_creates_user(self, client, app):
        """Test creating a user via signup route."""
        # Clean up any existing user
        with app.app_context():
            User.query.filter_by(username="ashketchum").delete()
            db.session.commit()
            
        response = client.post("/signup", json={
            "username": "ashketchum",
            "password": "pikachu",
            "bio": "I wanna be the very best...",
            "image_url": "https://example.com/image.jpg"
        })
        assert response.status_code == 201

        with app.app_context():
            user = User.query.filter_by(username="ashketchum").first()
            assert user is not None
            assert user.authenticate("pikachu")

    def test_requires_username(self, app):
        """Ensure username is required."""
        with app.app_context():
            # Try to create user without username - should raise ValueError from validation
            with pytest.raises(ValueError, match="Username must not be empty"):
                User(
                    username=None,
                    image_url="http://example.com",
                    bio="Test bio"
                )

    def test_unique_username(self, app):
        """Ensure usernames are unique."""
        with app.app_context():
            # Clean up any existing user
            User.query.filter_by(username="Ben").delete()
            db.session.commit()
            
            # Create first user with password
            u1 = User(username="Ben")
            u1.password_hash = "password123"
            db.session.add(u1)
            db.session.commit()
            
            # Try to create second user with same username - should raise IntegrityError at commit
            u2 = User(username="Ben")
            u2.password_hash = "password456"
            db.session.add(u2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()