
from flask import Flask, render_template, request, session, redirect, url_for

import sqlite3
import os

app = Flask(__name__)    #create Flask object
DB_FILE = "database.db" #create a database for private keys storage

# makin' a supa-secret key
app.secret_key = os.urandom(32)

db = sqlite3.connect(DB_FILE, check_same_thread=False) #open if file exists, otherwise create
c = db.cursor()  #facilitate db ops -- you will use cursor to trigger db events

#c.execute("DROP TABLE users;")

# making a table for users
c.execute(
'''
CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY,
        password TEXT,
        privatekey TEXT
        );
''')

db.commit()


@app.route(("/"), methods=['GET', 'POST'])
def home():
    # check if someone is logged in
    if 'username' in session:
        return render_template( 'home.html', username=session['username'])
    # else have them log in
    return redirect(url_for('login'))

@app.route(("/login") , methods=['POST'])
def login():
    # if submission
    if request.method == 'POST':


        nameInput = request.form['username']

        c.execute("SELECT * FROM users;")
        d = c.fetchall()
        broke = False
        # checking if this username is already in the database
        for row in d:
            #print(".")
            #print(d[0][0])
            #print(nameInput)
            if row[0] == nameInput:
                userKey = row[1]
                #print("userkey: " + userKey)
                broke = True
                break

        # if there is...
        if broke:
            #print(userKey + " == " + request.form['password'])

            # check if entered password matches up
            if userKey == request.form['password']:
                #print("gone thru")
                u = request.form['username']
                # add them to session
                session['username'] = request.form['username']
                # send them home
                return redirect(url_for('home'))
            else:
                # we tell them they messed up
                return render_template( 'login.html' , error_message = "Incorrect username or password")
        #checking if inputted password is the same as password linked to username in database
        elif not broke:
            # tell them to register
            error = "User not in database. Register to make an account!"
            return render_template( 'login.html' , error_message = error)

        return redirect(url_for('home'))
    return render_template( 'login.html' , error_message = "")

@app.route(("/register") , methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nameInput = request.form['username']

        c.execute("SELECT * FROM users;")
        d = c.fetchall()
        broke = False
        # check if same name user is in database
        for row in d:
            #print(".")
            #print(d[0][0])
            #print(nameInput)
            if row[0] == nameInput:
                broke = True
                break
        if (broke):
            # tell them to change
            error = "User already in database. Login to access existing account, or register a new one."
            return render_template( 'login.html' , error_message = error)

        session['username'] = request.form['username']

        newdata = [request.form['username'], request.form['password'], os.urandom(32)]
        # print("private key: ")
        # print(newdata[2])

        # else add their info into the table
        c.execute("INSERT INTO users VALUES (?, ?, ?);", newdata)
        db.commit()

        #PRINT STATEMENT
        #c.execute('SELECT * FROM users;')
        #result = c.fetchall()
        #print("USERS:")
        #for row in result:
        #    print(result)

        u = request.form['username']
        return redirect(url_for('home'))
    return render_template( 'login.html' )


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    if 'username' in session:
        if request.method == 'POST':
            # if they clicked the logout button..
            if request.form.get("logout") is not None:
                # log them out
                session.pop('username', None)
                return redirect(url_for('login'))
            else:
                return redirect(url_for('home'))
        return render_template( 'logout.html', username = session['username'])

    return redirect(url_for('login'))


if __name__ == "__main__": #false if this file imported as module
    app.debug = True
    app.run()

db.close()
