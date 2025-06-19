from flask import Flask, request, session
from flask_restful import Api, Resource
from flask_migrate import Migrate
from models import db, User, Recipe
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.secret_key = 'secretkey123'

CORS(app, supports_credentials=True)
db.init_app(app)
Migrate(app, db)
api = Api(app)

class Signup(Resource):
    def post(self):
        json = request.get_json()

        username = json.get('username')
        password = json.get('password')
        image_url = json.get('image_url')
        bio = json.get('bio')

        if not username or not password:
            return {'errors': ['Username and password are required.']}, 422

        new_user = User(
            username=username,
            image_url=image_url,
            bio=bio
        )
        new_user.password_hash = password

        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id

            return {
                'id': new_user.id,
                'username': new_user.username,
                'image_url': new_user.image_url,
                'bio': new_user.bio
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username must be unique.']}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }, 200

        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        json = request.get_json()
        username = json.get('username')
        password = json.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 200

        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id')
            return {}, 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        recipes = Recipe.query.all()
        return [
            {
                'id': r.id,
                'title': r.title,
                'instructions': r.instructions,
                'minutes_to_complete': r.minutes_to_complete,
                'user': {
                    'id': r.user.id,
                    'username': r.user.username,
                    'image_url': r.user.image_url,
                    'bio': r.user.bio
                }
            } for r in recipes
        ], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        json = request.get_json()
        title = json.get('title')
        instructions = json.get('instructions')
        minutes = json.get('minutes_to_complete')

        new_recipe = Recipe(
            title=title,
            instructions=instructions,
            minutes_to_complete=minutes,
            user_id=user_id
        )

        try:
            db.session.add(new_recipe)
            db.session.commit()
            return {
                'id': new_recipe.id,
                'title': new_recipe.title,
                'instructions': new_recipe.instructions,
                'minutes_to_complete': new_recipe.minutes_to_complete,
                'user': {
                    'id': new_recipe.user.id,
                    'username': new_recipe.user.username,
                    'image_url': new_recipe.user.image_url,
                    'bio': new_recipe.user.bio
                }
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)