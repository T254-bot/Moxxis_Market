import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from flask_mail import Mail, Message
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

@app.route("/")
@app.route("/main_page")
def main_page():
    """
    Renders the main page.

    Returns:
        Rendered template with the main page content.
    """
    # Checks if user is logged in and if so grabs users email
    if "user" in session:
        current_user_email = mongo.db.users.find_one(
            {"username": session["user"]})["email"]
    else:
        None 

    # Grab all items_for_sale from the database
    items_cursor = mongo.db.items_for_sale.find()

    # Convert cursor to a list and reverse it to get the last 6 items
    last_six_items = list(items_cursor)[-6:]

    return render_template("main.html", last_six_items=last_six_items,)


@app.route("/market_page")
def market_page():
    """
    Renders the market page.

    Returns:
        Rendered template with the market page content.
    """
    # grabs all items from db
    items_for_sale = mongo.db.items_for_sale.find()

    # checks if user is logged in and if so grabs email address from mongo
    if "user" in session:
        current_user_email = mongo.db.users.find_one(
            {"username": session["user"]})["email"]
    else:
        current_user_email = None

    return render_template("market.html", items_for_sale=items_for_sale,current_user_email=current_user_email)



@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    """
    Handles user sign-up process.

    Returns:
        Rendered template for sign-up page or redirects to profile page if sign-up is successful.
    """

    if request.method == "POST":

        # Grabs passwords from form for validation
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")
        
        # checks if passwords match
        if password != confirm_password:
            flash("Passwords do NOT match!")
            return redirect(url_for("sign_up"))

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

        # Builds new user data and inserts into users db collection
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
    """
    Handles user login process.

    Returns:
        Rendered template for login page or redirects to profile page if login is successful.
    """
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


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """
    Renders the user profile page.

    Returns:
        Rendered template with the user profile page content.
    """
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    # grab the session user's email from db
    email = mongo.db.users.find_one(
        {"username": session["user"]})["email"]

    # Query the MongoDB collection to find items with the same created_by value that matches current users email
    ifs_list = list(mongo.db.items_for_sale.find({"created_by": email}))
    pi_list = matching_items = list(mongo.db.pending_items.find({"created_by": email}))

    # grab all items in both dbs
    items_for_sale = list(mongo.db.items_for_sale.find())
    pending_items = list(mongo.db.pending_items.find())

    if session["user"]:
        return render_template("profile.html", username=username, email=email, items_for_sale=items_for_sale, pending_items=pending_items, ifs_list=ifs_list, pi_list=pi_list)

    return redirect(url_for("login"))


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_details():
    """
    Handles editing user details.

    Returns:
        Rendered template for editing details or redirects to profile page if details are updated.
    """
    if request.method == "POST":

        # Grabs users current info from db
        current_user = mongo.db.users.find_one({"username": session["user"]})
        
        # Grabs users new info from form
        new_username = request.form.get("username").lower()
        new_email = request.form.get("email").lower()
        new_password = generate_password_hash(request.form.get("password"))
        
        # grabs passwords from form for validation 
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")
        
        # checks if passwords match
        if password != confirm_password:
            flash("Passwords do NOT match!")
            return redirect(url_for("edit_details"))

        # Check if the new email is already in use by another user
        email_match = mongo.db.users.find_one({"email": new_email})
        if email_match and email_match["_id"] != current_user["_id"]:
            flash("Email address is already in use")
            return redirect(url_for("edit_details"))

        # Check if the new username is already in use by another user
        username_match = mongo.db.users.find_one({"username": new_username})
        if username_match and username_match["_id"] != current_user["_id"]:
            flash("Username is already in use")
            return redirect(url_for("edit_details"))

        # Update the user's details in the users collection
        mongo.db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"username": new_username, "email": new_email, "password": new_password}}
        )

        # Update the created_by field in the items_for_sale collection
        mongo.db.items_for_sale.update_many(
            {"created_by": current_user["email"]},
            {"$set": {"created_by": new_email}}
        )

        # Update the session user's username
        session["user"] = new_username

        flash("Details updated successfully!")
        return redirect(url_for("profile", username=new_username))

    # Get the session user's username and email
    username = mongo.db.users.find_one({"username": session["user"]})["username"]
    email = mongo.db.users.find_one({"username": session["user"]})["email"]

    return render_template("edit_details.html", username=username, email=email)



