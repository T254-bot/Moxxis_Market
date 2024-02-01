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
@app.route("/main_page")
def main_page():
    return render_template("main.html")


@app.route("/market_page")
def market_page():
    items_for_sale = mongo.db.items_for_sale.find()
    return render_template("market.html", items_for_sale=items_for_sale)



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

    # grab all items in db
    items_for_sale = mongo.db.items_for_sale.find()

    if session["user"]:
        return render_template("profile.html", username=username, email=email, items_for_sale=items_for_sale)

    return redirect(url_for("login"))


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_details():
    if request.method == "POST":

        new_item = mongo.db.users.find_one({"username": session["user"]})
        print(new_item)

        new_details = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }

        email_match = mongo.db.users.find_one({"email": new_details["email"]})


        if email_match and email_match["_id"] != new_item["_id"]:
            flash("Email address is already in use")
            return redirect(url_for("edit_details"))


        username_match = mongo.db.users.find_one({"username": new_details["username"]})

        if username_match and username_match["_id"] != new_item["_id"]:
            flash("Username is already in use")
            return redirect(url_for("edit_details"))

        username = request.form.get("username").lower()
        email = request.form.get("email").lower()

        mongo.db.users.update_one({"_id": ObjectId(new_item["_id"])}, {"$set": new_details}, upsert=True)

        # put the user into new 'session' cookie
        session.pop("user")
        session["user"] = request.form.get("username").lower()
        flash("Details updated successfully!")
        return render_template("profile.html", username=username, email=email)

        # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    # grab the session user's email from db
    email = mongo.db.users.find_one(
        {"username": session["user"]})["email"]

    return render_template("edit_details.html", username=username, email=email)


@app.route("/create_item", methods=["GET", "POST"])
def create_item():
    if request.method == "POST":

        user_email = mongo.db.users.find_one(
            {"username": session["user"]})["email"]

        new_item = {
            "item_name": request.form.get("item-name").lower(),
            "item_score": request.form.get("item-score").lower(),
            "damage": request.form.get("damage").lower(),
            "accuracy": request.form.get("accuracy").lower(),
            "handling": request.form.get("handling").lower(),
            "reload_time": request.form.get("reload-time").lower(),
            "fire_rate": request.form.get("fire-rate").lower(),
            "magazine_size": request.form.get("magazine-size").lower(),
            "elemental": request.form.get("elemental").lower(),
            "for_trade": request.form.get("for-trade").lower(),
            "created_by": user_email
        }
        mongo.db.items_for_sale.insert_one(new_item)

        flash("Item added to Market Successfully!")
        return redirect(url_for("market_page"))

    return render_template("create_item.html")


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
