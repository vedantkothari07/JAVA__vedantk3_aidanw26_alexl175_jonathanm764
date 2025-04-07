from pymongo import MongoClient, errors

############################# Build Database #############################

MONGO_URL = "mongodb+srv://alexl175:@cluster0.pvbrpxs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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