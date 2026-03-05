# testing/app_testing/app_test.py
import pytest
from faker import Faker
from random import randint

from models import db, User, Recipe

# --------------------------
# Test Signup Resource
# --------------------------

class TestSignup:

    def test_creates_users_at_signup(self, client, session):
        """Creates a new user at /signup"""
        session.query(User).delete()
        session.commit()

        response = client.post('/signup', json={
            'username': 'ashketchum',
            'password': 'pikachu',
            'bio': 'I wanna be the very best',
            'image_url': 'https://cdn.vox-cdn.com/uploads/ash.jpg'
        })

        assert response.status_code == 201

        new_user = session.query(User).filter_by(username='ashketchum').first()
        assert new_user
        assert new_user.authenticate('pikachu')
        assert new_user.bio == 'I wanna be the very best'

    def test_422s_invalid_users_at_signup(self, client, session):
        """Returns 422 for invalid signup"""
        session.query(User).delete()
        session.commit()

        response = client.post('/signup', json={
            'password': 'pikachu',
            'bio': 'I wanna be the very best',
            'image_url': 'https://cdn.vox-cdn.com/uploads/ash.jpg'
        })

        assert response.status_code == 422


# --------------------------
# Test Login / Logout / CheckSession
# --------------------------

class TestLoginLogout:

    def setup_user(self, session):
        """Helper to create a user directly in DB"""
        session.query(User).delete()
        session.commit()

        user = User(username='ashketchum', bio='I wanna be the very best')
        user.password_hash = 'pikachu'
        session.add(user)
        session.commit()
        return user

    def test_logs_in_successfully(self, client, session):
        self.setup_user(session)

        response = client.post('/login', json={
            'username': 'ashketchum',
            'password': 'pikachu'
        })

        assert response.status_code == 200
        with client.session_transaction() as s:
            assert s['user_id'] == session.query(User).filter_by(username='ashketchum').first().id

    def test_login_fails_wrong_credentials(self, client):
        response = client.post('/login', json={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        assert response.status_code == 401

    def test_logout_clears_session(self, client, session):
        user = self.setup_user(session)

        client.post('/login', json={'username': 'ashketchum', 'password': 'pikachu'})
        client.delete('/logout')

        with client.session_transaction() as s:
            assert not s.get('user_id')

    def test_check_session_returns_user_json(self, client, session):
        user = self.setup_user(session)

        client.post('/login', json={'username': 'ashketchum', 'password': 'pikachu'})
        response = client.get('/check_session')
        json_data = response.get_json()

        assert json_data['username'] == 'ashketchum'

    def test_check_session_unauthorized(self, client):
        response = client.get('/check_session')
        assert response.status_code == 401


# --------------------------
# Test Recipe Resource
# --------------------------

class TestRecipe:

    def setup_user_with_recipes(self, session):
        """Helper to create user + recipes"""
        session.query(Recipe).delete()
        session.query(User).delete()
        session.commit()

        fake = Faker()
        user = User(username='Slagathor', bio=fake.paragraph())
        user.password_hash = 'secret'
        session.add(user)

        recipes = []
        for _ in range(5):
            recipe = Recipe(
                title=fake.sentence(),
                instructions=fake.paragraph(nb_sentences=5),
                minutes_to_complete=randint(10, 60)
            )
            recipe.user = user
            recipes.append(recipe)
        session.add_all(recipes)
        session.commit()
        return user

    def test_lists_recipes_for_user(self, client, session):
        user = self.setup_user_with_recipes(session)

        client.post('/login', json={'username': 'Slagathor', 'password': 'secret'})
        response = client.get('/recipes')
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 5

    def test_creates_recipe(self, client, session):
        user = self.setup_user_with_recipes(session)

        client.post('/login', json={'username': 'Slagathor', 'password': 'secret'})
        response = client.post('/recipes', json={
            'title': 'New Recipe',
            'instructions': 'X' * 100,  # Force 100 characters to ensure it's long enough
            'minutes_to_complete': 30
        })

        assert response.status_code == 201
        recipe = session.query(Recipe).filter_by(title='New Recipe').first()
        assert recipe is not None

    def test_unauthorized_recipe_access(self, client):
        response = client.get('/recipes')
        assert response.status_code == 401