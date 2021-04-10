# Importing all necessary libraries
import os
import datetime
import smtplib
import time
import random

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, date

from helpers import login_required

# https://github.com/vairiskovels/log-it-app.git
# postgres://imaapiuscnjbaq:3555f85d9f67ce2b42e1ff29108d880ca9a22163ba12177d13b60dc56b38e80a@ec2-54-228-139-34.eu-west-1.compute.amazonaws.com:5432/defrtcvo099c7g


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "secret key"
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=10)

global COOKIE_TIME_OUT
COOKIE_TIME_OUT = 60*5*24 #5 minutes

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use PostgreSQL database
db = SQL(os.getenv("DATABASE_URL").replace("://", "ql://", 1))

@app.before_request
def make_session_permanent():
    session.permanent = True

def get_user_currency():
    return db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]["currency"]

def get_random_key():
    key = ''

    for i in range(random.randint(12, 16)):
        chars = [random.randint(48,57), random.randint(65,90), random.randint(97,121)]
        key += chr(chars[random.randint(0,2)])

    return key

# Route for main page if user is logged in
@app.route("/")
@login_required
def index():

    # Query database for all necessary data
    types = db.execute("SELECT * FROM types")
    history = db.execute(f"SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10", session["user_id"])

    # Getting total of each category, category name and color from user expenses
    rows = []
    for i in range(len(types)):
        # If user has logged an expense in this category
        if len(db.execute(f"SELECT type FROM expenses WHERE user_id = ? AND type_id={i+1}", session["user_id"])) > 0:
            #print("GETS TO IF LEN")

            #print(db.execute(f"SELECT ROUND(SUM(price)::numeric, 2) FROM expenses WHERE user_id = ? AND type_id = {i+1}", session["user_id"])[0]['round'])

            # If total of category is integer
            if db.execute(f"SELECT ROUND(SUM(price)::numeric, 2) FROM expenses WHERE user_id = ? AND type_id = {i+1}", session["user_id"])[0]['round'].is_integer():
                rows.append(db.execute(f"SELECT SUM(price)::numeric::integer AS price, type, color FROM expenses WHERE user_id = ? AND type_id = {i+1} GROUP BY type, color", session["user_id"]))
                #print("GETS TO INTEGER")

            # If total of category has floating point
            else:
                rows.append(db.execute(f"SELECT ROUND(SUM(price)::numeric, 2) AS price, type, color FROM expenses WHERE user_id = ? AND type_id = {i+1} GROUP BY type, color", session["user_id"]))
                #print("GETS TO FLOAT")

        # If user hasn't logged an expense in this category
        else:
            rows.append(db.execute(f"SELECT name AS type, color FROM types WHERE id={i+1}"))
            rows[i][0]['price'] = 0

    print(rows)

    '''
    # Rename key names in dictionaries, so it fits Jinja syntax in html file
    for i in range(len(rows)):

        if 'sum' in rows[i][0]:

        new_key = "price"
        old_key = "round"
        rows[i][0][new_key] = rows[i][0].pop(old_key)

        new_key_name = "type"
        old_key_name = "name"
        if rows[i][0].get('name') != None:
            rows[i][0][new_key_name] = rows[i][0].pop(old_key_name)
    '''

    if request.method == "GET":
        return render_template("index.html", rows=rows, currency=get_user_currency(), history=history)

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()
    error = None

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get user entered data
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check for valid username and password
        if len(rows) != 1:
            error = "Invalid username"

        elif not check_password_hash(rows[0]["password"], password):
            error = "Invalid password"

        elif len(username) <= 0:
            error = "Please fill username field"

        elif len(password) <= 0:
            error = "Please fill password field"

        # If everything is valid
        else:
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")

    return render_template("login.html",error=error)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    error = None

     # If user tries to register
    if request.method == "POST":

        # Get user inputed information
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("full_name")

        # Split name and surname
        first_name = name.split()[0]
        if len(name.split()) > 1:
            surname = name.split()[1]
        else:
            surname = ''

        # Check if username and email already exist
        name_check = db.execute("SELECT * FROM users WHERE username = ?", username)
        mail_check = db.execute("SELECT * FROM users WHERE email = ?", email)

        # If username or email is already taken, displays an error
        if len(name_check) >= 1:
            error = "Username already taken"

        elif len(mail_check) >= 1:
            error = "Email already taken"

        elif len(username) <= 0:
            error = "Please fill username field"

        elif len(email) <= 0:
            error = "Please fill email field"

        elif len(password) <= 0:
            error = "Please fill password field"

        elif len(name) <= 0:
            error = "Please fill name field"

        # If data is valid, insert add new user to the table
        else:
            db.execute("INSERT INTO users (username, password, email, name, surname) VALUES (?, ?, ?, ?, ?)", username, generate_password_hash(password), email, first_name, surname)
            return redirect("/")

    return render_template("register.html",error=error)


