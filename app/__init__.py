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

        if dbFunctions.registerUser(name, password):
            session['username'] = name
            return redirect(url_for('home'))
        else:
            return render_template('auth.html', errorS="USERNAME TAKEN")
    return render_template('auth.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.debug = True
    app.run()