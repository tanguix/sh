
from flask import Flask
from flask_cors import CORS                     # enable frontend backend connection, API request
from app.config import Config                   # correct way of importing config.py file
from flask_mailman import Mail                  # import for creating the mail object


# create flask object and enable request from all origins
# also enable routes from other blueprint
def create_app():
    # create app
    app = Flask(__name__)

    # enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})  # enable all routes

    # appiled config to flask app object 
    # access individual config with key: mail_server = current_app.config["MAIL_SERVER"]
    app.config.from_object(Config)

    # create Mail() object
    mail = Mail()

    # initialize the mail object with the app
    mail.init_app(app)

    # in order to access the configuration setting in config.py 
    # in flask you have to create an app_context, 
    # only program running within app_context can access to configuration
    with app.app_context():
        # register blueprint 
        register_all_blueprints(app)


    return app



def register_all_blueprints(app):

    # import all the routes 
    from app.auth.routes import auth_bp
    from app.upload.routes import upload_bp
    from app.search.routes import search_bp
    from app.excel.routes import excel_bp
    from app.extra.routes import extra_bp

    # "register_blueprint()" is a built-in function in flask, 
    # "register_all_blueprints()" is what I defined
    app.register_blueprint(auth_bp, url_prefix='/auth')           # url_prefix is for avoiding route conflict
    app.register_blueprint(upload_bp, url_prefix='/upload')       # with prefix, route will be localhost:5000/auth/login
    app.register_blueprint(search_bp, url_prefix='/search')       # without prefix, localhost:5000/login
    app.register_blueprint(excel_bp, url_prefix='/excel')
    app.register_blueprint(extra_bp, url_prefix='/extra')