@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/recover", methods=["GET", "POST"])
def recover():
    error = None
    success = None
    email = None
    key = get_random_key()

     # If user tries to register
    if request.method == "POST":

        # Get user email
        email = request.form.get("email")

        # Check if email exists
        mail_check = db.execute("SELECT * FROM users WHERE email = ?", email)

        # If email exists proceed
        if len(mail_check) >= 1:
            success = "Recovery message sent to "

            # Gets user's email and name
            rows = db.execute("SELECT * FROM users WHERE email = ?", email)
            name = rows[0]['name']

            # Sends a password recovery message to user's email
            message = 'Subject: {}\n\n{}'.format("Password recovery", f"Hello, {name}\nYou have recently lost/forgot your password.\n\nYou can change it here: https://ide-0ea9f6c526a0481da1950c02852766cf-8080.cs50.ws/change_password?email={email}&key={key}")

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login("help.logit@gmail.com", "135asus123")
            server.sendmail("help.logit@gmail.com",
                            email,
                            message)

            server.quit()

            db.execute("INSERT INTO recovery (email, key) VALUES (?, ?)", email, key)

        # If email doesn't exist display an error
        else:
            error = "Email doesn't exist"

    return render_template("recover.html",error=error, success=success, email=email)

@app.route("/change_password", methods=["GET", "POST"])
def change():
    error = None
    success = None
    urlparam = []

    # Gets an email from link arguments
    email = request.args.get('email')
    key = request.args.get('key')

    if request.method == "POST":

        # Gets new password from user
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks if email exists
        mail_check = db.execute("SELECT * FROM users WHERE email = ?", email)

        # Check key
        key_check = db.execute("SELECT * FROM recovery WHERE email = ? AND key = ?", email, key)

        # If email exists and new passwords are the same proceeds
        if len(mail_check) >= 1 and len(key_check) >= 1 and password == confirmation:
            success = "Password changed!"
            db.execute("UPDATE users SET password = ? WHERE email = ?", generate_password_hash(password), email)
            db.execute("DELETE FROM recovery WHERE key = ?", key)

        elif password != confirmation:
            error = "Passwords should match"

        elif len(key_check) < 1:
            error = "Invalid key"

        else:
            error = "Email doesn't exist"

    urlparam.extend([email,key])
    return render_template("change_password.html",error=error, success=success, urlparam=urlparam)
    if success:
        time.sleep(1)
        return redirect("/")

@app.route("/change_password_from_profile", methods=["GET", "POST"])
@login_required
def change_2():
    error = None
    success = None

    # Gets user's information
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    name = rows[0]["name"]
    surname = rows[0]["surname"]
    email = rows[0]["email"]
    username = rows[0]["username"]
    currency = rows[0]["currency"]

    if request.method == "POST":

        # Gets old and new password from the user
        old = request.form.get("old")
        new = request.form.get("new")
        confirm = request.form.get("confirm")

        # Checks for password validity
        if len(old) <= 0:
            error = "Please fill old password field"

        elif len(new) <= 0:
            error = "Please fill new password field"

        elif len(confirm) <= 0:
            error = "Please fill confirm password field"

        elif len(new) < 8 or len(confirm) < 8:
            error = "New password should be 8 characters long"

        elif not check_password_hash(rows[0]["password"], old):
            error = "Incorrect old password"

        elif new != confirm:
            error = "New password should match"

        else:
            success = "Password changed successfully"
            db.execute("UPDATE users SET password = ? WHERE id = ?", generate_password_hash(new), session["user_id"])

    return render_template("account.html",change_error=error, change_success=success, name=name, surname=surname, email=email, username=username, currency=currency)

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    error = None
    success = None

    # Gets user's information
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    name = rows[0]["name"]
    surname = rows[0]["surname"]
    email = rows[0]["email"]
    username = rows[0]["username"]

    if request.method == "POST":

        # Gets data from the user input
        get_name = request.form.get("name")
        get_surname = request.form.get("surname")
        get_email = request.form.get("email")
        get_username = request.form.get("username")
        get_currency = request.form.get("currency")
        if get_currency == None:
            get_currency = get_user_currency()


        # Checks if email and username is already taken
        mail_check = db.execute("SELECT * FROM users WHERE email = ?", get_email)
        username_check = db.execute("SELECT * FROM users WHERE username = ?", get_username)

        # Checks for validity
        if len(get_name) <= 0:
            error = "Please fill name field"

        elif len(get_surname) <= 0:
            error = "Please fill surname field"

        elif len(get_email) <= 0:
            error = "Please fill email field"

        elif len(get_username) <= 0:
            error = "Please fill username field"

        elif len(mail_check) >= 1 and get_email != email:
            error = "Email is alreay taken"

        elif len(username_check) >= 1 and get_username != username:
            error = "Username is alreay taken"

        else:
            success = "Data is successfully updated"
            db.execute("UPDATE users SET name = ?, surname = ?, email = ?, username = ?, currency = ? WHERE id = ?", get_name, get_surname, get_email, get_username, get_currency, session["user_id"])

    show_currency = get_user_currency()

    currencies = {
        '€' : 'EUR',
        '$' : 'USD',
        '£' : 'GBP'
    }

    show_currency = currencies[show_currency]

    if success:
        return render_template("account.html", name=get_name, surname=get_surname, email=get_email, username=get_username, error=error, success=success, currency=show_currency)
    return render_template("account.html", name=name, surname=surname, email=email, username=username, error=error, success=success, currency=show_currency)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    error = None
    success = None
    today = date.today()

    if request.method == "POST":

        # Gets data from user input
        add_type = request.form.get("type")
        add_name = request.form.get("name")
        add_amount = request.form.get("amount")
        add_date = request.form.get("date")

        # Converts "," to "." in price if price isn't an integer
        if "," in add_amount:
            add_amount = float(add_amount.replace(",", "."))
        else:
            add_amount = float(add_amount)
        add_amount = round(add_amount, 2)

        # Gets id and color of according expense type
        add_color = db.execute("SELECT color FROM types WHERE name = ?", add_type)
        type_id = db.execute("SELECT id FROM types WHERE name = ?", add_type)

        # Checks for validity
        if type(add_amount) == str:
            error = "Please enter correct price"

        elif add_amount <= 0:
            error = "Price cannot be negative"

        elif len(add_type) <= 0:
            error = "Please fill type field"

        elif len(add_type) <= 0:
            error = "Please fill type field"

        elif len(add_date) <= 0:
            error = "Please fill date field"

        else:
            db.execute("INSERT INTO expenses (user_id, type_id, Name, Price, Date, color, Type) VALUES (?, ?, ?, ?, ?, ?, ?)", session["user_id"], type_id[0]["id"], add_name, "{:.2f}".format(add_amount), add_date, add_color[0]["color"], add_type)
            success = f'"{add_name}" successfully added to the list'

    # Queries database for data
    rows = db.execute("SELECT * FROM types")

    return render_template("add.html",rows=rows,error=error, success=success, today=today, currency=get_user_currency())

