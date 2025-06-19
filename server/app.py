#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        bio = data.get("bio")
        image_url = data.get("image_url")

        if not username or not password:
            return {"errors": ["Username and password required."]}, 422

        try:
            new_user = User(
                username=username,
                bio=bio,
                image_url=image_url,
            )
            new_user.password_hash = password

            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id

            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio,
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username must be unique."]}, 422

class CheckSession(Resource):
    
    def get(self):
        user_id = session.get("user_id")

        if user_id:
            user = db.session.get(User, user_id)  # 🆕 Updated here
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio,
                }, 200

        return {"error": "Unauthorized"}, 401

class Login(Resource):
    
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id

            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio,
            }, 200

        return {"error": "Unauthorized"}, 401


class Logout(Resource):
    
    def delete(self):
        if session.get("user_id"):
            session["user_id"] = None
            return {}, 204  # No Content
        return {"error": "Unauthorized"}, 401


class RecipeIndex(Resource):
    
    def get(self):
        if not session.get("user_id"):
            return {"error": "Unauthorized"}, 401

        recipes = Recipe.query.all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "instructions": r.instructions,
                "minutes_to_complete": r.minutes_to_complete,
                "user": {
                    "id": r.user.id,
                    "username": r.user.username,
                    "image_url": r.user.image_url,
                    "bio": r.user.bio,
                }
            }
            for r in recipes
        ], 200

    def post(self):
        if not session.get("user_id"):
            return {"error": "Unauthorized"}, 401

        data = request.get_json()

        try:
            new_recipe = Recipe(
                title=data.get("title"),
                instructions=data.get("instructions"),
                minutes_to_complete=data.get("minutes_to_complete"),
                user_id=session["user_id"]
            )
            db.session.add(new_recipe)
            db.session.commit()

            return {
                "id": new_recipe.id,
                "title": new_recipe.title,
                "instructions": new_recipe.instructions,
                "minutes_to_complete": new_recipe.minutes_to_complete,
                "user": {
                    "id": new_recipe.user.id,
                    "username": new_recipe.user.username,
                    "image_url": new_recipe.user.image_url,
                    "bio": new_recipe.user.bio,
                }
            }, 201

        except Exception as e:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 422


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)