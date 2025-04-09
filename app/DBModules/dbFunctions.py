import csv
from pymongo import MongoClient, errors

############################# Build Database #############################

MONGO_URL = "mongodb+srv://alexl175:4Kqgfoufp7qErYSA@cluster0.pvbrpxs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["userdb"]
users = db["users"]
obesity_records = db["obesity_records"]

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

'''
def import_obesity_csv(csv_path: str = "ObesityDataSet_raw_and_data_sinthetic.csv"):
    docs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            docs.append({
                "demographics": {
                    "age":        float(row["Age"]),
                    "gender":     row["Gender"],
                    "height_m":   float(row["Height"]),
                    "weight_kg":  float(row["Weight"]),
                },
                "lifestyle": {
                    "caloric_beverages": row["CALC"],                
                    "high_calorie_food":  row["FAVC"].lower() == "yes",
                    "veggie_freq":        float(row["FCVC"]), 
                    "meals_per_day":      float(row["NCP"]),
                    "calorie_monitor":    row["SCC"].lower() == "yes",
                    "smokes":             row["SMOKE"].lower() == "yes",
                    "water_litres":       float(row["CH2O"]),
                    "physical_activity":  float(row["FAF"]),         
                    "tech_use":           float(row["TUE"]),         
                    "between_meals":      row["CAEC"],
                    "transport":          row["MTRANS"],
                },
                "family_history_overweight": row["family_history_with_overweight"].lower() == "yes",
                "target": row["NObeyesdad"],                        
            })
    if docs:
        obesity_records.insert_many(docs)
    print("inserted")
'''

def import_states(csv_path: str = "LakeCounty_Health_-6177935595181947989.csv"):
    docs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            docs.append({
                "state": row["NAME"],
                "obesity" : float(row["Obesity"]),
                "area" : float(row["Shape__Area"]),
                "length" : float(row["Shape__Length"]),
            })
    if docs:
        state_records.insert_many(docs)
        print("inserted")


