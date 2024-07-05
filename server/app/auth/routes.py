
from flask import Blueprint, request, jsonify
from app.auth.models import User


# 'auth' here is the name for identify the Blueprint internally for flask
# just for identification, no further purpose, so basically you name it anything
auth_bp = Blueprint('auth', __name__)


# ----------------------------------------------- Register -----------------------------------------------
# just for returning all user, later for login/logout status use
@auth_bp.route("/api/users", methods=['GET'])
def get_users():
    users_metadata = User.get_all_users()   # User object, and its staticmethod
    return jsonify(users_metadata), 200



# it gets information from frontend, but this POST method specified is with respect to mongoDB database
@auth_bp.route("/api/register", methods=['POST'])
def register_users():
    data = request.json     # receive data from frontend
    if not data:            # check data availability
        return jsonify({"error": "Invalid data format"}), 400

    # get all data from their keys
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    authToken = data.get('authToken')

    # check if username or password is empty (thought make them required field in frontend)
    # just double check
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # create new User object
    user = User(username, password, role, authToken)
    # initiate staticmethod for inserting users
    success = user.save_user()

    # send email to notify myself that a new user is register
    User.send_email(username)

    # check if succeed
    if success:
        return jsonify({"success": True}), 201
    else:
        return jsonify({"error": "Registration failed"}), 500



# ----------------------------------------------- Login -----------------------------------------------
# receive a username, and map it to the database, if found then return that username 
# else return None (nothing)
@auth_bp.route('/api/match', methods=['GET'])
def match_username():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username not provided"}), 400

    # User object staticmethod
    user = User.find_by_username(username)
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"username": None}), 200



# update the token whenever a user login to the system 
# frontend will generate a token when that event happen, and send it back
@auth_bp.route('/api/update_authtoken', methods=['POST'])
def update_authtoken():
    # check the token data, as well as the user
    data = request.json
    if not data or 'username' not in data or 'authToken' not in data:
        return jsonify({"error": "Invalid data format"}), 400

    # check username & token
    username = data['username']
    new_auth_token = data['authToken']
    success = User.update_token(username, new_auth_token)

    if success:
        return jsonify({"message": "User info updated successfully"}), 200
    else:
        return jsonify({"error": "Update failed"}), 500



# another match function, but this time user token to match, because in real world application
# this route is for hook usage in sveltekit, hook.server.ts
# you use cookies to match user, which is more secure, less expose your username and password
@auth_bp.route('/api/match_token', methods=['GET'])
def match_token():
    auth_token = request.args.get('authToken')
    if not auth_token:
        return jsonify({"error": "session not provided"}), 400 

    # match user by token
    user = User.find_by_token(auth_token)
    # print("CHECK FOR TOKEN MATCHING:", user)
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"auth_token": None}), 200




