from flask import Flask, request, jsonify, render_template
import mysql.connector

app = Flask(__name__)

# Establish MySQL connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password',  # Enter your MySQL password here
        database='blood_bank'
    )
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/donors', methods=['GET'])
def get_donors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Donors')
    donors = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(donors)

@app.route('/donors', methods=['POST'])
def add_donor():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO Donors (first_name, last_name, dob, blood_type, contact_number, email, address, last_donated)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', 
                   (data['first_name'], data['last_name'], data['dob'], data['blood_type'], 
                    data['contact_number'], data['email'], data['address'], data['last_donated']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Donor added successfully"}), 201

@app.route('/inventory', methods=['GET'])
def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM BloodInventory')
    inventory = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(inventory)

if __name__ == '__main__':
    app.run(debug=True)
