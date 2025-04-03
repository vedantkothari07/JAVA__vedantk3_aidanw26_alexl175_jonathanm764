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

    # Hash the password before storing
    hashed_password = generate_password_hash(password, method='sha256')

    # Insert new user into DB
    users.insert_one({"username": username, "password": hashed_password})

    return True

# Function to log in an existing user
def login(username, password):
    # Find the user by username
    user = users.find_one({"username": username})

    if user and check_password_hash(user['password'], password):
        return True
    else:
        return False
