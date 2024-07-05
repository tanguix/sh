
# ----------------------------------------- Explanation -----------------------------------------
# flask application object has field for you to add configuration variable just json file style 
# using key pair value manually: app.config["MAIL_SERVER"] = "smtp.fastmail.com"


import os 
from dotenv import load_dotenv

# Load environment variables from .env file
# .env is ignore in .gitignore, automatically hidden in NvimTree(H)
load_dotenv() 


# Email Sender: https://www.youtube.com/watch?v=WOHiGt9Ce3E
# https://www.fastmail.com/pricing/
# right now only setup for email sending config
class Config:
    MAIL_SERVER = 'smtp.fastmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'seekingh09@fastmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')     # fastmail passwd generate: -> Privacy&Security tab -> new app passwd
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    # MAIL_DEFAULT_SENDER = 'your_email@example.com'
    # SECRET_KEY = 'your_secret_key'
