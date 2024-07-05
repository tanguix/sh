
from app.database import db                     # db is a created mongoDB object in database.py 
from app.logger import logger                   # same for logger
from flask import current_app, url_for
from flask_mailman import EmailMessage
from itsdangerous import URLSafeTimedSerializer
# from bson import ObjectId


# User class (object)
class User:
    def __init__(self, username, password, role, authToken=None):     # initialize with 3 required parameters
        self.username = username
        self.password = password
        self.role = role
        self.authToken = authToken

    # method for assigning roles to users when they register new account 
    # later, write a more complex way to assign role (such as email verification)
    # best practice: you have to pass a database or collection to functions as parameter, but for sensitive information 
    # like creating a user, let's fix its collections right now, just need to make sure the collection name is correct "users"
    def save_user(self):
        try:
            db.users.insert_one({                                       # insert into mongoDB collection fixed name "users"
                "username": self.username,
                "password": self.password,
                "role": self.role,                                      # with assigned role
                "authToken": self.authToken 
            })
            return True

        except Exception as e:                                          # handle exception
            logger.error(f"Error saving user: {e}")
            return False

    # staticmethod is a decorator that tells you the below method are just utility function
    # they are not going to modify the internal variables within the class, they just perform task
    @staticmethod
    def get_all_users():
        return list(db.users.find({}, {'_id': 0, 'username': 1, 'password': 1}))    # return list of users


    @staticmethod
    def find_by_username(username):
        user = db.users.find_one({"username": username})
        if user:
            user['_id'] = str(user['_id'])                  # id in mongoDB are bson type, convert for send
        return user


    @staticmethod
    def update_token(username, new_auth_token):             # takes in username and new_auth_token
        result = db.users.update_one(                       # when login, update token in database
            {"username": username},
            {"$set": {"authToken": new_auth_token}}
        )
        return result.modified_count > 0


    @staticmethod
    def find_by_token(authToken):
        user = db.users.find_one({"authToken": authToken})
        if user:
            user['_id'] = str(user['_id'])                  # id in mongoDB are bson type, convert for send
        return user                                         # match one user with "authToken"



    # later set up the clickable approval and decline email in flask 
    # backend solely could handle all these, frontend just need to collect data
    # remove sasuke way of assigning role
    @staticmethod 
    def send_email(username):
        msg = EmailMessage(
            "New Registration",
            f"{username} is registering an account",
            "seekingh09@fastmail.com",
            ["spacelion121319@gmail.com"]
        )
        try: 
            msg.send()
            print("Email sent...")
        except Exception as e:
            # logger.error(f"Failed to send email: {e}")
            print(f"Failed to send email: {e}")

        # serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        # token = serializer.dumps(user_email, salt='email-confirm-salt')
        # confirm_url = url_for('auth.verify_email', token=token, _external=True)
        # subject = "Please verify your email"
        # body = f"Hi {username}, please click the link to verify your email: {confirm_url}"
        # msg = EmailMessage(subject, body, to=[user_email])
        # msg.send()


