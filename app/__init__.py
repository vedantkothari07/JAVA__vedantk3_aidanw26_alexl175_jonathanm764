'''
JAVA: Vedant Kothari, Aidan Wong, Alex Luo, Jonathan Metzler
SoftDev
P04: Makers Makin' It, Act II -- The Seequel
2025-04-05
Time Spent: 1
'''

from flask import Flask, render_template, url_for, session, request, redirect
from DBModules import dbFunctions
import os


app = Flask(__name__)

app.secret_key = os.urandom(32)

dbFunctions.initDB()

@app.route("/", methods=['GET', 'POST'])
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'], risk_info=session.pop('risk_info', None))
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
            "physical_activity": float(request.form.get("physical_activity",0)),
            "tech_use": float(request.form.get("tech_use", 0)),
            "between_meals": request.form.get("between_meals", "no"),
            "transport": request.form.get("transport", "Other"),
            "family_history_overweight": (request.form.get("family_history_overweight") == "yes"),
        }

        dbFunctions.storeUser(name, user_data)

        session['username'] = name
        return redirect(url_for('home'))

    return render_template('auth.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' in session:
        username = session['username']
        user_doc = dbFunctions.getUser(username)
        points, category = dbFunctions.computeRisk(user_doc)
        session['risk_info'] = {
            "points": points,
            "category": category
        }
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.debug = True
    app.run()