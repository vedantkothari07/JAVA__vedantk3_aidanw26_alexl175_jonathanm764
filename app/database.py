from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask_pymongo import PyMongo

uri = "mongodb+srv://Jon_595:wH85NEbxuVV3XH1U@cluster0.7risuh5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.userdb
users = db.users

def register(username, password):
    if users.find_one({"username": username}):
        return {"error": "User already exists!"}


    # Insert new user into DB
    users.insert_one({"username": username, "password": password})

    return True

# Function to log in an existing user, returns true if password matches, returns false otherwise
def login(username, password):
    # Find the user by username
    user = users.find_one({"username": username})
    user2 = users.find_one({"password": password})
    if user == user2:
        return True
    else:
        return False
