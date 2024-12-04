from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')

# MySQL Database configuration
db_config = {
    'host': os.environ.get('DB_HOST', '172.17.0.2'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '02136'),
    'database': os.environ.get('DB_NAME', 'users')
}

# Database Connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Automatically create required tables
def initialize_database():
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(create_users_table)
        conn.commit()
        print("Table 'users' is ensured to exist.")
    except Error as e:
        print(f"Error creating table: {e}")
    finally:
        cursor.close()
        conn.close()

# Flask Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate username
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash("Username already exists. Please choose another.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
        except Exception as e:
            flash("An error occurred during registration. Please try again.", "danger")
            print(e)  # Log the error for debugging
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed. Please check your username and password.", "danger")
    
    return render_template('login.html')

@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return f"Welcome, {session['username']}!"

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Initialize the database on app start
if __name__ == '__main__':
    initialize_database()  # Ensure tables are created
    app.run(debug=False, port=5002)