from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import pandas as pd
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Load best model + label encoder
model = joblib.load("best_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")   # make sure you saved it earlier

# ✅ MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",           # your MySQL username
        password="Sudheer@123",  # your MySQL password
        database="spare_tooling"
    )

# ------------------- Routes -------------------

# Home Page
@app.route("/")
def home():
    return render_template("home.html")

# About Page
@app.route("/about")
def about():
    return render_template("about.html")

# Signup Page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("login"))
    return render_template("signup.html")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["user"] = user["email"]
            return redirect(url_for("input_page"))
        else:
            return "❌ Invalid credentials"
    return render_template("login.html")

# Forget Password Page
@app.route("/forget-password", methods=["GET", "POST"])
def forget_password():
    if request.method == "POST":
        return "🔑 Password reset link sent to email!"
    return render_template("forget_password.html")

# Input Page
@app.route("/input", methods=["GET", "POST"])
def input_page():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        customer_id = request.form["customer_id"]
        service_history = request.form["service_history"]
        common_problem = request.form["common_problem"]
        company = request.form["company"]

        # Wrap into DataFrame
        input_data = pd.DataFrame([{
            "CUSTOMER ID": customer_id,
            "SERVICE HISTORY": service_history,
            "COMMON PROBLEM": common_problem,
            "VEHICAL COMPANY": company
        }])

        # Predict numeric label
        pred = model.predict(input_data)[0]

        # Decode number → actual solution string
        solution = label_encoder.inverse_transform([pred])[0]

        # Save to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (customer_id, service_history, common_problem, company, predicted_solution, user_email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (customer_id, service_history, common_problem, company, solution, session["user"]))
        conn.commit()
        cursor.close()
        conn.close()

        return render_template("result.html", prediction=solution)

    return render_template("input.html")

# Result Page
@app.route("/result")
def result():
    return render_template("result.html")

@app.route("/booking", methods=["GET"])
def booking_page():
    return render_template("booking.html")


@app.route("/book_slot", methods=["POST"])
def book_slot():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    appointment_date = request.form["appointment_date"]
    time_slot = request.form.get("time_slot")
    vehicle_type = request.form.getlist("vehicle_type")
    instructions = request.form["instructions"]

    vehicle_type_str = ", ".join(vehicle_type)

    # ✅ Use mysql.connector (your defined method)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO bookings 
           (first_name, last_name, appointment_date, time_slot, vehicle_type, instructions) 
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (first_name, last_name, appointment_date, time_slot, vehicle_type_str, instructions),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
        "booking_success.html",
        name=first_name,
        date=appointment_date,
        time=time_slot
    )




# Tool Description Page
@app.route("/tool-description")
def tool_description():
    solutions = [
        {"name": "Brake Pad Replacement",
         "description": "Inspect pads/rotors; replace if worn.",
         "image": "Breakpad.jfif",
         "link": "https://www.amazon.in/s?k=brake+pad+for+car"},
        
        {"name": "Radiator Replacement",
         "description": "Check coolant level; flush radiator; replace thermostat.",
         "image": "Radiator.jfif",
         "link": "https://www.amazon.in/s?k=car+radiator"},
        
        {"name": "Body Repair and Repaint",
         "description": "Fix dents, repaint body panels to restore car look.",
         "image": "carspray.jpg",
         "link": "https://www.amazon.in/s?k=car+body+repair+kit"},
        
        {"name": "Oil Seal Replacement",
         "description": "Replace leaking seals to prevent engine oil loss.",
         "image": "oilseal.jpg",
         "link": "https://www.amazon.in/s?k=oil+seal+car"},
        
        {"name": "Wheel Alignment",
         "description": "Align wheels for smooth driving and longer tire life.",
         "image": "Wheelalign.jfif",
         "link": "https://www.amazon.in/s?k=wheel+alignment+tool"},
        
        {"name": "Diagnostic Scan and Repairs",
         "description": "Scan ECU for faults and repair issues.",
         "image": "DiagnosticScan.jfif",
         "link": "https://www.amazon.in/s?k=car+diagnostic+scanner"},
        
        {"name": "Brake Fluid Replacement",
         "description": "Replace brake fluid for safety and performance.",
         "image": "breakfluid.jfif",
         "link": "https://www.amazon.in/s?k=brake+fluid"},
        
        {"name": "Exhaust System Repair",
         "description": "Repair or replace exhaust pipes and mufflers.",
         "image": "https://m.media-amazon.com/images/I/71zsmcJpGgL._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=car+exhaust"},
        
        {"name": "Transmission Fluid Change",
         "description": "Change transmission oil for smooth gear shifts.",
         "image": "https://m.media-amazon.com/images/I/81AjNtnY4UL._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=transmission+fluid"},
        
        {"name": "Spark Plug Replacement",
         "description": "Replace spark plugs to improve ignition.",
         "image": "sparkplug.jfif",
         "link": "https://www.amazon.in/s?k=spark+plug"},
        
        {"name": "Suspension Adjustment",
         "description": "Adjust suspension for better ride comfort.",
         "image": "https://m.media-amazon.com/images/I/81xP4dQkY5L._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=car+suspension+kit"},
        
        {"name": "Tire Rotation and Balancing",
         "description": "Rotate and balance tires to extend their life.",
         "image": "https://m.media-amazon.com/images/I/71Xl2Zg4Z2L._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=tire+balancing"},
        
        {"name": "Battery Replacement",
         "description": "Replace car battery for reliable performance.",
         "image": "baterry.jfif",
         "link": "https://www.amazon.in/s?k=car+battery"},
        
        {"name": "Fuel System Cleaning",
         "description": "Clean injectors, filters and fuel lines.",
         "image": "https://m.media-amazon.com/images/I/71b8pHvzGfL._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=fuel+system+cleaner"},
        
        {"name": "Clutch Repair",
         "description": "Repair or replace clutch plates for smooth drive.",
         "image": "https://m.media-amazon.com/images/I/71ovpka2n+L._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=clutch+kit+car"},
        
        {"name": "AC Repair",
         "description": "Fix leaks, replace compressor or gas recharge.",
         "image": "accahnge.jfif",
         "link": "https://www.amazon.in/s?k=car+ac+repair+kit"},
        
        {"name": "Timing Belt Replacement",
         "description": "Replace timing belt to prevent engine failure.",
         "image": "https://m.media-amazon.com/images/I/81td5cXv3lL._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=timing+belt+car"},
        
        {"name": "Wiper Replacement",
         "description": "Replace wipers for clear visibility during rain.",
         "image": "https://m.media-amazon.com/images/I/81rjRuFh0-L._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=wiper+blades"},
        
        {"name": "Power Steering Service",
         "description": "Check and refill power steering fluid.",
         "image": "powerstaring.jfif",
         "link": "https://www.amazon.in/s?k=power+steering+fluid"},
        
        {"name": "Engine Filter Replacement",
         "description": "Replace engine air filter for clean airflow.",
         "image": "https://m.media-amazon.com/images/I/81MZ0g1QaHL._AC_SL1500_.jpg",
         "link": "https://www.amazon.in/s?k=engine+air+filter+car"}
    ]
    
    return render_template("tool_description.html", solutions=solutions)


# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(port=8007, debug=True)