@app.route("/statistics")
@login_required
def statistics():

    # Creates list with two list - one for "Pie" type char, second for "Bar" chart
    rows = [[], ]

    # Gets all expense types from table
    types = db.execute("SELECT * FROM types")

    # Gets total of each expense type for "Pie" chart
    for i in range(len(types)):
        if len(db.execute(f"SELECT Type FROM expenses WHERE user_id = ? AND type_id={i+1}", session["user_id"])) > 0:
            rows[0].append(db.execute(f"SELECT SUM(Price) AS price, type, color FROM expenses WHERE user_id = ? AND type_id = {i+1} GROUP BY type, color", session["user_id"]))
        else:
            rows[0].append(db.execute(f"SELECT name, color FROM types WHERE id={i+1}"))
            rows[0][i][0]['price'] = 0

    # Gets data for "Bar" chart
    rows.append(db.execute("SELECT name, price, color FROM expenses WHERE user_id = ? ORDER BY price DESC LIMIT 5", session["user_id"]))

    return render_template("statistics.html", rows=rows, currency=get_user_currency())


order_num = 1
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    global order_num

    deep_search = False
    search_name = None
    search_type = None
    delete = None
    row_count = None

    today = date.today()

    if request.method == "POST":

        # Gets data from user input
        search_type = request.form.get("type")
        search_name = request.form.get("input")
        delete = request.args.get('delete')
        deep_search = True

        if search_type == 'Category':
            search_type = 'Type'

    # Gets sorting type from user
    sort_type = request.args.get('type')
    order = ["", "DESC", "ASC"]

    # Gets all expense types
    types = db.execute("SELECT * FROM types")

    if delete:
        db.execute(f"DELETE FROM expenses WHERE id={delete}")
        delete = None
        return redirect("/history")

    # If user is searching by anything but price
    if deep_search and search_name and search_type != 'Price' and search_type != 'Date' and search_type != None:
        rows = db.execute(f"SELECT * FROM expenses WHERE {search_type} LIKE '%{search_name}%' AND user_id = ?", session["user_id"])

    # If user is searching by excatly the price inputed
    elif deep_search and search_name and search_type == 'Price':
        rows = db.execute(f"SELECT * FROM expenses WHERE {search_type} = '{search_name}' AND user_id = ?", session["user_id"])

    # If user is searching by excatly the date inputed
    elif deep_search and search_name and search_type == 'Date':
        rows = db.execute(f"SELECT * FROM expenses WHERE {search_type} = '{search_name}' AND user_id = ?", session["user_id"])

    # If user is sorting by expense type (Ascending or Descending)
    elif sort_type:
        rows = db.execute(f"SELECT * FROM expenses WHERE user_id = ? ORDER BY {sort_type} {order[order_num]}", session["user_id"])
        order_num *= -1

    # By default it gets sorted by the date added in descending order
    else:
        rows = db.execute(f"SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC", session["user_id"])
        order_num *= -1

    # For html div height
    row_count = len(rows) * 20 + 1000
    row_count_mobile = len(rows) * 50 + 900

    if search_type == 'Type':
        search_type = 'Category'

    return render_template("history.html", rows=rows, types=types, search_type=search_type, row_count=row_count, row_count_mobile=row_count_mobile, today=today, currency=get_user_currency(), delete=delete)

@app.route("/dont")
@login_required
def dont():
    return render_template("dont.html")