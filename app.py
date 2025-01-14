from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
import cv2
import numpy as np
import tensorflow as tf
from werkzeug.security import generate_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename

# hashed_password = generate_password_hash('password123')


app = Flask(__name__)  # Correct variable __name__

app.secret_key = 'd92ac30b4b5f442ab3856493d3b8c2b7'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Update with your MySQL username
app.config['MYSQL_PASSWORD'] = '2414'  # Update with your MySQL password
app.config['MYSQL_DB'] = 'Tumor'

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Connect to MySQL and check if the user exists
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM User WHERE username = %s", [username])
        user = cursor.fetchone()
        
        print(f"User fetched: {user}")  # Debugging output
        
        if user:
            print(f"Stored password hash: {user[3]}")  # Print the stored hashed password
            if check_password_hash(user[3], password):  # user[2] is the hashed password
                session['logged_in'] = True
                session['username'] = username
                session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return redirect('home')
            else:
                flash('Invalid username or password', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if the username already exists
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM User WHERE username = %s", [username])
        user = cursor.fetchone()
        
        if user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)
        
        # Insert the new user into the database
        cursor.execute("INSERT INTO User (username,email, password) VALUES (%s,%s, %s)", (username,email, hashed_password))
        mysql.connection.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/home')
def home():
    if 'logged_in' not in session:
        return redirect('/login')  # Redirect to login if not logged in

    # Query to get all rows from the 'scan' table
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM tumor")
    scan_data = cursor.fetchall()  # Fetch all rows

    # Query to get the count of rows in the 'scan' table
    cursor.execute("SELECT COUNT(*) FROM tumor")
    row_count = cursor.fetchone()[0]  # Get the count
    cursor.execute("SELECT COUNT(*) FROM tumor WHERE prediction = 'Non-tumorous Brain'")
    non_tumorous_count = cursor.fetchone()[0]

    # Query to get the count of 'Tumorous Brain' predictions
    cursor.execute("SELECT COUNT(*) FROM tumor WHERE prediction = 'Tumorous Brain'")
    tumorous_count = cursor.fetchone()[0]
    # Pass both the data and count to the template
    return render_template('home.html',count=row_count,data=scan_data,tumor=tumorous_count,no_tumor=non_tumorous_count)

model = tf.keras.models.load_model('tumor_detection_model.h5')

def predict_tumor(image_path):
    image_size = 128
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        return "Error: Unable to load image"

    img = cv2.resize(img, (image_size, image_size))
    img = img / 255.0
    img = np.expand_dims(img, axis=-1)
    img = np.expand_dims(img, axis=0)
    
    prediction = model.predict(img)
    predicted_class = np.argmax(prediction, axis=1)
    
    return "Tumorous Brain" if predicted_class == 0 else "Non-tumorous Brain"

@app.route('/predict', methods=['GET', 'POST'])
def tumor_prediction():
    prediction = None  # Initialize prediction variable

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            image_path = os.path.join('static/uploads', file.filename)
            file.save(image_path)
            prediction = predict_tumor(image_path)
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO tumor (filename, file_path, prediction) VALUES (%s, %s, %s)", 
                           (file.filename, image_path, prediction))
            mysql.connection.commit()
            cursor.close()
            return render_template('tumor.html', prediction=prediction)
    return render_template('tumor.html', prediction=prediction)

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('login_time', None)  # Optional: Clear the login time from the session
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
