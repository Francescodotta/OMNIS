from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity, create_access_token
from app import app
from app.views.auth import register_user, login_user, change_password_views, get_user_views, delete_user_views 
from app import blacklist
import logging 

bp = Blueprint('auth', __name__)
logger = logging.getLogger("custom_info_logger")


# inserire le routes qua
@app.route('/api/register', methods=['POST'])
@jwt_required()
def register():
    username = get_jwt()["sub"]
    result, status_code = register_user(request.json, username)
    return jsonify(result), status_code


@app.route('/api/login', methods=['POST'])
def login():
    logger.info("Login request of username: {}".format(request.json['username']))
    data = request.get_json()
    result, status_code = login_user(data)
    logger.info("User {} logged in".format(data['username']))
    print(result)
    return jsonify(result), status_code

@app.route('/api/user/<username>', methods=['DELETE'])
@jwt_required()
def delete_user(username):
    admin_username = get_jwt()["sub"]
    result, status_code = delete_user_views(username, admin_username)
    return jsonify(result), status_code

@app.route('/api/user/password', methods=['POST'])
@jwt_required()
def change_password():
    username = get_jwt()["sub"]
    result, status_code = change_password_views(request.json, username)
    return jsonify(result), status_code

@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    # implementa il logout
    jti = get_jwt()["jti"]
    blacklist.add(jti)
    logger.info("User {} logged out".format(get_jwt()["sub"]))
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # implementa il refresh
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token), 200

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    username = get_jwt_identity()
    users, status_code = get_user_views(username)
    return jsonify(users), status_code