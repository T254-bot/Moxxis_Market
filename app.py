import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_items")
def get_items():
    items_for_sale = mongo.db.items_for_sale.find()
    return render_template("main.html", items_for_sale=items_for_sale)


@app.route("/main_page")
def main_page():
    return render_template("main.html")



@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        # checks if the username is already in use
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username taken")
            return redirect(url_for("sign_up"))

        #checks if email is already in use
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email").lower()})

        if existing_email:
            flash("Email address is already in use")
            return redirect(url_for("sign_up"))

        sign_up = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(sign_up)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Sign up Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    # grab the session user's email from db
    email = mongo.db.users.find_one(
        {"username": session["user"]})["email"]

    if session["user"]:
        return render_template("profile.html", username=username, email=email)

    return redirect(url_for("login"))


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_details():
    if request.method == "POST":

        new_details = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }

        username = request.form.get("username").lower()
        email = request.form.get("email").lower()

        mongo.db.users.update_one({"username": username}, {"$set": new_details}, upsert=True)

        # put the new user into 'session' cookie
        session.pop("user")
        session["user"] = request.form.get("username").lower()
        flash("Details updated successfully!")
        return render_template("profile.html", username=username, email=email)

    return render_template("edit_details.html")


@app.route("/logout")
def logout():
    # logs user out of session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/delete_user")
def delete_user():
    # finds and deletes user from db
    user = mongo.db.users.find_one(
        {"username": session["user"]})

    if session["user"]:
        session.pop("user")
        mongo.db.users.delete_one(user)

    return redirect(url_for("main_page"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
