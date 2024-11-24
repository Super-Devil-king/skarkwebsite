from flask import Flask, request, jsonify, render_template, session
import pymysql

import random
import string

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.nn.utils.rnn import pad_sequence
from collections import Counter

app = Flask(__name__)
app.secret_key = 'your_secret_key'


def create_connection():
    host = "SkarkWeb.mysql.pythonanywhere-services.com"
    root = "SkarkWeb"
    pass_in = "#Ranbir195"
    db = "SkarkWeb$Skark_bank"

    connection = pymysql.connect(
        host=host,
        user=root,
        password=pass_in,
        port=3306,
        database=db,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:

            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
            cursor.execute(f"USE {db}")

        connection.commit()
        connection.select_db(db)

    except Exception as e:
        f"Error: {e}"

    return connection


def create_tables():
    connection = create_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS AdminData (
                Adminname VARCHAR(255) NOT NULL,
                Pin VARCHAR(255) NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS UserData (
                Username VARCHAR(255) NOT NULL,
                Password VARCHAR(255) NOT NULL,
                mPin VARCHAR(4) DEFAULT ' ',
                Balance DECIMAL(10, 2) DEFAULT 0.00
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Requests (
                Username VARCHAR(255) NOT NULL,
                Updation VARCHAR(255) NOT NULL,
                Action VARCHAR(20) DEFAULT 'Pending'
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS UserFeedback (
                Username VARCHAR(255) NOT NULL,
                Name VARCHAR(255) NOT NULL,
                Age INT,
                Gender VARCHAR(10),
                Q1 VARCHAR(10),
                Q2 VARCHAR(10),
                Q3 TEXT,
                Mobile_Number VARCHAR(15)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Transactions (
                Sender VARCHAR(255) NOT NULL,
                Recipient VARCHAR(255) NOT NULL,
                Amount DECIMAL(10, 2) NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Feedbacks (
                Username VARCHAR(255) NOT NULL,
                Name VARCHAR(255) NOT NULL,
                Age INT,
                Gender VARCHAR(10),
                Q3 TEXT,
                Mobile_Number VARCHAR(15)
            );
            """)
        connection.commit()

    finally:
        connection.close()


def load_data():
    connection = create_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM AdminData")
            cursor.execute("SELECT * FROM UserData")
            cursor.execute("SELECT * FROM Requests")
            cursor.execute("SELECT * FROM UserFeedback")
            cursor.execute("SELECT * FROM Transactions")
            cursor.execute("SELECT * FROM Feedbacks")

    except pymysql.MySQLError as e:
        f"Error loading data: {e}"

    finally:
        connection.close()


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/get_response', methods=['GET', 'POST'])
def get_response():
    if request.method == 'POST':
        connection = create_connection()

        user_request = request.json.get("message").strip()

        with connection.cursor() as cursor:

            if 'state' not in session:
                session['state'] = 'welcome'

            state = session['state']
            response = ""
            menu = ""
            global amount
            if state == 'welcome':
                if user_request.lower() in ["hello", "hi", "hey"]:
                    response = "Welcome to S.K.A.R.K bank system"
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                else:
                    response = "Try saying 'hello'"
                    session['state'] = 'welcome'

            elif state == 'main_menu':
                if user_request.lower() in ["1", "user login"]:
                    response = "User Login selected."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'
                elif user_request.lower() in ["2", "admin login"]:

                    response = "Admin Login selected."
                    menu = get_admin_login_menu()
                    session['state'] = 'admin_login'

                elif user_request.lower() in ["3", "logout"]:
                    response = "Goodbye!"
                    session.clear()
                else:
                    response = "Invalid choice."
                    menu = get_main_menu()
                    session['state'] = 'main_menu'

            elif state == 'admin_login':

                cursor.execute("SELECT Adminname FROM AdminData")
                adminnames = [row['Adminname'] for row in cursor.fetchall()]

                if user_request.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_main_menu()
                    session['state'] = 'main_menu'

                elif user_request in adminnames:
                    session['adminname'] = user_request
                    menu = get_admin_password_menu()
                    session['state'] = 'admin_password'

                else:
                    response = "You does not have admin access."
                    menu = get_main_menu()
                    session['state'] = 'main_menu'

            elif state == 'admin_password':

                cursor.execute(
                    "SELECT Pin FROM AdminData WHERE Adminname = %s", (session['adminname'],))
                pin = cursor.fetchone()['Pin']

                if user_request.lower() in ["exit", "e"]:
                    menu = get_main_menu()
                    session['state'] = 'main_menu'

                elif user_request == pin:
                    session['state'] = 'admin_menu'
                    menu = get_admin_menu()

                else:
                    response = "Incorrect pin. Please try again."

            elif state == 'admin_menu':
                if user_request in ["1", "view users"]:
                    menu = get_view_user_menu()
                    session['state'] = 'view_user'
                elif user_request in ["2", "edit users"]:
                    menu = get_edit_user_menu()
                    session['state'] = 'edit_user'
                elif user_request in ["3", "delete users"]:
                    menu = get_delete_user_menu()
                    session['state'] = 'delete_user'
                elif user_request in ["4", "view requests"]:
                    menu = get_view_user_request_menu()
                    session['state'] = 'view_user_request'
                elif user_request in ["5", "view feedbacks"]:
                    menu = get_view_feedback_chart_menu()
                    session['state'] = 'view_feedback_chart'
                elif user_request in ["6", "logout"]:
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                else:
                    response = "Invalid input. Please try again."
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'

            elif state == 'view_user':
                menu = get_admin_menu()
                session['state'] = 'admin_menu'

            elif state == 'edit_user':

                global selected_user
                selected_user = user_request
                cursor.execute("SELECT Username FROM UserData")
                usernames = [row['Username'] for row in cursor.fetchall()]

                if selected_user.lower() in ["exit", "e"]:
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'

                elif selected_user in usernames:
                    response = "User found."
                    menu = get_edit_selected_user_menu()
                    session['state'] = 'edit_selected_user'

                else:
                    response = "User not found. Please try again."
                    menu = get_edit_user_menu()
                    session['state'] = 'edit_user'

            elif state == 'edit_selected_user':

                global update_column
                update_column = user_request

                if update_column.lower() in ["exit", "e"]:
                    menu = get_edit_user_menu()
                    session['state'] = 'edit_user'
                elif update_column.lower() in ["1", "username", "2", "name", "3", "age", "4", "gender", "5", "mobile"]:
                    menu = get_selected_user()
                    session['state'] = 'selected_user'
                else:
                    response = "Enter a valid input"
                    menu = get_edit_selected_user_menu()
                    session['state'] = 'edit_selected_user'

            elif state == "selected_user":

                user_new_value = user_request
                cursor.execute("SELECT Username FROM UserData")
                edit_usernames = [row['Username'] for row in cursor.fetchall()]

                if update_column in ["1", "change username"]:

                    if user_new_value.lower() in ["exit", "e"]:
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    elif user_new_value in edit_usernames:
                        response = "Username already exists. Please try again."
                        menu = get_selected_user()
                        session['state'] = 'selected_user'
                    else:
                        update_user_data(
                            "Username", selected_user, user_new_value)
                        response = "User Data Updated."
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'

                elif update_column in ["2", "name"]:

                    if user_new_value.lower() in ["exit", "e"]:
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    else:
                        update_user_data("Name", selected_user, user_new_value)
                        response = "User Data Updated."
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'

                elif update_column in ["3", "age"]:

                    if user_new_value.lower() in ["exit", "e"]:
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    elif user_new_value.isdigit() and 18 <= int(user_new_value) <= 125:
                        update_user_data("Age", selected_user,
                                         int(user_new_value))
                        response = "User Data Updated."
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    else:
                        response = "Invalid input. Age must be a number."
                        menu = get_edit_selected_user_menu()
                        session['state'] = 'edit_selected_user'

                elif update_column in ["4", "gender"]:

                    if user_new_value.lower() in ["exit", "e"]:
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    elif user_new_value.lower() in ["m", "male"]:
                        user_new_value = "m"
                        update_user_data(
                            "Gender", selected_user, user_new_value)
                        response = "User Data Updated."
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    elif user_new_value.lower() in ["f", "female"]:
                        user_new_value = "f"
                        update_user_data(
                            "Gender", selected_user, user_new_value)
                        response = "User Data Updated."
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    else:
                        response = "Invalid input. Gender must be 'm' or 'f'."
                        menu = get_edit_selected_user_menu()
                        session['state'] = 'edit_selected_user'

                elif update_column in ["5", "mobile number"]:
                    if user_new_value.lower() in ["exit", "e"]:
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    elif user_new_value.isdigit() and len(user_new_value) == 10:
                        update_user_data(
                            "Mobile_Number", selected_user, user_new_value)
                        response = "User Data Updated."
                        menu = get_edit_user_menu()
                        session['state'] = 'edit_user'
                    else:
                        response = "Invalid input. Mobile number must be a 10-digit number."
                        menu = get_edit_selected_user_menu()
                        session['state'] = 'edit_selected_user'

            elif state == 'delete_user':

                global del_username
                del_username = user_request
                cursor.execute("SELECT Username FROM UserData")
                delete_usernames = [row['Username']
                                    for row in cursor.fetchall()]

                if del_username.lower() in ["e", "exit"]:
                    menu = get_admin_menu()
                    session['state'] = "admin_menu"
                elif del_username in delete_usernames:
                    menu = get_admin_confirm_pin()
                    session['state'] = "admin_confirm_pin"
                else:
                    response = "Enter a valid username."
                    menu = get_delete_user_menu()
                    session['state'] = 'delete_user'

            elif state == "admin_confirm_pin":

                cursor.execute("SELECT Pin FROM AdminData")
                admin_pins = [row['Pin'] for row in cursor.fetchall()]

                if user_request.lower() in ["e", "exit"]:
                    menu = get_admin_menu()
                    session['state'] = "admin_menu"

                elif user_request in admin_pins:

                    cursor.execute(
                        "DELETE FROM UserData WHERE Username=%s", (del_username,))
                    cursor.execute(
                        "DELETE FROM UserFeedback WHERE Username=%s", (del_username,))
                    cursor.execute(
                        "DELETE FROM Feedbacks WHERE Username=%s", (del_username,))
                    cursor.execute(
                        "DELETE FROM Transactions WHERE Sender=%s", (del_username,))
                    cursor.execute(
                        "DELETE FROM Transactions WHERE Recipient=%s", (del_username,))
                    cursor.execute(
                        "DELETE FROM Requests WHERE Username=%s", (del_username,))
                    connection.commit()

                    response = "Deletion Successful."
                    menu = get_delete_user_menu()
                    session['state'] = "delete_user"
                else:
                    response = "Enter a valid username."
                    menu = get_delete_user_menu()
                    session['state'] = 'delete_user'

            elif state == 'view_user_request':

                global requesting_user
                requesting_user = user_request
                session['requesting_user'] = requesting_user

                cursor.execute(
                    "SELECT Username FROM Requests WHERE Action = 'Pending'")
                all_usernames = [row["Username"] for row in cursor.fetchall()]

                if requesting_user.lower() in ["exit", "e"]:
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'
                elif requesting_user in all_usernames:
                    menu = get_select_request_menu()
                    session['state'] = 'select_request'
                else:
                    response = "<br>Username not found in requests."
                    menu = get_view_user_request_menu()
                    session['state'] = 'view_user_request'

            elif state == 'select_request':
                cursor.execute(
                    "SELECT Updation FROM Requests WHERE Action = 'Pending' AND Username = %s", (requesting_user,))
                updations = [row['Updation'].split()[0].lower()
                             for row in cursor.fetchall()]

                if user_request.lower() in ["exit", "e"]:
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'
                elif user_request.lower() not in updations:
                    response = "Invalid input. Please try again."
                    menu = get_select_request_menu()
                    session['state'] = 'select_request'
                else:
                    menu = get_action_menu()
                    session['state'] = 'action_menu'

            elif state == 'action_menu':

                action = user_request

                if user_request.lower() in ["exit", "e"]:
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'
                elif action in ['1', 'accept']:
                    cursor.execute(
                        "SELECT Updation, Action FROM Requests WHERE Username = %s", (requesting_user,))
                    request_data = cursor.fetchone()
                    if request_data:
                        column = request_data["Updation"].split()[0]
                        user_new_value = request_data["Updation"].split(
                            ":")[-1]
                        update_user_data(
                            column, requesting_user, user_new_value)
                    cursor.execute(
                        "UPDATE Requests SET Action = %s WHERE Username = %s", ('Accepted', requesting_user))
                    connection.commit()
                    response = f"Request for {requesting_user} accepted and data updated."
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'
                elif action in ['2', 'decline']:
                    cursor.execute(
                        "UPDATE Requests SET Action = %s WHERE Username = %s", ('Rejected', requesting_user))
                    connection.commit()
                    response = f"Request for {requesting_user} declined."
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'
                else:
                    response = "Invalid action."
                    menu = get_action_menu()
                    session['state'] = 'action_menu'

            elif state == 'view_feedback_chart':

                if user_request.lower() in ["exit", "e"]:
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'
                elif user_request in ["1", "survey 1"]:
                    menu = get_q1_menu()
                    session['state'] = 'view_feedbacks'

                elif user_request in ["2", "survey 2"]:
                    menu = get_q2_menu()
                    session['state'] = 'view_feedbacks'

                elif user_request in ["3", "survey 3"]:
                    menu = get_q3_menu()
                    session['state'] = 'view_feedbacks'

                elif user_request in ["4", "all"]:

                    menu = get_feedback_table_menu()
                    session['state'] = 'view_feedback_table'

                elif user_request.lower() in ["exit", "e"]:
                    menu = get_admin_menu()
                    session['state'] = 'admin_menu'

                else:
                    response = "Enter a valid input"
                    menu = get_view_feedback_chart_menu()
                    session['state'] = 'view_feedback_chart'

            elif state == 'view_feedback_table':
                menu = get_view_feedback_chart_menu()
                session['state'] = 'view_feedback_chart'

            elif state == 'view_feedbacks':
                menu = get_view_feedback_chart_menu()
                session['state'] = 'view_feedback_chart'

            elif state == "feedback_exit":

                menu = get_view_feedback_chart_menu()
                session['state'] = 'view_feedback_chart'

            elif state == 'user_login_signup':

                if user_request.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                elif user_request.lower() in ["1", "login"]:
                    menu = get_login_username()
                    session['state'] = 'login_username_check'
                elif user_request.lower() in ["2", "signup"]:
                    menu = get_signup_username()
                    session['state'] = 'signup_username_check'
                else:
                    response = "Invalid choice."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'

            elif state == 'signup_username_check':
                cursor.execute("SELECT Username FROM UserData")
                usernames = [row['Username'] for row in cursor.fetchall()]
                if user_request in usernames:
                    response = "User already exists. Try logging in."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'
                elif user_request.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'
                else:
                    session['username'] = user_request
                    menu = get_user_name()
                    session['state'] = 'signup_name'

            elif state == 'signup_name':
                global name
                name = user_request
                if name.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'
                else:
                    menu = get_user_age()
                    session['state'] = 'signup_age'

            elif state == 'signup_age':
                global age
                age = user_request
                if age.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'
                elif not age.isdigit() or not (18 <= int(age) <= 125):
                    response = (
                        "You are not eligible to open an account. Redirecting to signup menu...")
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                else:
                    menu = get_user_gender()
                    session['state'] = 'signup_gender'

            elif state == 'signup_gender':
                global gender
                gender = user_request.lower()
                if gender.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'
                elif gender in ["m", "male"]:
                    gender = "m"
                    menu = get_user_password()
                    session['state'] = 'signup_password'
                elif gender in ["f", "female"]:
                    gender = "f"
                    menu = get_user_password()
                    session['state'] = 'signup_password'
                else:
                    response = "Enter valid input"
                    menu = get_user_gender()
                    session['state'] = 'signup_gender'

            elif state == 'signup_password':
                global password
                password = user_request

                has_upper = any(char.isupper() for char in password)
                has_lower = any(char.islower() for char in password)
                has_special = any(char in "@#_:" for char in password)
                has_number = any(char.isdigit() for char in password)

                if user_request.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'

                elif password.lower() == "use":

                    username = session['username']
                    password = session['suggested_password']
                    response = "Signup successful."
                    cursor.execute("INSERT INTO UserData (Username, Password, mPin, Balance) VALUES (%s, %s, %s, %s)",
                                   (username, password, "", 0))
                    cursor.execute("INSERT INTO UserFeedback (Username, Name, Age, Gender, Q1, Q2, Q3, Mobile_Number) "
                                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                   (username, name, age, gender, None, None, None, None))
                    cursor.execute("INSERT INTO Feedbacks (Username, Name, Age, Gender, Q3, Mobile_number)"
                                   "VALUES (%s, %s, %s, %s, %s, %s)",
                                   (username, password, age, gender, None, None))
                    connection.commit()
                    menu = get_user_menu()
                    session['state'] = 'user_menu'

                elif len(password) >= 8 and has_upper and has_lower and has_special and has_number:
                    username = session['username']
                    response = "Signup successful."
                    cursor.execute("INSERT INTO UserData (Username, Password, mPin, Balance) VALUES (%s, %s, %s, %s)",
                                   (username, password, "", 0))
                    cursor.execute("INSERT INTO UserFeedback (Username, Name, Age, Gender, Q1, Q2, Q3, Mobile_Number) "
                                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                   (username, name, age, gender, None, None, None, None))
                    cursor.execute("INSERT INTO Feedbacks (Username, Name, Age, Gender, Q3, Mobile_number)"
                                   "VALUES (%s, %s, %s, %s, %s, %s)",
                                   (username, password, age, gender, None, None))
                    connection.commit()
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                else:
                    response = "Invalid Password."
                    menu = get_user_password()
                    session['state'] = 'signup_password'

            elif state == 'login_username_check':

                cursor.execute("SELECT Username FROM UserData")
                usernames = [row['Username'] for row in cursor.fetchall()]

                if user_request.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'

                elif user_request in usernames:
                    session['username'] = user_request
                    menu = get_login_password()
                    session['state'] = 'user_login_password'

                else:
                    response = "UserID not found. Please try again."
                    menu = get_user_login_signup_menu()
                    session['state'] = 'user_login_signup'

            elif state == 'user_login_password':

                if user_request.lower() in ["exit", "e"]:
                    response = "Returning to main menu..."
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                else:
                    username = session["username"]
                    query = "SELECT Password FROM UserData WHERE Username = %s"
                    cursor.execute(query, username)
                    pass_in = cursor.fetchone()["Password"]

                    if pass_in == user_request:
                        response = "Login successful!"
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    else:
                        response = "Invalid password. Please try again."
                        menu = get_login_password()
                        session['state'] = 'user_login_password'

            elif state == 'user_menu':

                if user_request.lower() in ['1', 'transaction menu']:
                    menu = get_transaction_menu()
                    session['state'] = 'transaction_menu'
                elif user_request.lower() in ['2', "calculate fd"]:
                    menu = get_calculate_fd_menu()
                    session['state'] = 'calculate_fd'
                elif user_request.lower() in ['3', "loan application"]:
                    menu = get_loan_application_menu()
                    session['state'] = 'loans'
                elif user_request.lower() in ['4', "currency exchange"]:
                    menu = get_currency_exchange_menu()
                    session['state'] = 'rate_conversion'
                elif user_request.lower() in ['5', "create mpin"]:
                    menu = get_create_mpin_menu()
                    session['action'] = 'user_menu'
                    session['state'] = 'verify_password'
                elif user_request.lower() in ['6', "user profile"]:
                    menu = get_user_profile()
                    session['state'] = 'profile'
                elif user_request.lower() in ['7', "request change"]:
                    menu = get_request_change_menu()
                    session['state'] = 'update_info'
                elif user_request.lower() in ['8', "feedbacks"]:
                    menu = get_answer_one()
                    session['state'] = 'answer_one'
                elif user_request.lower() in ['9', "bank policies"]:
                    menu = get_bank_policies()
                    session['state'] = 'policies'
                elif user_request.lower() in ['10', "logout"]:
                    response = "You have successfully logged out."
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                else:
                    response = "Invalid choice."
                    menu = get_user_menu()

            elif state == 'transaction_menu':

                username = session['username']

                query = "SELECT mPin FROM UserData WHERE Username = %s"
                cursor.execute(query, (username,))
                user_mpin = cursor.fetchone()['mPin']

                if user_request.lower() in ['1', 'deposit']:
                    session['action'] = 'transaction_menu'
                    if user_mpin is None or user_mpin == "":
                        response = "You must create an mPin to access this feature."
                        menu = get_create_mpin_menu()
                        session['state'] = 'verify_password'
                    else:
                        menu = get_deposit_menu()
                        session['state'] = 'deposit_amount_check'
                elif user_request.lower() in ['2', 'withdraw']:
                    session['action'] = 'transaction_menu'
                    if user_mpin is None or user_mpin == "":
                        response = "You must create an mPin to access this feature."
                        menu = get_create_mpin_menu()
                        session['state'] = 'verify_password'
                    else:
                        menu = get_withdraw_menu()
                        session['state'] = 'withdraw_amount_check'
                elif user_request.lower() in ['3', 'send money']:
                    session['action'] = 'transaction_menu'
                    if user_mpin is None or user_mpin == "":
                        response = "You must create an mPin to access this feature."
                        menu = get_create_mpin_menu()
                        session['state'] = 'verify_password'
                    else:
                        menu = get_send_money_menu()
                        session['state'] = 'send_money'

                elif user_request.lower() in ['4', 'check balance']:
                    menu = get_check_balance_menu()
                    session['state'] = 'check_balance'
                elif user_request.lower() in ['5', "view transaction history"]:
                    menu = get_view_transaction_history_menu()
                    session['state'] = 'transaction_history'
                elif user_request.lower() in ['6', 'exit', "e"]:
                    response = "Returning to user menu..."
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                else:
                    response = "Invalid choice."
                    menu = get_transaction_menu()

            elif state == 'deposit_amount_check':
                try:

                    amount = user_request
                    if str(amount).lower() in ["exit", "e"]:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    if int(amount) <= 0:
                        response = "Invalid deposit amount. Please enter a positive value."
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    else:
                        session['state'] = 'deposit'
                        menu = get_mpin_amount()
                except ValueError:
                    response = "Invalid amount. Please enter a numeric value."
                    menu = get_deposit_menu()
                    session['state'] = 'deposit_amount_check'

            elif state == "deposit":

                username = session['username']
                if user_request.lower() in ["exit", "e"]:
                    menu = get_transaction_menu()
                    session['state'] = 'transaction_menu'
                else:
                    query = "SELECT mPin, Balance FROM UserData WHERE Username = %s"
                    cursor.execute(query, (username,))
                    user_data = cursor.fetchone()
                    if user_request == user_data['mPin']:
                        new_balance = float(
                            user_data['Balance']) + float(amount)
                        update_query = "UPDATE UserData SET Balance = %s WHERE Username = %s"
                        deposit_query = "INSERT INTO Transactions VALUES (%s, %s, %s)"
                        cursor.execute(
                            update_query, (new_balance, username))
                        cursor.execute(
                            deposit_query, (username, username, float(amount)))
                        connection.commit()
                        response = (f"Successfully deposited <span style='color: white;'>₹{float(amount):.2f}</span>"
                                    f"<br>New balance: <span style='color: white;'>₹{new_balance:.2f}</span>")
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'

                    else:
                        response = "Invalid mPin. Please try again."
                        menu = get_mpin_amount()
                        session['state'] = 'deposit'

            elif state == 'withdraw_amount_check':
                try:
                    amount = user_request
                    if str(amount).lower() in ["exit", "e"]:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    if int(amount) <= 0 or int(amount) > 20000:
                        response = "Invalid withdraw amount"
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    else:
                        session['state'] = 'withdraw'
                        menu = get_mpin_amount()
                except ValueError:
                    response = "Invalid amount. Please enter a numeric value."
                    menu = get_deposit_menu()
                    session['state'] = 'withdraw_amount_check'

            elif state == "withdraw":
                username = session['username']

                if user_request.lower() in ["exit", "e"]:
                    menu = get_transaction_menu()
                    session['state'] = 'transaction_menu'
                else:
                    query = "SELECT mPin, Balance FROM UserData WHERE Username = %s"
                    cursor.execute(query, (username,))
                    user_data = cursor.fetchone()
                    if user_request == user_data['mPin']:
                        new_balance = float(
                            user_data['Balance']) - float(amount)
                        if new_balance >= 0:
                            update_query = "UPDATE UserData SET Balance = %s WHERE Username = %s"
                            withdraw_query = "INSERT INTO Transactions VALUES (%s, %s, %s)"
                            cursor.execute(
                                withdraw_query, (username, username, float(amount)))
                            cursor.execute(
                                update_query, (new_balance, username))
                            connection.commit()
                            response = (f"Successfully withdrew <span style='color: white;'>₹{float(amount):.2f}</span>"
                                        f"<br>New balance: <span style='color: white;'>₹{new_balance:.2f}</span>")
                            menu = get_transaction_menu()
                            session['state'] = 'transaction_menu'
                        else:
                            response = "Insufficient balance. Please try again."
                            menu = get_withdraw_menu()
                            session['state'] = 'withdraw_amount_check'
                    else:
                        response = "Invalid mPin. Please try again."
                        menu = get_mpin_amount()
                        session['state'] = 'withdraw'

            elif state == "send_money":
                global recipient_username
                recipient_username = user_request
                if recipient_username.lower() in ["exit", "e"]:
                    menu = get_transaction_menu()
                    session['state'] = 'transaction_menu'
                else:
                    query = "SELECT * FROM UserData WHERE Username = %s"
                    cursor.execute(query, (recipient_username,))
                    recipient_data = cursor.fetchone()

                    if not recipient_data:
                        response = "Recipient not found."
                        menu = get_send_money_menu()
                        session['state'] = 'send_money'
                    elif recipient_username.lower() in ["e", "exit"]:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    else:
                        menu = get_send_money_amount()
                        session['state'] = 'send_money_amount'

            elif state == "send_money_amount":
                try:
                    amount = user_request
                    if str(amount).lower() in ["exit", "e"]:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    elif int(amount) <= 0 or int(amount) > 10000:
                        response = "The Transaction limit is 10000."
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                    else:
                        session['state'] = 'send_mpin'
                        menu = get_user_mpin()
                except ValueError:
                    response = "Invalid amount. Please enter a numeric value."
                    menu = get_send_money_amount()
                    session['state'] = 'send_money_amount'

            elif state == "send_mpin":
                username = session['username']
                query = "SELECT mPin, Balance FROM UserData WHERE Username = %s"
                cursor.execute(query, (username,))
                sender_data = cursor.fetchone()

                cursor.execute(
                    "SELECT Balance FROM UserData WHERE Username = %s", (recipient_username,))
                recipient_data = cursor.fetchone()

                if user_request.lower() in ["exit", "e"]:
                    menu = get_transaction_menu()
                    session['state'] = 'transaction_menu'

                elif recipient_data is None:
                    response = "Recipient not found. Transaction failed."
                    menu = get_send_money_menu()
                    session['state'] = 'send_money'

                else:
                    stored_mpin = sender_data['mPin']
                    username = session['username']

                    if user_request != stored_mpin:
                        response = "Invalid mPin. Transaction failed."
                        menu = get_send_money_menu()
                        session['state'] = 'send_money'

                    if user_request.lower() in ["exit", "e"]:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'

                    elif float(amount) > float(sender_data['Balance']):
                        response = "Insufficient balance. Transaction failed."
                        menu = get_send_money_menu()
                        session['state'] = 'send_money'
                    else:
                        new_sender_balance = float(
                            sender_data['Balance']) - float(amount)
                        new_recipient_balance = float(
                            recipient_data['Balance']) + float(amount)

                        update_sender_query = "UPDATE UserData SET Balance = %s WHERE Username = %s"
                        cursor.execute(update_sender_query,
                                       (new_sender_balance, username))

                        update_recipient_query = "UPDATE UserData SET Balance = %s WHERE Username = %s"
                        cursor.execute(update_recipient_query,
                                       (new_recipient_balance, recipient_username))
                        transaction_query = ("INSERT INTO Transactions "
                                             "VALUES (%s, %s, %s)")
                        cursor.execute(transaction_query,
                                       (username, recipient_username, int(amount)))

                        connection.commit()
                        response = f"Successfully sent <span style='color: white;'>₹{float(amount):.2f}</span> to <span style='color: white;'>{recipient_username}</span>."
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'

            elif state == "check_balance":

                menu = get_transaction_menu()
                session['state'] = 'transaction_menu'

            elif state == "transaction_history":
                menu = get_transaction_menu()
                session['state'] = 'transaction_menu'

            elif state == "calculate_fd":
                global principal
                principal = user_request
                if principal.lower() in ["exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                elif principal.isdigit():
                    principal = float(principal)
                    menu = get_tenure()
                    session['state'] = 'tenure'
                else:
                    response = "Invalid principal amount. Please try again."
                    menu = get_calculate_fd_menu()
                    session['state'] = 'calculate_fd'

            elif state == "tenure":
                tenure = user_request
                username = session['username']

                if user_request.lower() in ["exit", "e"]:
                    menu = get_main_menu()
                    session['state'] = 'main_menu'
                elif tenure not in ["1", "3", "5"]:
                    response = "Invalid tenure. Please try again."
                    menu = get_calculate_fd_menu()
                    session['state'] = 'calculate_fd'
                else:
                    cursor.execute(
                        "SELECT Age FROM UserFeedback WHERE Username = %s", (username,))
                    user_age = cursor.fetchone()['Age']
                    is_senior_citizen = int(user_age) > 56
                    rates = {"private": {'1': 6.0, '3': 6.5, '5': 7.0}}
                    if is_senior_citizen:
                        interest_rate = rates["private"][tenure] + 0.5
                    else:
                        interest_rate = rates["private"][tenure]
                    tenure = int(tenure)
                    interest_earned = (
                                              principal * interest_rate * tenure) / 100
                    maturity_amount = principal + interest_earned
                    response = ("--- Fixed Deposit Summary ---<br>"
                                f"<br>Principal Amount: <span style='color: white;'>₹{principal:.2f}</span>"
                                f"<br>Interest Rate: <span style='color: white;'>{interest_rate:.2f}%</span>"
                                f"<br>Tenure: <span style='color: white;'>{tenure} years</span>"
                                f"<br>Interest Earned: <span style='color: white;'>₹{interest_earned:.2f}</span>"
                                f"<br>Maturity Amount: <span style='color: white;'>₹{maturity_amount:.2f}</span>")
                    menu = get_user_exit()
                    session['state'] = 'user_exit'

            elif state == "loans":
                loan_types = {
                    '1': "Personal Loan",
                    '2': "Home Loan",
                    '3': "Car Loan",
                    '4': "Education Loan",
                    '5': "Business Loan"
                }

                if user_request not in loan_types:
                    if user_request.lower() in ["exit", "e"]:

                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    else:
                        response = "Invalid choice. Please select a valid loan type."
                        menu = get_loan_application_menu()
                        session['state'] = 'loans'
                else:
                    loan_type = loan_types[user_request]
                    steps = {
                        "Personal Loan": [
                            "Research and Compare lenders.",
                            "Check eligibility based on income and credit score.",
                            "Gather documents: Username proof, income proof, bank statements.",
                            "Fill the loan application form.",
                            "Submit required documents.",
                            "Loan processing and verification of documents.",
                            "Approval and disbursement of loan amount."
                        ],
                        "Home Loan": [
                            "Get pre-approval for a loan.",
                            "Choose between fixed or floating interest rates.",
                            "Check eligibility based on income and credit score.",
                            "Gather documents: property papers, Username proof, income proof.",
                            "Submit home loan application.",
                            "Property evaluation by the lender.",
                            "Loan processing and verification of documents.",
                            "Receive sanction letter and loan disbursement."
                        ],
                        "Car Loan": [
                            "Research and compare car loan offers.",
                            "Check eligibility based on income and credit score.",
                            "Gather documents: Username proof, income proof, car details.",
                            "Fill out the car loan application form.",
                            "Submit application with required documents.",
                            "Loan processing and verification of credit history.",
                            "Receive loan sanction letter and disbursement."
                        ],
                        "Education Loan": [
                            "Research education loan options.",
                            "Check eligibility based on the academic institution and course.",
                            "Gather documents: admission proof, Username proof, income proof.",
                            "Fill out the education loan application form.",
                            "Submit application with required documents.",
                            "Loan verification and assessment.",
                            "Receive sanction letter and loan disbursement."
                        ],
                        "Business Loan": [
                            "Research business loan options.",
                            "Prepare a solUsername business plan outlining the loan usage.",
                            "Check eligibility based on business turnover and credit score.",
                            "Gather documents: Registration, Username proof, financial statements.",
                            "Submit application form.", "Due diligence by the lender.",
                            "Receive approval and loan disbursement."
                        ]
                    }

                    response = f"--- {loan_type} Application Process ---<br>"
                    for i, step in enumerate(steps[loan_type], start=1):
                        response += f"<br>{i}. <span style='color: white;'>{step}</span>"

                    menu = get_loan_application_menu()
                    session['state'] = 'loans'

            elif state == "user_exit":

                menu = get_user_menu()
                session['state'] = 'user_menu'

            elif state == "verify_password":
                username = session['username']
                cursor.execute(
                    "SELECT Password FROM UserData WHERE Username = %s", (username,))
                pass_in = cursor.fetchone()['Password']

                if user_request.lower() in ["exit", "e"]:
                    if session['action'] == 'user_menu':
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    else:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'

                elif user_request != pass_in:
                    response = "Entered password is incorrect."
                    menu = get_create_mpin_menu()
                    session['state'] = 'verify_password'

                else:
                    cursor.execute(
                        "SELECT mPin FROM UserData WHERE Username = %s", (username,))
                    user_mpin_db = cursor.fetchone()['mPin']

                    if user_mpin_db is None or user_mpin_db == "":
                        menu = get_create_mpin()
                        session['state'] = 'create_mpin'
                    elif session['action'] == 'user_menu':
                        menu = get_updated_mpin()
                        session['state'] = 'updated_mpin'

            elif state == "create_mpin":
                username = session['username']
                user_mpin = user_request
                if user_mpin.lower() in ["exit", "e"]:
                    if session['action'] == 'user_menu':
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    else:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                if len(user_mpin) == 4 and all(char in "0123456789" for char in user_mpin):
                    cursor.execute(
                        "UPDATE UserData SET mPin = %s WHERE Username = %s", (user_mpin, username))
                    connection.commit()
                    response = "mPin created successfully!"
                    if session['action'] == 'user_menu':
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    else:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                else:
                    response = "Invalid mPin. Please enter a 4-digit number."
                    menu = get_create_mpin()
                    session['state'] = 'create_mpin'

            elif state == "updated_mpin":
                username = session['username']
                user_mpin = user_request
                cursor.execute(
                    "SELECT mPin FROM UserData WHERE Username = %s", (username,))
                old_mpin = cursor.fetchone()['mPin']
                if user_mpin.lower() in ["exit", "e"]:
                    if session['action'] == 'user_menu':
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    else:
                        menu = get_transaction_menu()
                        session['state'] = 'transaction_menu'
                elif len(user_mpin) == 4 and all(char in "0123456789" for char in user_mpin) and user_mpin != old_mpin:
                    cursor.execute(
                        "UPDATE UserData SET mPin = %s WHERE Username = %s", (user_mpin, username))
                    connection.commit()
                    response = "mPin updated successfully!"
                    menu = get_transaction_menu()
                    session['state'] = 'transaction_menu'
                else:
                    response = "Invalid mPin. Please enter a 4-digit number."
                    menu = get_updated_mpin()
                    session['state'] = 'updated_mpin'

            elif state == 'rate_conversion':

                global rate_number
                rate_number = user_request

                if rate_number in ['1', '2', '3', '4', '5']:
                    menu = get_rate_conversion()
                    session['state'] = 'converted_amount'
                elif rate_number.lower() in ['6', "exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                else:
                    response = "Invalid choice. Please try again."
                    menu = get_currency_exchange_menu()
                    session['state'] = 'rate_conversion'

            elif state == 'converted_amount':
                amount = user_request
                if int(amount) < 0:
                    response = "Invalid amount. Please enter a positive number."
                    menu = get_currency_exchange_menu()
                    session['state'] = 'rate_conversion'
                else:
                    exchange_rates = {
                        '1': 0.012,
                        '2': 0.0096,
                        '3': 0.011,
                        '4': 1.63,
                        '5': 0.011
                    }
                    converted_amount = float(
                        amount) * exchange_rates[rate_number]
                    response = f"Converted Amount: <span style='color: white;'>{converted_amount:.2f}</span>"
                    menu = get_currency_exchange_menu()
                    session['state'] = 'rate_conversion'

            elif state == 'profile':
                username = session['username']
                cursor.execute(
                    "SELECT * FROM UserData WHERE Username = %s", (username,))
                mPin = cursor.fetchone()["mPin"]
                cursor.execute(
                    "SELECT Password FROM UserData WHERE Username = %s", (username,))
                password = cursor.fetchone()["Password"]
                if user_request == mPin:

                    response = f"Password: <span style='color: white;'>{password}</span>"
                    menu = get_profile_exit()
                    session['state'] = 'profile_exit'
                elif user_request.lower() in ["exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                else:
                    response = "Enter a valid input"
                    menu = get_user_profile()
                    session['state'] = 'profile'

            elif state == 'profile_exit':
                menu = get_user_profile()
                session['state'] = 'profile'

            elif state == "answer_one":
                global answers
                answers = []
                if user_request.lower() in ["exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                elif user_request.lower() in ['y', 'n']:
                    answers.append(user_request.lower())
                    menu = get_answer_two()
                    session['state'] = 'answer_two'
                else:
                    menu = get_answer_one()
                    session['state'] = 'answer_one'

            elif state == "answer_two":
                if user_request.lower() in ["exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                elif user_request.isdigit() and 0 <= int(user_request) <= 5:
                    answers.append(user_request.strip())
                    menu = get_answer_three()
                    session['state'] = 'answer_three'
                else:
                    menu = get_answer_two()
                    session['state'] = 'answer_two'

            elif state == "answer_three":
                username = session['username']
                if user_request:
                    answers.append(user_request.lower())
                    cursor.execute(
                        "SELECT Mobile_Number FROM UserFeedback WHERE Username = %s", (username,))
                    m_number = cursor.fetchone()["Mobile_Number"]
                    if user_request.lower() in ["exit", "e"]:
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                    elif m_number is None or m_number == "" or m_number == " ":
                        menu = get_mnum()
                        session['state'] = 'save_feedbacks'
                    else:
                        response = "Thank you for your feedback."
                        menu = get_user_menu()
                        session['state'] = 'user_menu'
                else:
                    menu = get_answer_three()
                    session['state'] = 'answer_three'

            elif state == "save_feedbacks":
                username = session['username']
                if not user_request:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                elif user_request.lower() in ["exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'
                elif len(user_request) == 10 and user_request.isdigit():
                    try:
                        query1 = "UPDATE UserFeedback SET Q1 = %s, Q2 = %s, Q3 = %s, Mobile_Number = %s " \
                                 "WHERE Username = %s"
                        query2 = "UPDATE Feedbacks SET Q3 = %s, Mobile_Number = %s WHERE Username = %s"
                        cursor.execute(
                            query1, (answers[0], answers[1], answers[2], user_request, username))
                        cursor.execute(
                            query2, (answers[2], user_request, username))
                        connection.commit()
                        response = "Thank you for your feedback!"
                    except Exception as e:
                        response = f"An error occurred: {e}"
                    finally:

                        menu = get_user_menu()
                        session['state'] = 'user_menu'

            elif state == "update_info":
                username = session['username']
                global field
                field = user_request

                if field.lower() in ["username", "name", "age", "gender", "mobile number", "password"] or field in ["1",
                                                                                                                    "2",
                                                                                                                    "3",
                                                                                                                    "4",
                                                                                                                    "5",
                                                                                                                    "6"]:
                    options = {
                        "1": "username",
                        "2": "name",
                        "3": "age",
                        "4": "gender",
                        "5": "mobile number",
                        "6": "password",
                    }
                    field = options[field]
                    query = """
                        SELECT u.*, f.* FROM UserData u JOIN UserFeedback f ON u.Username = f.Username WHERE u.Username = %s
                    """
                    cursor.execute(query, (username,))
                    user_data = cursor.fetchone()

                    if user_data is None:
                        response = "User not found."
                        menu = get_request_change_menu()
                        session['state'] = 'update_info'
                    else:
                        global old_value
                        if field.lower() in ["username", "1"]:
                            old_value = user_data['Username']
                            session['state'] = "new_value"
                        elif field.lower() in ["name", "2"]:
                            old_value = user_data['Name']
                            session['state'] = "new_value"
                        elif field.lower() in ["age", "3"]:
                            old_value = user_data['Age']
                            session['state'] = "new_value"
                        elif field.lower() in ["gender", "4"]:
                            old_value = user_data['Gender']
                            session['state'] = "new_value"
                        elif field.lower() in ["mobile number", "5"]:
                            old_value = user_data['Mobile_Number']
                            session['state'] = "new_value"
                        elif field.lower() in ["password", "6"]:
                            old_value = user_data['Password']
                            session['state'] = "new_value"
                        cursor.execute(
                            "SELECT * FROM Requests WHERE Username = %s AND Updation LIKE %s AND Action = 'Pending'",
                            (username, f"{field.capitalize()} to:%"))
                        existing_requests = cursor.fetchall()

                        if len(existing_requests) > 0:
                            response = f"You have already requested a change in {field.capitalize()}."
                            menu = get_request_change_menu()
                            session['state'] = 'update_info'
                        else:
                            if field != "Password":
                                response = f"Current {field.capitalize()}: <span style='color: white;'>{old_value}</span>"
                                menu = get_new_value()
                            else:
                                menu = get_new_value()

                elif field.lower() in ["7", "delete account"]:
                    response = ("Please contact the Bank through <span style='color: white;'>mail</span>"
                                "or <span style='color: white;'>mobile</span> to delete your account.")
                    menu = get_request_change_menu()
                    session['state'] = "update_info"

                elif field.lower() in ["8", "view requests"]:

                    menu = get_view_requests()
                    session['state'] = 'view_user_requests'

                elif field.lower() in ["9", "exit", "e"]:
                    menu = get_user_menu()
                    session['state'] = 'user_menu'

                else:
                    response = "Invalid field selected."
                    menu = get_request_change_menu()
                    session['state'] = 'update_info'

            elif state == "view_user_requests":
                menu = get_request_change_menu()
                session['state'] = 'update_info'

            elif state == "new_value":
                username = session['username']
                new_value = user_request
                if new_value.lower() in ["exit", "e"]:
                    menu = get_request_change_menu()
                    session['state'] = 'update_info'

                elif old_value == user_request:
                    response = f"Enter a {field.capitalize()} different from the previous one."
                    menu = get_new_value()
                    session['state'] = 'new_value'

                else:
                    if field == "username":
                        cursor.execute("SELECT Username FROM UserData")
                        request_usernames = [row['Username']
                                             for row in cursor.fetchall()]

                        if new_value in request_usernames:
                            response = "User already exists, Enter a different username."
                            menu = get_new_value()
                            session['state'] = 'new_value'
                        else:
                            new_request = (
                                username, f"{field.capitalize()} to: {new_value}", "Pending")
                            cursor.execute(
                                "INSERT INTO Requests (Username, Updation, Action) VALUES (%s, %s, %s)",
                                new_request)
                            connection.commit()
                            response = f"Request sent for {field.capitalize()} change."
                            menu = get_request_change_menu()
                            session['state'] = 'update_info'

                    if field == "name":
                        new_request = (
                            username, f"{field.capitalize()} to: {new_value}", "Pending")
                        cursor.execute(
                            "INSERT INTO Requests (Username, Updation, Action) VALUES (%s, %s, %s)",
                            new_request)
                        connection.commit()
                        response = f"Request sent for {field.capitalize()} change."
                        menu = get_request_change_menu()
                        session['state'] = 'update_info'

                    elif field == "gender":
                        if new_value.lower() not in ["m", "male", "f", "female"]:
                            response = "Enter valid input"
                            menu = get_new_value()
                            session['state'] = 'new_value'
                        else:
                            if new_value.lower() in ["m", "male"]:
                                new_value = "m"
                            elif new_value.lower() in ["f", "female"]:
                                new_value = "f"

                            new_request = (
                                username, f"{field.capitalize()} to: {new_value}", "Pending")
                            cursor.execute(
                                "INSERT INTO Requests (Username, Updation, Action) VALUES (%s, %s, %s)", new_request)
                            connection.commit()

                            response = f"Request sent for {field.capitalize()} change."
                            menu = get_request_change_menu()
                            session['state'] = 'update_info'

                    elif field == "mobile_number":
                        if len(user_request) != 10 and not user_request.isdigit():
                            response = "Enter valid input"
                            menu = get_new_value()
                            session['state'] = 'new_value'
                        else:
                            new_request = (
                                username, f"Mobile_Number to: {new_value}", "Pending")
                            cursor.execute(
                                "INSERT INTO Requests (Username, Updation, Action) VALUES (%s, %s, %s)", new_request)
                            connection.commit()

                            response = f"Request sent for {field.capitalize()} change."
                            menu = get_request_change_menu()
                            session['state'] = 'update_info'

                    elif field == "password":
                        has_upper = any(char.isupper() for char in password)
                        has_lower = any(char.islower() for char in password)
                        has_special = any(char in "@#_:" for char in password)
                        has_number = any(char.isdigit() for char in password)
                        if len(user_request) < 8 or not has_upper or not has_lower or not has_special or not has_number:
                            response = "Enter valid input"
                            menu = get_new_value()
                            session['state'] = 'new_value'
                        else:
                            new_request = (
                                username, f"{field.capitalize()} to: {new_value}", "Pending")
                            cursor.execute(
                                "INSERT INTO Requests (Username, Updation, Action) VALUES (%s, %s, %s)", new_request)
                            connection.commit()

                            response = f"Request sent for {field.capitalize()} change."
                            menu = get_request_change_menu()
                            session['state'] = 'update_info'

                    elif field == "age":
                        if not user_request.isdigit() or not (18 <= int(user_request) <= 125):
                            response = "Enter a valid age (must be a positive number)."
                            menu = get_new_value()
                            session['state'] = 'new_value'
                        else:
                            new_request = (
                                username, f"{field.capitalize()} to: {new_value}", "Pending")
                            cursor.execute(
                                "INSERT INTO Requests (Username, Updation, Action) VALUES (%s, %s, %s)", new_request)
                            connection.commit()

                            response = f"Request sent for {field.capitalize()} change."
                            menu = get_request_change_menu()
                            session['state'] = 'update_info'

            elif state == 'policies':
                menu = get_user_menu()
                session['state'] = 'user_menu'

            return jsonify({"response": response, "menu": menu})


def update_user_data(column, username, new_value):
    connection = create_connection()

    try:
        with connection.cursor() as cursor:
            if column == "Username":
                cursor.execute(
                    "UPDATE UserData SET Username=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE UserFeedback SET Username=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Feedbacks SET Username=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Transactions SET Sender=%s WHERE Sender=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Transactions SET Recipient=%s WHERE Recipient=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Requests SET Username=%s WHERE Username=%s", (new_value, username))

            elif column == "Name":
                cursor.execute(
                    "UPDATE UserFeedback SET Name=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Feedbacks SET Name=%s WHERE Username=%s", (new_value, username))

            elif column == "Age":
                cursor.execute(
                    "UPDATE UserFeedback SET Age=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Feedbacks SET Age=%s WHERE Username=%s", (new_value, username))

            elif column == "Gender":
                cursor.execute(
                    "UPDATE UserFeedback SET Gender=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Feedbacks SET Gender=%s WHERE Username=%s", (new_value, username))

            elif column == "Mobile_Number":
                cursor.execute(
                    "UPDATE UserFeedback SET Mobile_Number=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Feedbacks SET Mobile_Number=%s WHERE Username=%s", (new_value, username))

            elif column == "Q1":
                cursor.execute(
                    "UPDATE UserFeedback SET Q1=%s WHERE Username=%s", (new_value, username))

            elif column == "Q2":
                cursor.execute(
                    "UPDATE UserFeedback SET Q2=%s WHERE Username=%s", (new_value, username))

            elif column == "Q3":
                cursor.execute(
                    "UPDATE UserFeedback SET Q3=%s WHERE Username=%s", (new_value, username))
                cursor.execute(
                    "UPDATE Feedbacks SET Q3=%s WHERE Username=%s", (new_value, username))

        connection.commit()
    finally:
        connection.close()


def get_main_menu():
    return ("1. <span style='color: white;'>User Login</span>"
            "<br>2. <span style='color: white;'>Admin Login</span>"
            "<br>3. <span style='color: white;'>Exit</span>"
            "<br>Enter your choice")


def get_admin_login_menu():
    return ("--- Admin Interface ---<br>"
            "<br>Enter your AdminID")


def get_admin_password_menu():
    return "Enter your Password"


def get_admin_menu():
    return ("--- Admin Menu ---<br>"
            "<br>1. <span style='color: white;'>View Users</span><br>"
            "2. <span style='color: white;'>Edit Users</span><br>"
            "3. <span style='color: white;'>Delete Users</span><br>"
            "4. <span style='color: white;'>View User Requests</span><br>"
            "5. <span style='color: white;'>View Feedback Tables</span><br>"
            "6. <span style='color: white;'>Logout</span><br>"
            "Enter your choice")


def get_view_user_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        response = "--- User Data ---<br>"
        cursor.execute("SELECT"
                       " UserFeedback.Username,"
                       " UserFeedback.Age,"
                       " UserFeedback.Gender,"
                       " UserFeedback.Mobile_Number,"
                       " UserData.Balance"
                       " FROM"
                       " UserFeedback"
                       " JOIN"
                       " UserData"
                       " ON"
                       " UserFeedback.Username = UserData.Username;")
        user_data = cursor.fetchall()

        response += "Username&emsp;Age&emsp;Gender&emsp;Mobile Number&emsp;Balance<br>"

        for data in user_data:
            username = data["Username"]
            age = data["Age"]
            gender = data["Gender"]
            m_num = data["Mobile_Number"]
            balance = data["Balance"]

            if m_num is None:
                m_num = "N/A"

            response += ("<br>" + "-" * 25 + "<br>")
            response += (
                f"<br><span style='color: white;'>{username}&emsp;{age}&emsp;{gender}&emsp;{m_num}&emsp;{balance}</span>"
            )
        response += "<br><br>Type 'exit' to leave the interface."

        return response


def get_edit_user_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        response = "--- User Data ---<br>"
        cursor.execute("SELECT"
                       " Username,"
                       " Name,"
                       " Age,"
                       " Gender,"
                       " Mobile_Number"
                       " FROM UserFeedback;")
        user_data = cursor.fetchall()

        response += "<br>Username&emsp;Name&emsp;Age&emsp;Gender&emsp;Mobile Number<br>"

        for data in user_data:
            username = data["Username"]
            name = data["Name"]
            age = data["Age"]
            gender = data["Gender"]
            m_num = data["Mobile_Number"]

            if m_num is None:
                m_num = "N/A"

            response += ("<br>" + "-" * 25 + "<br>")
            response += (
                f"<br><span style='color: white;'>{username}&emsp;{name}&emsp;{age}&emsp;{gender}&emsp;{m_num}</span>"
            )
        response += "<br><br>Enter the username of the user you want to edit"

        return response


def get_edit_selected_user_menu():
    return ("Type 'exit' to leave the interface.<br>"
            "<br>1. <span style='color: white;'>Change Username</span>"
            "<br>2. <span style='color: white;'>Change Name</span>"
            "<br>3. <span style='color: white;'>Change Age</span>"
            "<br>4. <span style='color: white;'>Change Gender</span>"
            "<br>5. <span style='color: white;'>Change Mobile Number</span>"
            "<br><br>Enter the Column you want to edit: ")


def get_selected_user():
    return "Enter the new value for the user"


def get_delete_user_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        response = "--- User Data ---<br>"
        cursor.execute("SELECT"
                       " Username"
                       " FROM UserFeedback;")
        user_data = cursor.fetchall()

        response += "<br>Username<br>"

        for data in user_data:
            username = data["Username"]

            response += ("<br>" + "-" * 25 + "<br>")
            response += (
                f"<br><span style='color: white;'>{username}</span>"
            )
        response += "<br><br>Enter the username of the user you want to delete"

        return response


def get_admin_confirm_pin():
    return "Enter your pin to delete"


def get_view_user_request_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM Requests WHERE Action = 'Pending'")
        user_requests = cursor.fetchall()

        if user_requests == ():
            response = "No pending requests."
            connection.close()
            response += "<br>Type 'exit' to go back to Admin Menu..."
            return response
        if user_requests != ():
            response = "User Request(s):<br>"
            response += f"{'Username'}&emsp;{'Updation'}&emsp;{'Action'}<br>"

            for request in user_requests:
                username = request["Username"]
                updation = request["Updation"]
                action = request["Action"]

                response += "<br>" + "-" * 25 + "<br>"
                response += f"<br><span style='color: white;'>{username}&emsp;{updation}&emsp;{action}</span>"

        response += "<br>Enter the username for which you want to manage requests (or 'exit' to go back): "

        return response


def get_select_request_menu():
    connection = create_connection()
    req_user = session['requesting_user']

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM Requests WHERE Action = 'Pending' AND Username = %s", (req_user,))
        user_requests = cursor.fetchall()

        if user_requests == ():
            response = "No pending requests."
            connection.close()
            response += "<br>Type 'exit' to go back to Admin Menu..."
            return response
        if user_requests != ():
            response = "Available Request(s):<br>"
            response += f"{'Username'}&emsp;{'Updation'}&emsp;{'Action'}<br>"

            for request in user_requests:
                username = request["Username"]
                updation = request["Updation"]
                action = request["Action"]

                response += "<br>" + "-" * 25 + "<br>"
                response += f"<span style='color: white;'>{username}&emsp;{updation}&emsp;{action}</span>"

        response += "<br>Enter the field you want to manage (or 'exit' to go back): "

        return response


def get_action_menu():
    return ("--- Action Menu ---"
            "<br><br>1. <span style='color: white;'>Accept</span>"
            "<br>2. <span style='color: white;'>Decline</span>"
            "<br>3. <span style='color: white;'>Exit</span>"
            "<br>Enter your choice: ")


def get_view_feedback_chart_menu():
    return ("--- Feedback Tables ---<br>"
            "<br>Type 'exit' to leave the interface<br><br>"
            "Survey '1': <span style='color: white;'>Enjoying our Services in (y / n)</span><br>"
            "Survey '2': <span style='color: white;'>Ratings of Services Provided (0-5)</span><br>"
            "Survey '3': <span style='color: white;'>Reviews for Improvement</span><br>"
            "View all '4': <span style='color: white;'>Every Review in One Table</span><br>"
            "<br>Your Choice: ")


def get_q1_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT Username, Age, Gender, Q1, Mobile_Number FROM UserFeedback WHERE Mobile_Number IS NOT NULL")
        feedbacks_list = cursor.fetchall()

    response = "--- Their reviews ---<br>"
    response += f'<br>{"Username"}&emsp;{"Age"}&emsp;{"Gender"}&emsp;{"Mobile Number"}&emsp;{"Q1"}<br>'

    for answers in feedbacks_list:
        username = answers["Username"]
        age = answers["Age"]
        gender = answers["Gender"]
        q1 = answers["Q1"]
        m_num = answers["Mobile_Number"]

        if m_num is None:
            m_num = "N/A"

        response += "<br>" + "-" * 25 + "<br>"
        response += f"<span style='color: white;'>{username}&emsp;{age}&emsp;{gender}&emsp;{m_num}&emsp;{q1}</span><br>"

    response += "<br>Type 'exit' to leave the interface"
    return response


def get_q2_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT Username, Age, Gender, Q2, Mobile_Number FROM UserFeedback WHERE Mobile_Number IS NOT NULL")
        feedbacks_list = cursor.fetchall()

    response = "--- Their reviews ---<br>"
    response += f'<br>{"Username"}&emsp;{"Age"}&emsp;{"Gender"}&emsp;{"Mobile Number"}&emsp;{"Q2"}<br>'

    for answers in feedbacks_list:
        username = answers["Username"]
        age = answers["Age"]
        gender = answers["Gender"]
        q2 = answers["Q2"]
        m_num = answers["Mobile_Number"]

        if m_num is None:
            m_num = "N/A"

        response += "<br>" + "-" * 25 + "<br>"
        response += f"<span style='color: white;'>{username}&emsp;{age}&emsp;{gender}&emsp;{m_num}&emsp;{q2}</span><br>"

    response += "<br>Type 'exit' to leave the interface"
    return response


def get_q3_menu():
    connection = create_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT Username, Age, Gender, Q3, Mobile_Number FROM UserFeedback WHERE Mobile_Number IS NOT NULL")
        feedbacks_list = cursor.fetchall()

    response = "--- Their reviews ---<br>"
    response += f'<br>{"Username"}&emsp;{"Age"}&emsp;{"Gender"}&emsp;{"Mobile Number"}&emsp;{"Q3"}<br>'

    for answers in feedbacks_list:
        username = answers["Username"]
        age = answers["Age"]
        gender = answers["Gender"]
        q3 = answers["Q3"]
        m_num = answers["Mobile_Number"]

        if m_num is None:
            m_num = "N/A"

        response += "<br>" + "-" * 25 + "<br>"
        response += f"<span style='color: white;'>{username}&emsp;{age}&emsp;{gender}&emsp;{m_num}&emsp;{q3}</span><br>"

    response += "<br>Type 'exit' to leave the interface"
    return response


def get_feedback_table_menu():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM UserFeedback WHERE Mobile_Number IS NOT NULL")
    all_feedback = cursor.fetchall()

    response = "--- Their reviews ---<br>"

    response += (
        f'{"Username"}&emsp;{"Age"}&emsp;{"Gender"}&emsp;{"Mobile Number"}&emsp;{"Q1"}&emsp;{"Q2"}&emsp;{"Q3"}<br>')

    for user_answers in all_feedback:
        username = user_answers["Username"]
        user_Age = user_answers["Age"]
        user_Gender = user_answers["Gender"]
        q1 = user_answers["Q1"]
        q2 = user_answers["Q2"]
        q3 = user_answers["Q3"]
        user_M_num = user_answers["Mobile_Number"]

        if user_M_num is None:
            user_M_num = "N/A"

        response += ("<br>" + "-" * 25 + '<br>')
        response += (
            f"<span style='color: white;'>{username}&emsp;{user_Age}&emsp;{user_Gender}&emsp;{user_M_num}&emsp;{q1}&emsp;{q2}&emsp;{q3}</span><br>")

    response += "<br>Type 'exit' to go back"

    return response


def get_user_login_signup_menu():
    return ("--- User Interface ---<br>"
            "<br>1. <span style='color: white;'>Login</span>"
            "<br>2. <span style='color: white;'>Signup</span>"
            "<br>Enter your choice")


def get_login_username():
    return "Enter your Username"


def get_signup_username():
    return "Enter your new Username"


def get_login_password():
    return "Enter your Password"


def get_user_name():
    return "Enter your Full name"


def get_user_age():
    return "Enter your Age"


def get_user_gender():
    return "Enter your Gender"


def create_lstm_model(vocab_size):
    embedding = nn.Embedding(vocab_size, 10)
    lstm = nn.LSTM(10, 50, batch_first=True)
    fc = nn.Linear(50, vocab_size)
    return embedding, lstm, fc


def preprocess_passwords(existing_passwords):
    all_chars = ''.join(existing_passwords)
    char_counts = Counter(all_chars)
    vocab = {char: idx + 1 for idx,
                               (char, _) in enumerate(char_counts.items())}
    vocab_size = len(vocab) + 1

    sequences = []
    for pwd in existing_passwords:
        seq = [vocab[char] for char in pwd]
        sequences.append(seq)

    X, y = [], []
    for seq in sequences:
        for i in range(1, len(seq)):
            X.append(torch.tensor(seq[:i], dtype=torch.long))
            y.append(seq[i])

    if X:
        X = pad_sequence(X, batch_first=True, padding_value=0)
    else:
        X = torch.empty(0, 0)
    y = torch.tensor(y, dtype=torch.long)

    return X, y, vocab_size


def suggest_password(userid, name, age, gender):
    word_list_personal = [userid, name, age, gender]
    alphabets = "abcdefghijklmnopqrstuvwxyz"
    special_chars = '@#_:'
    digits = "1234567890"

    def randomize_case(word):
        if not word:
            return ''
        return ''.join(random.choice([char.lower(), char.upper()]) for char in word)

    password_length = random.randint(8, 12)

    lowercase = random.choice(string.ascii_lowercase)
    uppercase = random.choice(string.ascii_uppercase)
    number = random.choice(digits)
    special = random.choice(special_chars)
    character = random.choice(alphabets)

    personal_word = randomize_case(random.choice(word_list_personal))

    remaining_length = password_length - \
                       len(lowercase + uppercase + number +
                           special + personal_word + character)

    all_chars = list(string.ascii_letters + digits +
                     special_chars) + list(word_list_personal)
    password_chars = [lowercase, uppercase,
                      number, special, personal_word, character]

    while remaining_length > 0:
        next_char = random.choice(all_chars)
        if next_char in string.ascii_letters:
            next_char = randomize_case(next_char)
        password_chars.append(next_char)
        remaining_length -= len(next_char)

    random.shuffle(password_chars)

    user_suggested_password = ''.join(password_chars)[:password_length]

    return user_suggested_password


def get_existing_passwords():
    connection = create_connection()
    passwords = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Password FROM UserData")
            passwords = [row['Password'] for row in cursor.fetchall()]
    finally:
        connection.close()
    return passwords


def get_user_password():
    username = session['username']

    existing_passwords = get_existing_passwords()

    X, y, vocab_size = preprocess_passwords(existing_passwords)

    if X.size(0) == 0:
        X = torch.zeros((1, 10), dtype=torch.long)
        y = torch.zeros(1, dtype=torch.long)

    embedding, lstm, fc = create_lstm_model(vocab_size)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(list(embedding.parameters(
    )) + list(lstm.parameters()) + list(fc.parameters()), lr=0.001)

    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    for _ in range(100):
        for inputs, targets in dataloader:
            optimizer.zero_grad()
            embedded_input = embedding(inputs)
            lstm_output, _ = lstm(embedded_input)
            output = fc(lstm_output[:, -1, :])
            loss = criterion(output, targets)
            loss.backward()
            optimizer.step()

    suggested_password = suggest_password(username, name, age, gender)
    session['suggested_password'] = suggested_password

    return ("Password must have 8+ chars, uppercase, lowercase, numbers, & a special char (@, #, _, :)."
            f"<br><br>Suggested Password: <span style='color: white;'>{suggested_password}</span>"
            "<br><br>Set a password (or type <span style='color: white;'>'use'</span> to use the suggested password): "
            )


def get_user_menu():
    return ("--- User Menu ---<br>"
            "<br>1. <span style='color: white;'>Transaction Menu</span><br>"
            "2. <span style='color: white;'>Calculate Fixed Deposit</span><br>"
            "3. <span style='color: white;'>Loan Application Process</span><br>"
            "4. <span style='color: white;'>Currency Exchange</span><br>"
            "5. <span style='color: white;'>Create/Update mPin</span><br>"
            "6. <span style='color: white;'>User Profile</span><br>"
            "7. <span style='color: white;'>Update Information</span><br>"
            "8. <span style='color: white;'>Feedback</span><br>"
            "9. <span style='color: white;'>See Bank Policies</span><br>"
            "10. <span style='color: white;'>Logout</span><br>"
            "Enter your choice")


def get_transaction_menu():
    return ("--- Transaction Menu ---<br>"
            "<br>1. <span style='color: white;'>Deposit</span><br>"
            "2. <span style='color: white;'>Withdraw</span><br>"
            "3. <span style='color: white;'>Send Money</span><br>"
            "4. <span style='color: white;'>Check Balance</span><br>"
            "5. <span style='color: white;'>View Transaction History</span><br>"
            "6. <span style='color: white;'>Exit</span><br>"
            "Choose an option")


def get_deposit_menu():
    return ("--- Deposit Interface ---<br>"
            "<br>Enter <span style='color: white;'>amount to deposit</span>")


def get_withdraw_menu():
    return ("--- Withdraw Interface ---<br>"
            "<br>Enter <span style='color: white;'>amount to withdraw</span>")


def get_mpin_amount():
    return "Enter your mPin"


def get_send_money_menu():
    return ("--- Send Money Interface ---<br>"
            "<br>Enter <span style='color: white;'>recipient's username</span>")


def get_user_mpin():
    return "Enter your 4-digit mPin"


def get_send_money_amount():
    return "Enter the amount to send"


def get_check_balance_menu():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            username = session['username']
            cursor.execute(
                "SELECT Balance FROM UserData WHERE Username = %s", (username,))
            balance = cursor.fetchone()['Balance']

    return (f"Your current balance is <span style='color: white;'>₹{balance:.2f}</span>"
            "<br><br>Type 'exit' to go back.")


def get_view_transaction_history_menu():
    res = "--- Transaction History ---<br>"

    with create_connection() as connection:
        with connection.cursor() as cursor:

            username = session['username']
            cursor.execute(
                "SELECT Username FROM UserData WHERE Username = %s", (username,))
            username = cursor.fetchone()['Username']

            cursor.execute("""
                SELECT * FROM Transactions
                WHERE Sender = %s OR Recipient = %s
            """, (username, username))
            user_transactions = cursor.fetchall()

            if user_transactions:
                res += "<br>Sender&emsp;Recipient&emsp;Amount"
                res += "<br>"
                res += ("<br>" + '-' * 25)
                for transaction in user_transactions:
                    sender = transaction['Sender']
                    recipient = transaction['Recipient']

                    amount = float(transaction['Amount'])
                    res += f"<br><span style='color: white;'>{sender}&emsp;{recipient}&emsp;{amount:<10}</span>"
                res += "<br><br>Type 'exit' to return to the user menu."
                return res

            else:
                return ("No transactions found."
                        "<br><br>Type 'exit' to go back.")


def get_calculate_fd_menu():
    return ("--- Calculating Fixed Deposit ---<br>"
            "<br>Enter the principal amount (in ₹)")


def get_tenure():
    return "Enter the tenure (1, 3, or 5 years)"


def get_currency_exchange_menu():
    return ("--- Currency Exchange ---<br>"
            "<br>1. <span style='color: white;'>INR to USD</span>"
            "<br>2. <span style='color: white;'>INR to GBP</span>"
            "<br>3. <span style='color: white;'>INR to EUR</span>"
            "<br>4. <span style='color: white;'>INR to JPY</span>"
            "<br>5. <span style='color: white;'>INR to CHF</span>"
            "<br>6. <span style='color: white;'>Exit</span>"
            "<br>Enter your choice")


def get_rate_conversion():
    return "Enter the amount in INR"


def get_loan_application_menu():
    return ("--- Loan Application Process ---<br>"
            "<br>Choose a loan type:"
            "<br>1. <span style='color: white;'>Personal Loan</span>"
            "<br>2. <span style='color: white;'>Home Loan</span>"
            "<br>3. <span style='color: white;'>Car Loan</span>"
            "<br>4. <span style='color: white;'>Education Loan</span>"
            "<br>5. <span style='color: white;'>Business Loan</span>"
            "<br>Enter the loan type (1-5)")


def get_create_mpin_menu():
    return ("--- mPin Interface ---<br>"
            "<br>Enter your Password")


def get_create_mpin():
    return "Enter your 4-digit mPin"


def get_updated_mpin():
    return "Enter the new 4-digit mPin"


def get_user_profile():
    username = session['username']
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM UserData WHERE Username = %s",
                   (username,))
    user_data = cursor.fetchone()
    cursor.execute(
        "SELECT * FROM UserFeedback WHERE Username = %s", (username,))
    user_feedback = cursor.fetchone()
    return ("--- User Profile ---"
            f"<br>Username: <span style='color: white;'>{user_data['Username']}</span>"
            "<br><br>--- Personal Info ---"
            f"<br>Name: <span style='color: white;'>{user_feedback['Name']}</span>"
            f"<br>Age: <span style='color: white;'>{user_feedback['Age']}</span>"
            f"<br>Gender: <span style='color: white;'>{user_feedback['Gender']}</span>"
            f"<br>Mobile Number: <span style='color: white;'>{user_feedback['Mobile_Number']}</span>"
            "<br><br>--- Bank Info ---"
            f"<br>Balance: <span style='color: white;'>₹{float(user_data['Balance']):.2f}</span>"
            "<br><br>Enter mpin to view Password or Type 'exit' to return to User Menu")


def get_answer_one():
    return ("--- Feedback Interface ---<br>"
            "<br>Did you enjoy our service? <span style='color: white;'>(y / n)</span>")


def get_answer_two():
    return "Please rate our service <span style='color: white;'>(0-5)</span>"


def get_answer_three():
    return "How can we improve? <span style='color: white;'>(Open End)</span>"


def get_mnum():
    return "If you want to save your feedback<br>Enter your mobile number"


def get_request_change_menu():
    return ("--- Request Change Interface ---<br>"
            "<br>What do you want to Update?"
            "<br>1. <span style='color: white;'>Username</span>"
            "<br>2. <span style='color: white;'>Name</span>"
            "<br>3. <span style='color: white;'>Age</span>"
            "<br>4. <span style='color: white;'>Gender</span>"
            "<br>5. <span style='color: white;'>Mobile Number</span>"
            "<br>6. <span style='color: white;'>Password</span>"
            "<br>7. <span style='color: white;'>Delete Account</span>"
            "<br>8. <span style='color: white;'>View Requests</span>"
            "<br>9. <span style='color: white;'>Exit</span>"
            "<br>Enter here")


def get_new_value():
    return "Please enter a new value (or type 'exit' to cancel)"


def get_view_requests():
    with create_connection() as connection:
        with connection.cursor() as cursor:

            username = session['username']
            cursor.execute(
                "SELECT * FROM Requests WHERE Username = %s", (username,)
            )
            user_requests = cursor.fetchall()

            if user_requests:
                response = "--- Your Request(s) ---<br>"
                response += f"<br>{'Username'}&emsp;{'Updation'}&emsp;{'Action'}<br>"
                response += ("<br>" + "-" * 25 + "<br>")

                for data in user_requests:
                    username = data["Username"]
                    updation = data["Updation"]
                    action = data["Action"]

                    response += f"<br><span style='color: white;'>{username}&emsp;{updation}&emsp;{action}</span>"
                response += "<br><br>Type 'exit' to return to the user menu."

                return response
            else:
                response = "No requests sent"
                return response


def get_bank_policies():
    return """--- Bank Policies ---
    <br><br>1. <span style='color: white;'>Account Opening Policy</span>: Guidelines on the documentation and identification
    "required to open different types of accounts (savings, checking, etc.).

    <br><br>2. <span style='color: white;'>Know Your Customer (KYC) Policy</span>: Procedures to verify the identity of clients
    to prevent fraud and comply with regulations.

    <br><br>3. <span style='color: white;'>Privacy Policy</span>: Guidelines on how customer information is collected, used,
    and protected, including data sharing practices.

    <br><br>4. <span style='color: white;'>Loan Policy</span>: Guidelines regarding loan terms, interest rates, repayment
    schedules, and eligibility criteria.

    <br><br>5. <span style='color: white;'>Deposit Insurance Policy</span>: Information about insurance coverage for deposits,
    typically provided by government entities.

    <br><br>6. <span style='color: white;'>Interest Rate Policy</span>: Framework for determining interest rates on loans and
    deposits based on market conditions and internal criteria.

    <br><br>7. <span style='color: white;'>Transaction Limits Policy</span>: Rules governing limits on withdrawals, deposits,
    and transfers to prevent fraud and manage risk.

    <br><br>8. <span style='color: white;'>Customer Complaint Policy</span>: Procedures for addressing customer complaints,
    including escalation processes and resolution timelines.

    <br><br>9. <span style='color: white;'>Code of Conduct</span>: Standards of behavior expected from employees, including
    ethical practices and compliance with laws.

    <br><br>10. <span style='color: white;'>Digital Banking Policy</span>: Regulations governing online and mobile banking
    services, including security measures and customer authentication.

    <br><br>Type 'exit' to return to the user menu.
    """


def get_user_exit():
    return "Type 'exit' to return to the user menu."


def get_feedback_exit():
    return "Type 'exit' to return to the feedbacks menu"


def get_profile_exit():
    return "Type 'exit' to return to your profile"


if __name__ == '__main__':
    create_tables()
    load_data()
    app.run(debug=True)