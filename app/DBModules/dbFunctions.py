import csv
from pymongo import MongoClient, errors
import numpy as np

############################# Build Database #############################

MONGO_URL = "mongodb+srv://alexl175:4Kqgfoufp7qErYSA@cluster0.pvbrpxs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["userdb"]
users = db["users"]
obesity_records = db["obesity_records"]
year_records = db["year_records"]
state_records = db.state_records

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

def risk_factor_percentages(user_doc):
    #{ "BMI": 26.67, "FAMILY_HISTORY": 20.0, ... }
    #labels = keys, values = dict.values()

    if not user_doc:
        return {}

    pts = {}

    def add(label, n):
        if n > 0:
            pts[label] = pts.get(label, 0) + n

    d = user_doc.get("demographics", {})
    l = user_doc.get("lifestyle", {})

    h, w = d.get("height_m", 0), d.get("weight_kg", 0)
    bmi = w / (h*h) if h else 0
    add("BMI", 0 if bmi < 25 else 2 if bmi < 30 else 4 if bmi < 35 else 6 if bmi < 40 else 8)

    age = d.get("age", 0)
    add("AGE", 2 if age >= 40 else 1 if age >= 30 else 0)

    if d.get("gender", "").lower() == "male":
        add("MALE SEX", 1)

    if user_doc.get("family_history_overweight"):
        add("FAMILY HISTORY", 3)

    if l.get("high_calorie_food"):
        add("HIGH‑CAL FOOD", 2)

    vf = l.get("veggie_freq", 0)
    add("LOW VEGGIES", 2 if vf < 1 else 1 if vf < 2 else 0)

    if l.get("meals_per_day", 0) < 3:
        add("<3 MEALS", 1)

    snack = l.get("between_meals", "").lower()
    add("SNACKING", 2 if snack == "always" else 1 if snack == "frequently" else 0)

    h2o = l.get("water_litres", 0)
    add("LOW WATER", 2 if h2o < 1 else 1 if h2o < 2 else 0)

    if l.get("physical_activity", 0) <= 0:
        add("NO EXERCISE", 3)

    tu = l.get("tech_use", 0)
    add("SCREEN TIME", 2 if tu > 4 else 1 if tu > 2 else 0)

    cb = l.get("caloric_beverages", "").lower()
    add("SUGARY/ALC DRINKS", 2 if cb == "frequently" else 1 if cb == "sometimes" else 0)

    if l.get("transport", "").lower() not in ("walking", "bike"):
        add("INACTIVE TRANSPORT", 1)

    total = sum(pts.values())
    if not total:
        return {}

    return {k: round(v * 100 / total, 2) for k, v in pts.items()}

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
    by_year = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            country = row["Country"]
            year = row["Year"]
            obesity = row["Obesity (%)"]
            sex = row["Sex"].lower()  # male, female, or both sexes

            # gets first num
            main = obesity.split()[0]
            try:
                obesity_val = float(main)
            except ValueError:
                continue

            # make sure we have year
            if year not in by_year:
                by_year[year] = {
                    "year": int(year),
                    "countries": {}
                }

            # make sure we have sub-dict for country
            if country not in by_year[year]["countries"]:
                by_year[year]["countries"][country] = {}

            by_year[year]["countries"][country]["bmi"] = obesity_val

    docs = list(by_year.values())

    if docs:
        year_records.insert_many(docs)
        print("inserted")

def fetch_obesity_data():
    records = year_records.find({}, {"_id": 0})
    all_data = []

    for record in records:
        year = record["year"]
        countries = record["countries"]
        for name, stats in countries.items():
            value = stats.get("obesity%", 0)
            all_data.append({
                "date": f"{year}",
                "name": name,
                "value": value
            })

    return all_data

def get_state_data():
    data = state_records.find({}, {"_id": 0, "state": 1, "obesity": 1})
    # Normalize state name
    result = [{"state": d["state"].strip().lower(), "obesity": d["obesity"]} for d in data]
    return result

def get_user_risk_factors(username):
    user = getUser(username)
    if not user:
        return {}

    # Unpack fields
    demo = user.get("demographics", {})
    life = user.get("lifestyle", {})
    family_history = user.get("family_history_overweight", False)

    # Create input dict for risk factor calculator
    user_data = {
        "age": demo.get("age", 0),
        "gender": demo.get("gender", "Male"),
        "height_m": demo.get("height_m", 1.0),
        "weight_kg": demo.get("weight_kg", 1.0),
        "caloric_beverages": life.get("caloric_beverages", "Sometimes"),
        "high_calorie_food": life.get("high_calorie_food", False),
        "veggie_freq": life.get("veggie_freq", 0),
        "meals_per_day": life.get("meals_per_day", 3),
        "calorie_monitor": life.get("calorie_monitor", False),
        "smokes": life.get("smokes", False),
        "water_litres": life.get("water_litres", 0),
        "physical_activity": life.get("physical_activity", 0),
        "tech_use": life.get("tech_use", 0),
        "between_meals": life.get("between_meals", "Sometimes"),
        "transport": life.get("transport", "Walking"),
        "family_history_overweight": family_history
    }

    return risk_factor_percentages(user_data)

