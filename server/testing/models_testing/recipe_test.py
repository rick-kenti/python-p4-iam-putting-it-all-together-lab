# testing/models_testing/recipe_test.py
import pytest
from faker import Faker
from random import randint
from models import db, User, Recipe
from sqlalchemy.exc import IntegrityError

fake = Faker()

class TestRecipe:
    def test_create_recipe(self, client, app):
        """Create a recipe for a user."""
        # First, ensure any existing user is cleaned up
        with app.app_context():
            User.query.filter_by(username="Slagathor").delete()
            db.session.commit()
        
        # Sign up
        signup_response = client.post("/signup", json={
            "username": "Slagathor",
            "password": "secret",
            "bio": "Test bio",
            "image_url": "http://example.com/image.jpg"
        })
        assert signup_response.status_code == 201

        # Login
        login_response = client.post("/login", json={
            "username": "Slagathor",
            "password": "secret"
        })
        assert login_response.status_code == 200

        # Create recipe with specific title (not random) for easier testing
        recipe_data = {
            "title": "Test Recipe Title",
            "instructions": "X" * 100,  # Force 100 characters to ensure it's long enough
            "minutes_to_complete": 30
        }
        
        response = client.post("/recipes", json=recipe_data)
        assert response.status_code == 201

        with app.app_context():
            user = User.query.filter_by(username="Slagathor").first()
            recipe = Recipe.query.filter_by(user_id=user.id, title="Test Recipe Title").first()
            assert recipe is not None
            assert recipe.title == "Test Recipe Title"
            assert recipe.minutes_to_complete == 30
            assert len(recipe.instructions) >= 50

    def test_recipe_index_unauthorized(self, client):
        """GET /recipes should 401 if no session."""
        response = client.get("/recipes")
        assert response.status_code == 401

    def test_requires_title(self, app):
        """Ensure recipes require a title."""
        with app.app_context():
            # Create user with password
            user = User(username="Tester")
            user.password_hash = "password123"
            db.session.add(user)
            db.session.commit()

            # Try to create recipe without title - should raise ValueError from validation
            # We need to set title to None explicitly to trigger the validator
            with pytest.raises(ValueError, match="Title must not be empty"):
                recipe = Recipe(
                    user_id=user.id,
                    instructions="This is a very long instruction that should be at least fifty characters long to pass validation.",
                    minutes_to_complete=30
                )
                # Explicitly set title to None to trigger validator
                recipe.title = None
            db.session.rollback()

    def test_requires_min_50_char_instructions(self, app):
        """Instructions must be >= 50 characters."""
        with app.app_context():
            # Create user with password
            user = User(username="Tester2")
            user.password_hash = "password123"
            db.session.add(user)
            db.session.commit()

            # Try to create recipe with short instructions - should raise ValueError from validation
            with pytest.raises(ValueError, match="Instructions must be at least 50 characters long"):
                Recipe(
                    user_id=user.id,
                    title="Short Test",
                    instructions="Too short",
                    minutes_to_complete=30
                )
            db.session.rollback()