from flask import Flask, render_template, request, session, redirect, url_for

import os

app = Flask(__name__)    #create Flask object

app.secret_key = os.urandom(32)

@app.route(("/"), methods=['GET', 'POST'])
def home():
    # check if someone is logged in
    if 'username' in session:
        return render_template( 'home.html', username=session['username'])
    # else have them log in
    return redirect(url_for('login'))

@app.route(("/login") , methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('home'))
    return render_template( 'login.html' , error_message = "")