#import sqlite3
from pymongo import MongoClient, errors

#DB_FILE="America.db"

############################# Build Database #############################
'''
def initDB():
    db = sqlite3.connect(DB_FILE) # Open/Create database file
    c = db.cursor()
    
    c.execute("""
              CREATE TABLE IF NOT EXISTS users (
              username TEXT, 
              password TEXT
              )
              """) # creates login database
    
    db.commit() #save changes
    db.close()  #close database

############################# User Database Interations #############################

def addUser(username, password):
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    query = "INSERT INTO users (username, password) VALUES (?, ?)"
    c.execute(query, (username, password))
    db.commit()
    db.close()

def checkUser(username, password):
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username, )) # Passing username as a single element tuple
    user = c.fetchone() # Checks to see if any rows were returned
    if user is not None:
        if password == user[1]:
            return True
    return False

def registerUser(username, password):
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username, )) # Passing username as a single element tuple
    user = c.fetchone() # Checks to see if any rows were returned
    if user is None:
        addUser(username, password)
        return True
    return False
'''
MONGO_URL = "mongodb+srv://alexl175:4Kqgfoufp7qErYSA@cluster0.pvbrpxs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["userdb"]
users = db["users"]

def initDB():
    try: 
        users.create_index("username", unique=True)
    except errors.OperationFailure:
        pass # if username already exists 

def addUser(username, password):
    users.insert_one({"username": username, "password": password})

def checkUser(username, password):
    doc = users.find_one({"username": username})   
    if not doc:                                
        return False
    return doc["password"] == password    

def registerUser(username, password):
    if users.find_one({"username": username}):
        return False              # username taken
    addUser(username, password)
    return True