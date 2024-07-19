
# ----------------------------------------- Explanation -----------------------------------------
# flask application object has field for you to add configuration variable just json file style 
# using key pair value manually: app.config["MAIL_SERVER"] = "smtp.fastmail.com"


import os 
from dotenv import load_dotenv
import socket

# Load environment variables from .env file
# .env is ignore in .gitignore, automatically hidden in NvimTree(H)
load_dotenv() 



def get_local_ip():
    try:
        # 1) socket.socket() create a new socket object 
        # 2) socket.AF_INET + SOCK_RGRAM (UDP IPv4), together they are ask OS
        #    - if I were to send a UDP packet to this address (8.8.8.8) google's public address, 
        #    - which of my network interfaces and IP addresses would you use? 
        # so we will not the localhost value of our machine in the network, we aren't actually creating connection
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost if unable to determine IP



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


    # Dynamically set the backend URL
    LOCAL_IP = get_local_ip()
    PORT = 5000                                         # default flask port
    BACKEND_LOCAL_URL = f'http://{LOCAL_IP}:{PORT}'


