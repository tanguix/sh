
from pymongo import MongoClient

# this file right now is only for connecting database
client = MongoClient('localhost', 27017)
db = client.flask_database  # use this temp

