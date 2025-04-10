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

def storeUser(username, user_data):
    users.update_one(
        {"username": username},
        {
            "$set": {
                "demographics": {
                    "age": user_data["age"],
                    "gender": user_data["gender"],
                    "height_m": user_data["height_m"],
                    "weight_kg":user_data["weight_kg"]
                },
                "lifestyle": {
                    "caloric_beverages": user_data["caloric_beverages"],
                    "high_calorie_food": user_data["high_calorie_food"],
                    "veggie_freq": user_data["veggie_freq"],
                    "meals_per_day": user_data["meals_per_day"],
                    "calorie_monitor":user_data["calorie_monitor"],
                    "smokes":user_data["smokes"],
                    "water_litres": user_data["water_litres"],
                    "physical_activity": user_data["physical_activity"],
                    "tech_use": user_data["tech_use"],
                    "between_meals": user_data["between_meals"],
                    "transport": user_data["transport"]
                },
                "family_history_overweight":user_data["family_history_overweight"]
            }
        }
    )

def getUser(username):
    return users.find_one({"username": username})

def computeRisk(user_doc):
    if not user_doc:
        return None, None

    demographics = user_doc.get("demographics", {})
    lifestyle= user_doc.get("lifestyle", {})

    age = demographics.get("age",0)
    gender = demographics.get("gender", "")
    height_m = demographics.get("height_m", 0)
    weight_kg = demographics.get("weight_kg", 0)

    bmi = 0
    if height_m > 0:
        bmi = weight_kg / (height_m ** 2)

    family_history = user_doc.get("family_history_overweight", False)
    caloric_beverages = lifestyle.get("caloric_beverages", "").lower()
    high_calorie_food = lifestyle.get("high_calorie_food", False)
    veggie_freq = lifestyle.get("veggie_freq",0)
    meals_per_day = lifestyle.get("meals_per_day", 0)
    calorie_monitor = lifestyle.get("calorie_monitor", False)
    smokes = lifestyle.get("smokes", False)
    water_litres = lifestyle.get("water_litres", 0)
    physical_activity = lifestyle.get("physical_activity", 0)
    tech_use = lifestyle.get("tech_use", 0)
    between_meals = lifestyle.get("between_meals", "").lower()
    transport = lifestyle.get("transport", "").lower()

    points = 0

    if bmi < 25:
        points += 0
    elif bmi < 30:
        points += 2
    elif bmi < 35:
        points += 4
    elif bmi < 40:
        points += 6
    else:
        points += 8

    if age >= 40:
        points += 2
    elif age >= 30:
        points += 1

    if gender.lower() == "male":
        points += 1

    if family_history:
        points += 3

    if high_calorie_food:
        points += 2

    if veggie_freq < 1:
        points += 2
    elif veggie_freq < 2:
        points += 1

    if meals_per_day < 3:
        points += 1

    if between_meals == "always":
        points += 2
    elif between_meals == "frequently":
        points += 1

    if water_litres < 1:
        points += 2
    elif water_litres < 2:
        points += 1

    if calorie_monitor:
        points -= 1

    if physical_activity <= 0:
        points += 3

    if tech_use > 4:
        points += 2
    elif tech_use > 2:
        points += 1

    if caloric_beverages == "frequently":
        points += 2
    elif caloric_beverages == "sometimes":
        points += 1

    if transport not in ["walking", "bike"]:
        points += 1

    if points <= 5:
        category = "low Risk"
    elif points <= 12:
        category = "Medium Risk"
    else:
        category = "HIGH Risk"

    return points, category

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
'''
def import_years(csv_path: str = "obesity-cleaned.csv"):
    docs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            docs.append({
                "country": row["Country"],
                "year" : row["Year"],
                "obesity" : row["Obesity (%)"],
                #one country, one year, avg range of obesity across year for given country, 
            })
    if docs:
        state_records.insert_many(docs)
        print("inserted")