@app.route("/create_item", methods=["GET", "POST"])
def create_item():
    """
    Handles creation of new items for sale.

    Returns:
        Rendered template for creating items or redirects to market page if item is created successfully.
    """

    if request.method == "POST":

        # Grabs current users email for use in item data
        user_email = mongo.db.users.find_one(
            {"username": session["user"]})["email"]

        # Builds new item data from form and inserts into items_for_sale db collection
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
    """
    Logs out the user.

    Returns:
        Redirects to the login page after logging out.
    """
    # logs user out of session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/delete_user")
def delete_user():
    """
    Deletes the user.

    Returns:
        Redirects to the main page after deleting the user.
    """
    # finds and deletes user from db
    user = mongo.db.users.find_one(
        {"username": session["user"]})

    if session["user"]:
        session.pop("user")
        mongo.db.users.delete_one(user)

    return redirect(url_for("main_page"))

@app.route("/delete_item", methods=["GET", "POST"])
def delete_item():
    """
    Deletes an item.

    Returns:
        Redirects to the profile page after deleting the item.
    """

    # Gets item id from html page
    item_id = request.form.get("item-id")

    # Checks if the item is in the 'items_for_sale' database
    item = mongo.db.items_for_sale.find_one({'_id': ObjectId(item_id)})
    if item:
        # If the item IS in the 'items_for_sale' db
        mongo.db.items_for_sale.delete_one({'_id': ObjectId(item_id)})
        flash("Item deleted successfully")
        return redirect(url_for("profile"))

    # Checks if the item is in the 'pending_items' db
    item = mongo.db.pending_items.find_one({'_id': ObjectId(item_id)})
    if item:
        # If the item IS in the 'pending_items' db
        mongo.db.pending_items.delete_one({'_id': ObjectId(item_id)})
        flash("Item deleted successfully")
        return redirect(url_for("profile"))

    # If the item is not found in either db
    flash("Error: Item could not be found")
    return redirect(url_for("profile"))


@app.route("/move_to_pending", methods=["GET", "POST"])
def move_to_pending():
    """
    Moves an item to the pending items collection and send email to seller.

    Returns:
        Redirects to the market page after moving the item.
    """

    # Retrieves the item id from html page and finds item within 'items_for_sale' and builds new_item to be placed into 'pending_items'
    item_id = request.form.get("item-id")
    item = mongo.db.items_for_sale.find_one({'_id': ObjectId(item_id)})
    new_item = {
        "item_name": item["item_name"],
        "item_score": item["item_score"],
        "damage": item["damage"],
        "accuracy": item["accuracy"],
        "handling": item["handling"],
        "reload_time": item["reload_time"],
        "fire_rate": item["fire_rate"],
        "magazine_size": item["magazine_size"],
        "elemental": item["elemental"],
        "for_trade": item["for_trade"],
        "created_by": item["created_by"]
    }
    if session["user"]:
        current_user_email = mongo.db.users.find_one(
            {"username": session["user"]})["email"]
    else:
        flash("You must be logged in to perform this action")
        return redirect(url_for("market_page"))

    if item:
        # Insert the item into the pending_items collection
        mongo.db.pending_items.insert_one(new_item)

        # Sends the email to the seller
        msg = Message("A user is interested in your item!", sender = current_user_email , recipients=[item["created_by"]])
        msg.body = f"Reply to this email to begin discussing a price/trade for your {item['item_name']}. Just dont forget to remove the item if it sells or re list if you cannot make a deal."
        mail.send(msg)
        
        # Remove the item from the items_for_sale collection
        mongo.db.items_for_sale.delete_one({'_id': ObjectId(item_id)})
        flash("You have alerted the seller you are Interested in this item!")
        return redirect(url_for("market_page"))

    else:
        # Provides the user with error message
        flash("Item could not be found. Please try again later")
        return redirect(url_for("market_page"))

@app.route("/move_to_market", methods=["GET", "POST"])
def move_to_market():
    """
    Moves an item to the items for sale collection.

    Returns:
        Redirects to the profile page after moving the item.
    """

    # Retrieves the item id from html page and finds item within pending_items db
    item_id = request.form.get("item-id")
    item = mongo.db.pending_items.find_one({'_id': ObjectId(item_id)})

    if item:
        # Insert the item into the items_for_sale collection
        mongo.db.items_for_sale.insert_one(item)
        
        # Remove the item from the pending_items collection
        mongo.db.pending_items.delete_one({'_id': ObjectId(item_id)})
        flash("Item has been placed back on the Market!")
        return redirect(url_for("profile"))

    else:
        # Provides the user with error message
        flash("Item could not be found. Please try again later")
        return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