def get_avg():
    total_users = users.count_documents({})

    if total_users == 0:
        return {}

    #gets averages for numeric fields
    avg_pipeline = [
        {
            "$project": {
                "age": "$demographics.age",
                "height_m": "$demographics.height_m",
                "weight_kg": "$demographics.weight_kg",
                "veggie_freq": "$lifestyle.veggie_freq",
                "meals_per_day": "$lifestyle.meals_per_day",
                "water_litres": "$lifestyle.water_litres",
                "physical_activity": "$lifestyle.physical_activity",
                "tech_use": "$lifestyle.tech_use"
            }
        },
        {
            #gets a ratio for non numeric fields
            "$group": {
                "_id": None,
                "avg_age": {"$avg": "$age"},
                "avg_height_m": {"$avg": "$height_m"},
                "avg_weight_kg": {"$avg": "$weight_kg"},
                "avg_veggie_freq": {"$avg": "$veggie_freq"},
                "avg_meals_per_day": {"$avg": "$meals_per_day"},
                "avg_water_litres": {"$avg": "$water_litres"},
                "avg_physical_activity": {"$avg": "$physical_activity"},
                "avg_tech_use": {"$avg": "$tech_use"},
            }
        }
    ]

    numeric_result = list(users.aggregate(avg_pipeline))[0]

    # Count categorical/boolean values
    count = [
        {
            "$group": {
                "_id": None,
                "high_calorie_food_count": {"$sum": {"$cond": ["$lifestyle.high_calorie_food", 1, 0]}},
                "calorie_monitor_count": {"$sum": {"$cond": ["$lifestyle.calorie_monitor", 1, 0]}},
                "smokes_count": {"$sum": {"$cond": ["$lifestyle.smokes", 1, 0]}},
            }
        }
    ]

    result = list(users.aggregate(count))[0]

    # Group by caloric_beverages frequency
    bev = [
        {
            "$group": {
                "_id": "$lifestyle.caloric_beverages",
                "count": {"$sum": 1}
            }
        }
    ]

    bev_result = list(users.aggregate(bev))
    caloric_beverages_ratios = {
        item["_id"]: round(item["count"] / total_users * 100, 2)
        for item in bev_result
    }

    # Compile final result
    return {
        "averages": {k.replace("avg_", ""): round(v, 2) for k, v in numeric_result.items() if k != "_id"},
        "ratios": {
            "high_calorie_food": round(result["high_calorie_food_count"] / total_users * 100, 2),
            "calorie_monitor": round(result["calorie_monitor_count"] / total_users * 100, 2),
            "smokes": round(result["smokes_count"] / total_users * 100, 2),
            "caloric_beverages": caloric_beverages_ratios
        },
        "total_users": total_users
    }

# returns one doc per obesity class with avg of six lifestyle mtrics
def get_radar_stats(classes):
    pipeline = [
        {"$match": {"target": {"$in": classes}}},
        {"$group": {
            "_id": "$target",

            "veggie_freq":       {"$avg": "$lifestyle.veggie_freq"},
            "water_litres":      {"$avg": "$lifestyle.water_litres"},
            "physical_activity": {"$avg": "$lifestyle.physical_activity"},
            "tech_use":          {"$avg": "$lifestyle.tech_use"},
            "meals_per_day":     {"$avg": "$lifestyle.meals_per_day"},
            "high_calorie_food": {"$avg": {
                "$cond": ["$lifestyle.high_calorie_food", 1, 0]
            }}
        }}
    ]

    docs = list(obesity_records.aggregate(pipeline))
    for d in docs:
        for i in ("veggie_freq","water_litres","physical_activity","tech_use","meals_per_day","high_calorie_food"):
            d[i] = round(d[i], 2)
    return docs

def get_user_radar_values(username):
    user = getUser(username)
    if not user:
        return {}

    lifestyle = user.get("lifestyle", {})

    fields = [
        "veggie_freq",
        "water_litres",
        "physical_activity",
        "tech_use",
        "meals_per_day",
        "high_calorie_food"
    ]

    data = {}
    for f in fields:
        if f == "high_calorie_food":
            data[f] = 1 if lifestyle.get(f, False) else 0
        else:
            try:
                data[f] = float(lifestyle.get(f, 0))
            except (TypeError, ValueError):
                data[f] = 0.0

    axis_meta = get_radar_axis()

    normalized_data = {}
    for f in fields:
        val = data[f]
        if val > 10:
            normalized_data[f] = 1.00
            continue

        mn = axis_meta[f]["min"]
        mx = axis_meta[f]["max"]

        if mx > mn:
            scaled = (val - mn) / (mx - mn)
        else:
            scaled = 0.5

        scaled = max(0.0, min(1.0, scaled))
        normalized_data[f] = round(scaled, 2)

    return normalized_data

def get_radar_axis():
    axes = [
        "veggie_freq",
        "water_litres",
        "physical_activity",
        "tech_use",
        "meals_per_day",
        "high_calorie_food"
    ]

    axis = {}
    for f in axes:
        stats = next(obesity_records.aggregate([
            {"$group": {
                "_id": None,
                "mn": {"$min": f"$lifestyle.{f}"},
                "mx": {"$max": f"$lifestyle.{f}"}
            }}
        ]))

        axis[f] = {"min": stats["mn"], "max": stats["mx"]}

    return axis

def get_lifestyle_risk_leaderboard():

    all_users = list(users.find())
    if not all_users:
        return []

    lifestyle_keys = list(all_users[0]["lifestyle"].keys())
    factor_impact = {}

    for key in lifestyle_keys:
        x = []
        y = []
        for user in all_users:
            try:
                lifestyle_val = float(user["lifestyle"][key])
                height = float(user["demographics"]["height_m"])
                weight = float(user["demographics"]["weight_kg"])
                bmi = weight / (height ** 2)
                x.append(lifestyle_val)
                y.append(bmi)
            except:
                continue

        if len(x) > 1:
            correlation = np.corrcoef(x, y)[0, 1]
            factor_impact[key] = abs(correlation)

    sorted_factors = sorted(factor_impact.items(), key=lambda x: x[1], reverse=True)
    return sorted_factors


