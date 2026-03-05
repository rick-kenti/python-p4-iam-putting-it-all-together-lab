# app.py
from flask import Flask, request, jsonify, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from config import db, bcrypt
from models import User, Recipe

def create_app(test_config=None):
    """Application factory function."""
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = b'a\xdb\xd2\x13\x93\xc1\xe9\x97\xef2\xe3\x004U\xd1Z'
    app.json.compact = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)

    class Signup(Resource):
        def post(self):
            data = request.get_json()
            
            try:
                # Check for required fields
                errors = []
                if not data.get('username'):
                    errors.append("Username required")
                if not data.get('password'):
                    errors.append("Password required")
                
                if errors:
                    return {"errors": errors}, 422
                
                # Check if username already exists
                if User.query.filter_by(username=data.get('username')).first():
                    return {"errors": ["Username already taken"]}, 422
                
                user = User(
                    username=data.get('username'),
                    image_url=data.get('image_url'),
                    bio=data.get('bio')
                )
                user.password_hash = data.get('password')
                
                db.session.add(user)
                db.session.commit()
                
                session['user_id'] = user.id
                
                return user.to_dict(), 201
                
            except ValueError as e:
                return {"errors": [str(e)]}, 422
            except Exception as e:
                return {"errors": [str(e)]}, 422

    class CheckSession(Resource):
        def get(self):
            user_id = session.get('user_id')
            if user_id:
                user = User.query.filter(User.id == user_id).first()
                if user:
                    return user.to_dict(), 200
            return {"errors": ["Unauthorized"]}, 401

    class Login(Resource):
        def post(self):
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {"errors": ["Username and password required"]}, 401
            
            user = User.query.filter(User.username == username).first()
            
            if user and user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
            
            return {"errors": ["Invalid username or password"]}, 401

    class Logout(Resource):
        def delete(self):
            if session.get('user_id'):
                session.pop('user_id')
                return {}, 204
            return {"errors": ["Unauthorized"]}, 401

    class RecipeIndex(Resource):
        def get(self):
            if session.get('user_id'):
                recipes = Recipe.query.all()
                return [recipe.to_dict() for recipe in recipes], 200
            return {"errors": ["Unauthorized"]}, 401
        
        def post(self):
            if session.get('user_id'):
                data = request.get_json()
                
                try:
                    # Validate required fields
                    errors = []
                    if not data.get('title'):
                        errors.append("Title must not be empty")
                    if not data.get('instructions'):
                        errors.append("Instructions required")
                    elif len(data.get('instructions', '')) < 50:
                        errors.append("Instructions must be at least 50 characters long")
                    
                    if errors:
                        return {"errors": errors}, 422
                    
                    recipe = Recipe(
                        title=data.get('title'),
                        instructions=data.get('instructions'),
                        minutes_to_complete=data.get('minutes_to_complete'),
                        user_id=session['user_id']
                    )
                    
                    db.session.add(recipe)
                    db.session.commit()
                    
                    return recipe.to_dict(), 201
                    
                except ValueError as e:
                    return {"errors": [str(e)]}, 422
                except Exception as e:
                    return {"errors": [str(e)]}, 422
            
            return {"errors": ["Unauthorized"]}, 401

    api.add_resource(Signup, '/signup')
    api.add_resource(CheckSession, '/check_session')
    api.add_resource(Login, '/login')
    api.add_resource(Logout, '/logout')
    api.add_resource(RecipeIndex, '/recipes')

    # Create tables if they don't exist (for testing)
    with app.app_context():
        db.create_all()

    return app  # This should be inside create_app function

# For running the app directly
if __name__ == '__main__':
    app = create_app()
    app.run(port=5555, debug=True)