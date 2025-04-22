'''
JAVA: Vedant Kothari, Aidan Wong, Alex Luo, Jonathan Metzler
SoftDev
P04: Makers Makin' It, Act II -- The Seequel
2025-04-05
Time Spent: 1
'''

from flask import Flask, render_template, url_for, session, request, redirect, jsonify
from app.DBModules import dbFunctions
import os


app = Flask(__name__)

app.secret_key = os.urandom(32)

dbFunctions.initDB()

@app.route("/", methods=['GET', 'POST'])
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('auth'))

@app.route("/auth", methods=['GET', 'POST'])
def auth():
    form_type = request.form.get('form_type')
    if form_type == "sign_in": # Login Functionality
        name = request.form.get('name')
        password = request.form.get('password')

        if dbFunctions.checkUser(name, password):
            session['username'] = name
            return redirect(url_for('home'))
        else:
            return render_template('auth.html', errorL = "USERNAME OR PASSWORD IS INCORRECT")
    if form_type == "sign_up": # Register Functionality
        name = request.form.get('name')
        password = request.form.get('password')

        if not dbFunctions.registerUser(name, password):
            return render_template('auth.html', errorS="USERNAME TAKEN")    
        session['username'] = name
        return redirect(url_for('home'))

    return render_template('auth.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('auth'))
    return redirect(url_for('profile'))

@app.route("/visualize")
def visualize():
    if 'username' not in session:
        return redirect(url_for('auth'))

    user_doc = dbFunctions.getUser(session['username'])
    print(user_doc)
    return render_template("visualizations.html", user_data=user_doc)

@app.route("/data")
def data():
    return jsonify(dbFunctions.fetch_obesity_data())

@app.route("/api/state-values")
def state_values():
    data = dbFunctions.get_state_data()
    print(jsonify(data))
    return jsonify(data)

@app.route("/api/risk-factors", methods=["GET"])
def user_risk_factors():
    if 'username' in session:
        user_doc = dbFunctions.getUser(session['username'])
        if not user_doc.get("demographics"):
            return jsonify([])
        percentages = dbFunctions.risk_factor_percentages(user_doc)
        return jsonify([{"name": k, "value": v} for k, v in percentages.items()])
    return jsonify({"error": "Not logged in"}), 401

#[{"_id":"Normal_Weight","veggie_freq":val,"water_litres":val,"physical_activity":val,"tech_use":val,"meals_per_day":val,"high_calorie_food":val},{"_id":"Obesity_Type_I","veggie_freq":val,"water_litres":val,"physical_activity":val,"tech_use":val,"meals_per_day":val,"high_calorie_food":val}]
@app.route("/api/radar")
def api_radar():
    classes = request.args.get("classes","").split(",")
    cls = [c for c in classes if c] or ["Normal_Weight","Obesity_Type_I"]
    return jsonify(dbFunctions.get_radar_stats(cls))

#{"veggie_freq":{"min":val,"max":val},"water_litres":{"min":val,"max":val},"physical_activity":{"min":val,"max":val},"tech_use":{"min":val,"max":val},"meals_per_day":{"min":val,"max":val},"high_calorie_food":{"min":val,"max":val}}
@app.route("/api/radar_axis")
def api_radar_meta():
    return jsonify(dbFunctions.get_radar_axis())

@app.route("/api/radar_user")
def api_user_radar():
    username = session.get("username")  
    return jsonify(dbFunctions.get_user_radar_values(username))

@app.route("/api/user_risk", methods=["GET"])
def user_risk():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_doc = dbFunctions.getUser(session["username"])
    if not user_doc:
        return jsonify({"error": "User not found"}), 404

    percentages = dbFunctions.risk_factor_percentages(user_doc)
    return jsonify(percentages)

@app.route('/simulate', methods=['POST'])
def simulate():
    user_doc = request.get_json()
    percentages = dbFunctions.risk_factor_percentages(user_doc)
    return jsonify([{"name": k, "value": v} for k, v in percentages.items()])

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect(url_for("auth"))

    username = session["username"]

    if request.method == "POST":
        user_data = {
            "age": float(request.form.get("age", 0)),
            "gender": request.form.get("gender", ""),
            "height_m": float(request.form.get("height_m", 0)),
            "weight_kg": float(request.form.get("weight_kg", 0)),
            "caloric_beverages": request.form.get("caloric_beverages", "no"),
            "high_calorie_food": (request.form.get("high_calorie_food") == "yes"),
            "veggie_freq": float(request.form.get("veggie_freq", 0)),
            "meals_per_day": float(request.form.get("meals_per_day", 0)),
            "calorie_monitor": (request.form.get("calorie_monitor") == "yes"),
            "smokes": (request.form.get("smokes") == "yes"),
            "water_litres": float(request.form.get("water_litres", 0)),
            "physical_activity": float(request.form.get("physical_activity", 0)),
            "tech_use": float(request.form.get("tech_use", 0)),
            "between_meals": request.form.get("between_meals", "no"),
            "transport": request.form.get("transport", "Other"),
            "family_history_overweight": (request.form.get("family_history_overweight") == "yes"),
        }
        dbFunctions.storeUser(username, user_data)

    user_doc = dbFunctions.getUser(username)
    risk_info = None
    recommendations = []

    if user_doc.get("demographics"):
        points, category = dbFunctions.computeRisk(user_doc)
        pcts = dbFunctions.risk_factor_percentages(user_doc)

        def top3_with_tips(p):
            TIP_MAP = {
                "BMI": "try a calorie‑controlled diet and daily walks.",
                "FAMILY HISTORY": "schedule yearly BMI checks and seek diet advice.",
                "LOW VEGGIES": "add one veggie serving to each meal.",
                "NO EXERCISE": "start with 10‑minute brisk walks twice daily.",
                "SUGARY/ALC DRINKS": "swap soda/alcohol for water."
            }
            top = sorted(p.items(), key=lambda kv: kv[1], reverse=True)[:3]
            return [(k, v, TIP_MAP.get(k, "consult a professional")) for k, v in top]

        risk_info = {"points": points, "category": category}
        recommendations = top3_with_tips(pcts)
    return render_template("profile.html",username=username,user=user_doc,risk_info=risk_info,recommendations=recommendations)

@app.route("/bar_race")
def bar_race():             
    if 'username' not in session:
        return redirect(url_for('auth'))
    return render_template("bar_race.html", username=session['username'])

@app.route("/map")
def map():                  
    if 'username' not in session:
        return redirect(url_for('auth'))
    return render_template("map.html", username=session['username'])

@app.route("/radar")
def radar():                
    if 'username' not in session:
        return redirect(url_for('auth'))
    return render_template("radar.html", username=session['username'])

@app.route("/risk_leaderboard")
def leaderboard():
    sorted_factors = dbFunctions.get_lifestyle_risk_leaderboard()
    return render_template("leaderboard.html", factors=sorted_factors, username=session.get("username"))


if __name__ == "__main__":
    app.debug = True
    app.run()
