from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, send_file, make_response
import firebase_admin
from firebase_admin import credentials, auth, db, storage
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import csv
import secrets
from datetime import datetime, timedelta
from functools import wraps
import requests
import re
import logging
import json
import uuid
from io import StringIO, BytesIO
from werkzeug.utils import secure_filename
import io
import random
import string
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch 
# Make sure this is also imported
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "CS-B")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")  # Add this to your .env file
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER", "your_email@gmail.com")  # Change this
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")  # Change this
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "admin@gmail.com") 

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Initialize Firebase Admin SDK
# Replace the credentials initialization with:
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "token_uri": "https://oauth2.googleapis.com/token",
})
firebase_admin.initialize_app(cred, {
    'databaseURL': 'your-database-url',  # Your Realtime Database URL
    'storageBucket': 'your-bucket-name'  # Replace with your Firebase Storage bucket name
})
ref = db.reference('/')
# Add this to app.py after Firebase initialization
def get_today_date():
    return datetime.now().strftime('%Y-%m-%d')


def initialize_menu_items():
    menu_items_ref = db.reference('menu_items')
    existing_items = menu_items_ref.get()
    
    # Define menu_items_data outside the conditional block
    menu_items_data = {
        "appam": {
            "name": "Appam",
            "category": "Breakfast",
            "price": 8,
            "image_url": "/static/img/appam.png",
            "description": "Traditional South Indian pancake made from fermented rice batter",
            "in_stock": False,
            "stock_count": 50,
            "special": False,
            "discount": 0
        },
        "masala-dosa": {
            "name": "Masala Dosa",
            "category": "Breakfast",
            "price": 80,
            "image_url": "/static/img/dosa.webp",
            "description": "Crispy rice crepe filled with spiced potato filling",
            "in_stock": False,
            "stock_count": 45,
            "special": False,
            "discount": 0
        },
        "idli-sambar": {
            "name": "Idli Sambar (4 pcs)",
            "category": "Breakfast",
            "price": 30,
            "image_url": "/static/img/idli.webp",
            "description": "Steamed rice cakes served with spiced lentil soup",
            "in_stock": False,
            "stock_count": 60,
            "special": False,
            "discount": 0
        },
        "poori-masala": {
            "name": "Poori Masala",
            "category": "Breakfast",
            "price": 30,
            "image_url": "/static/img/poori.jpg",
            "description": "Deep-fried puffy bread served with potato curry",
            "in_stock": False,
            "stock_count": 40,
            "special": False,
            "discount": 0
        },
        "chapati": {
            "name": "Chapati",
            "category": "Breakfast",
            "price": 10,
            "image_url": "/static/img/chapati.jpg",
            "description": "Whole wheat flatbread",
            "in_stock": False,
            "stock_count": 80,
            "special": False,
            "discount": 0
        },
        "puttu": {
            "name": "Puttu",
            "category": "Breakfast",
            "price": 15,
            "image_url": "/static/img/puttu.jpg",
            "description": "Steamed cylinders of ground rice layered with coconut",
            "in_stock": False,
            "stock_count": 35,
            "special": False,
            "discount": 0
        },
        "upma": {
            "name": "Upma",
            "category": "Breakfast",
            "price": 20,
            "image_url": "/static/img/upma.jpg",
            "description": "Savory semolina porridge with vegetables and spices",
            "in_stock": False,
            "stock_count": 40,
            "special": False,
            "discount": 0
        },
        "veg-thali": {
            "name": "Veg Thali",
            "category": "Lunch",
            "price": 50,
            "image_url": "/static/img/vegmeals.webp",
            "description": "Complete vegetarian meal with rice, curries, and sides",
            "in_stock": False,
            "stock_count": 30,
            "special": False,
            "discount": 0
        },
        "chicken-biryani": {
            "name": "Chicken Biryani",
            "category": "Lunch",
            "price": 110,
            "image_url": "/static/img/chickenbiryani.jpg",
            "description": "Fragrant rice dish with spiced chicken and aromatics",
            "in_stock": False,
            "stock_count": 25,
            "special": False,
            "discount": 5
        },
        "fish-curry-meals": {
            "name": "Fish Curry Meals",
            "category": "Lunch",
            "price": 70,
            "image_url": "/static/img/fishthali.jpg",
            "description": "Rice meal served with fish curry and accompaniments",
            "in_stock": False,
            "stock_count": 20,
            "special": False,
            "discount": 0
        },
        "veg-pulao": {
            "name": "Veg Pulao",
            "category": "Lunch",
            "price": 60,
            "image_url": "/static/img/vegpulao.jpg",
            "description": "Mildly spiced rice with mixed vegetables",
            "in_stock": False,
            "stock_count": 35,
            "special": False,
            "discount": 0
        },
        "poratta": {
            "name": "Poratta",
            "category": "Lunch",
            "price": 10,
            "image_url": "/static/img/poratta.jpeg",
            "description": "Flaky layered flatbread",
            "in_stock": False,
            "stock_count": 90,
            "special": False,
            "discount": 0
        },
        "masala-chai": {
            "name": "Masala Chai",
            "category": "Drinks",
            "price": 30,
            "image_url": "/static/img/masalachai.jpg",
            "description": "Spiced tea with milk",
            "in_stock": False,
            "stock_count": 100,
            "special": False,
            "discount": 0
        },
        "gulab-jamun": {
            "name": "Gulab Jamun (2 pcs)",
            "category": "Desserts",
            "price": 50,
            "image_url": "/static/img/gulabjamun.webp",
            "description": "Sweet milk solids balls soaked in sugar syrup",
            "in_stock": False,
            "stock_count": 30,
            "special": False,
            "discount": 0
        },
        "mango-lassi": {
            "name": "Mango Lassi",
            "category": "Drinks",
            "price": 40,
            "image_url": "/static/img/mangolassi.webp",
            "description": "Yogurt-based smoothie with mango",
            "in_stock": False,
            "stock_count": 40,
            "special": False,
            "discount": 0
        },
        "vanilla-icecream": {
            "name": "Vanilla Ice Cream",
            "category": "Desserts",
            "price": 80,
            "image_url": "/static/img/vanilla.jpg",
            "description": "Classic vanilla ice cream scoop",
            "in_stock": False,
            "stock_count": 25,
            "special": False,
            "discount": 0
        },
        "chocolate-icecream": {
            "name": "Chocolate Ice Cream",
            "category": "Desserts",
            "price": 80,
            "image_url": "/static/img/chocolate.webp",
            "description": "Rich chocolate ice cream scoop",
            "in_stock": False,
            "stock_count": 25,
            "special": False,
            "discount": 0
        },
        "butterscotch-icecream": {
            "name": "Butterscotch Ice Cream",
            "category": "Desserts",
            "price": 80,
            "image_url": "/static/img/butterscotch.jpg",
            "description": "Sweet butterscotch flavored ice cream",
            "in_stock": False,
            "stock_count": 25,
            "special": False,
            "discount": 0
        },
        "strawberry-icecream": {
            "name": "Strawberry Ice Cream",
            "category": "Desserts",
            "price": 80,
            "image_url": "/static/img/strawberry.jpg",
            "description": "Sweet strawberry flavored ice cream",
            "in_stock": False,
            "stock_count": 25,
            "special": False,
            "discount": 0
        },
        "pepsi": {
            "name": "Pepsi",
            "category": "Drinks",
            "price": 40,
            "image_url": "/static/img/pepsi.jpg",
            "description": "Refreshing carbonated soft drink",
            "in_stock": False,
            "stock_count": 50,
            "special": False,
            "discount": 0
        },
        "7up": {
            "name": "7up",
            "category": "Drinks",
            "price": 40,
            "image_url": "/static/img/7up.jpg",
            "description": "Lemon-lime flavored soft drink",
            "in_stock": False,
            "stock_count": 50,
            "special": False,
            "discount": 0
        },
        "coca-cola": {
            "name": "Coca-Cola",
            "category": "Drinks",
            "price": 40,
            "image_url": "/static/img/cocacola.webp",
            "description": "Classic cola flavored beverage",
            "in_stock": False,
            "stock_count": 50,
            "special": False,
            "discount": 0
        },
        "frooti": {
            "name": "Frooti",
            "category": "Drinks",
            "price": 40,
            "image_url": "/static/img/frooti.webp",
            "description": "Mango flavored fruit drink",
            "in_stock": False,
            "stock_count": 50,
            "special": False,
            "discount": 0
        },
        "veg-curry": {
            "name": "Veg Curry",
            "category": "Curry",
            "price": 50,
            "image_url": "/static/img/vegcurry.jpg",
            "description": "Mixed vegetable curry with traditional spices",
            "in_stock": False,
            "stock_count": 40,
            "special": False,
            "discount": 0
        },
        "chicken-curry": {
            "name": "Chicken Curry",
            "category": "Curry",
            "price": 120,
            "image_url": "/static/img/chickencurry.jpg",
            "description": "Spicy chicken curry with rich gravy",
            "in_stock": False,
            "stock_count": 30,
            "special": False,
            "discount": 0
        },
        "fish-curry": {
            "name": "Fish Curry",
            "category": "Curry",
            "price": 110,
            "image_url": "/static/img/fishcurry.jpg",
            "description": "Traditional Kerala style fish curry",
            "in_stock": False,
            "stock_count": 30,
            "special": False,
            "discount": 0
        },
        "kadala-curry": {
            "name": "Kadala Curry",
            "category": "Curry",
            "price": 40,
            "image_url": "/static/img/kadalacurry.jpg",
            "description": "Black chickpea curry with coconut gravy",
            "in_stock": False,
            "stock_count": 40,
            "special": False,
            "discount": 0
        },
        "egg-curry": {
            "name": "Egg Curry",
            "category": "Curry",
            "price": 40,
            "image_url": "/static/img/eggcurry.jpg",
            "description": "Boiled eggs simmered in spicy curry",
            "in_stock": False,
            "stock_count": 40,
            "special": False,
            "discount": 0
        }
    }
    
    if not existing_items:
        # Get reference to menu_items node in Firebase
        menu_items_ref.set(menu_items_data)
        print("Initialized default menu items")
    else:
        print("Menu items already exist, skipping initialization")

initialize_menu_items()    

@app.after_request
def add_no_cache_headers(response):
    # Prevent caching of authenticated pages
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response 
@app.route('/check_auth')
def check_auth():
    if 'user_id' in session and session.get('is_admin'):
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})
# Create admin user during initialization if it doesn't exist
def ensure_admin_exists():
    try:
        # Check if admin user exists
        admin_user = auth.get_user_by_email(ADMIN_EMAIL)
        print(f"Admin user exists: {admin_user.uid}")
        
        # Ensure admin role is set in database
        admin_ref = db.reference('admins').child(admin_user.uid)
        if not admin_ref.get():
            admin_ref.set({'email': ADMIN_EMAIL, 'role': 'admin'})
            print("Admin role updated in database")
            
    except auth.UserNotFoundError:
        # Create admin user if not exists
        admin_password = os.getenv("ADMIN_PASSWORD", "strong-admin-password")
        admin_user = auth.create_user(
            email=ADMIN_EMAIL,
            password=admin_password,
            display_name="Administrator"
        )
        
        # Save admin data in Realtime Database
        admin_data = {
            'name': "Administrator",
            'email': ADMIN_EMAIL,
            'uid': admin_user.uid
        }
        
        # Save in users collection
        user_ref = db.reference('users')
        user_ref.child(admin_user.uid).set(admin_data)
        
        # Save in admins collection
        admin_ref = db.reference('admins')
        admin_ref.child(admin_user.uid).set({
            'email': ADMIN_EMAIL,
            'role': 'admin'
        })
        
        print(f"Admin user created: {admin_user.uid}")
    except Exception as e:
        print(f"Error ensuring admin exists: {str(e)}")

# Call function to ensure admin exists during startup
ensure_admin_exists()

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if 'user_id' not in session:
            # Set cache control headers to prevent back button issues
            response = make_response(redirect(url_for('signin')))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            flash('Please sign in to access this page.', 'error')
            return response
            
        # Check if user is an admin
        admin_ref = db.reference(f'admins/{session["user_id"]}')
        admin_data = admin_ref.get()
        
        if not admin_data or admin_data.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
            
        return f(*args, **kwargs)
    return decorated_function
# Function to send email
def send_reset_email(to_email, reset_link):
    sender_email = os.getenv("EMAIL_USER", "your-email@gmail.com")  # Change this to your email
    sender_password = os.getenv("EMAIL_PASSWORD", "your-email-password")  # Use App Password if 2FA is enabled
    subject = "Password Reset Request"
    
    # HTML body for better formatting
    html_body = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
            <h2 style="color: #007BFF;">Password Reset Request</h2>
            <p>You requested to reset your password. Click the button below to reset it:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #007BFF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
            </div>
            <p>If you didn't request this password reset, you can ignore this email.</p>
            <p>This link will expire in 1 hour for security reasons.</p>
            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">This is an automated email. Please do not reply.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text as fallback
    text_body = f"Click the link below to reset your password:\n\n{reset_link}\n\nIf you didn't request this, you can ignore this email."
    
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Attach both plain text and HTML versions
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Home Route (Index Page)
@app.route('/')
def index():
    return render_template('index.html')

# Sign Up Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']

        try:
            # Create user in Firebase Authentication
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            print(f"User created in Firebase Authentication: {user.uid}")

            # Save user data in Realtime Database
            user_data = {
                'name': name,
                'email': email,
                'uid': user.uid
            }
            ref = db.reference('users')
            ref.child(user.uid).set(user_data)
            print(f"User data saved in Realtime Database: {user_data}")

            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('signin'))
        except Exception as e:
            print(f"Error: {str(e)}")
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

# Sign In Route - FIXED with proper authentication
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
    
        try:
            # Use Firebase Auth REST API to verify credentials
            auth_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
            
            if not FIREBASE_API_KEY:
                flash('Server configuration error: Missing API key', 'error')
                return redirect(url_for('signin'))
                
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(f"{auth_url}?key={FIREBASE_API_KEY}", json=payload)
            data = response.json()
            
            if 'error' in data:
                error_message = data['error'].get('message', 'Authentication failed')
                
                # Translate Firebase error messages to user-friendly messages
                if error_message == 'EMAIL_NOT_FOUND':
                    flash('No account found with that email address.', 'error')
                elif error_message == 'INVALID_PASSWORD':
                    flash('Incorrect password. Please try again.', 'error')
                elif error_message == 'USER_DISABLED':
                    flash('This account has been disabled.', 'error')
                else:
                    flash(f'Sign in error: {error_message}', 'error')
                    
                return redirect(url_for('signin'))
            
            # If we get here, authentication was successful
            # Get the user from Firebase Admin SDK for additional information
            user = auth.get_user_by_email(email)
            
            # Store user ID in session
            session['user_id'] = user.uid
            
            # Check if user is an admin
            admin_ref = db.reference(f'admins/{user.uid}')
            admin_data = admin_ref.get()
            
            if admin_data and admin_data.get('role') == 'admin':
                session['is_admin'] = True
                flash('Admin sign in successful!', 'success')
                return redirect(url_for('menu_management'))
            else:
                session['is_admin'] = False
                flash('Sign in successful!', 'success')
                return redirect(url_for('home'))
                
        except requests.RequestException as e:
            print(f"Network error: {str(e)}")
            flash('Network error. Please check your connection and try again.', 'error')
            return redirect(url_for('signin'))
        except Exception as e:
            print(f"Error: {str(e)}")
            flash(f'Error during sign in: {str(e)}', 'error')
            return redirect(url_for('signin'))

    return render_template('signin.html')

# Home/Dashboard Route
@app.route('/home')
def home():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # Fetch user data from Realtime Database
    user_id = session['user_id']
    ref = db.reference(f'users/{user_id}')
    user_data = ref.get()

    if not user_data:
        flash('User data not found.', 'error')
        return redirect(url_for('signin'))

    return render_template('home.html', user=user_data)

@app.route('/admin')
@admin_required
def  admin_dashboard():
    # Fetch all users from the database
    if 'user_id' not in session:
        return redirect(url_for('index'))
        

    users_ref = db.reference('users')
    users = users_ref.get()
    
    return redirect(url_for('menu_management'))

# Logout Route
@app.route('/logout')
def logout():
    # Clear the session
    session.pop('user_id', None)
    session.pop('is_admin', None)
    session.pop('_flashes', None)
    flash('You have been logged out.', 'success')
    session.clear()
    return redirect(url_for('index'))

def single_flash(message, category):
    # Clear existing flashes
    session.pop('_flashes', None)
    # Set the new flash message
    flash(message, category)

# Forgot Password Route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        try:
            # Check if the email exists in Firebase Authentication
            try:
                user = auth.get_user_by_email(email)
                uid = user.uid  # Get the user ID
            except auth.UserNotFoundError:
                flash('No account found with that email address.', 'error')
                return redirect(url_for('forgot_password'))
            
            # Generate a token
            token = secrets.token_urlsafe(32)
            
            # Store the reset token in the Realtime Database
            ref = db.reference('password_reset_tokens')
            expiry_time = datetime.now() + timedelta(hours=1)
            
            reset_data = {
                'token': token,
                'email': email,
                'uid': uid,
                'expiry': expiry_time.timestamp(),
                'used': False
            }
            
            # Use sanitized email as the key
            safe_email = email.replace('.', '_')
            ref.child(safe_email).set(reset_data)
            
            # Generate reset link using url_for instead of base_url
            # We need to use _external=True to get a full URL
            reset_link = url_for('reset_password', uid=uid, token=token, _external=True)
            
            print(f"Generated Reset Link: {reset_link}")
            
            # Send email with reset link
            email_sent = send_reset_email(email, reset_link)
            
            if email_sent:
                flash('Password reset email sent! Check your inbox.', 'success')
            else:
                flash('Error sending email. Please try again later.', 'error')
                
            return redirect(url_for('signin'))
        except Exception as e:
            print(f"Error in forgot_password: {str(e)}")
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('forgot_password'))

    return render_template('forgot-password.html')

# Reset Password Route
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    uid = request.args.get('uid')
    token = request.args.get('token')
    
    if not uid or not token:
        flash('Invalid password reset link.', 'error')
        return redirect(url_for('signin'))
    
    try:
        # Get user email from uid
        user = auth.get_user(uid)
        email = user.email
        safe_email = email.replace('.', '_')
        
        # Verify token from database using safe_email
        ref = db.reference(f'password_reset_tokens/{safe_email}')
        reset_data = ref.get()
        
        if not reset_data or reset_data.get('token') != token or reset_data.get('used'):
            flash('Invalid or expired reset token.', 'error')
            return redirect(url_for('signin'))
        
        # Check if token is expired
        expiry_time = datetime.fromtimestamp(reset_data.get('expiry', 0))
        if datetime.now() > expiry_time:
            flash('Reset link has expired. Please request a new one.', 'error')
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if new_password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('reset-password.html', uid=uid, token=token, email=email)
            
            try:
                # Update the password in Firebase Authentication
                auth.update_user(
                    uid,
                    password=new_password
                )
                
                # Mark token as used
                ref.update({'used': True})
                
                flash('Password updated successfully! Please sign in with your new password.', 'success')
                return redirect(url_for('signin'))
            except Exception as e:
                flash(f'Error updating password: {str(e)}', 'error')
                return render_template('reset-password.html', uid=uid, token=token, email=email)
        
        return render_template('reset-password.html', uid=uid, token=token, email=email)
    
    except Exception as e:
        print(f"Error in reset_password: {str(e)}")
        flash('Error validating reset request.', 'error')
        return redirect(url_for('signin'))

# Routes for menu management
@app.route('/menu-management')
@admin_required  # This is your existing decorator to check admin access
def menu_management():
    # Fetch menu items from Firebase
    menu_items_ref = db.reference('menu_items')
    menu_items = menu_items_ref.get() or {}
    
    # Get unique categories
    categories = set()
    for item in menu_items.values():
        if 'category' in item:
            categories.add(item['category'])
    
    # Get user data for avatar
    user_id = session.get('user_id')
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    return render_template('menu_management.html', menu_items=menu_items, categories=list(categories), user_data=user_data)


@app.route('/api/menu-items/<item_id>', methods=['DELETE'])
@admin_required
def delete_menu_item(item_id):
    # Delete from Firebase
    menu_items_ref = db.reference(f'menu_items/{item_id}')
    menu_items_ref.delete()
    
    return jsonify({'success': True})

@app.route('/api/upload-image', methods=['POST'])
@admin_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file:
        # Create a secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(temp_path)
        
        try:
            # Upload to Firebase Storage
            bucket = storage.bucket()
            blob = bucket.blob(f"menu_images/{unique_filename}")
            blob.upload_from_filename(temp_path)
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Get the public URL
            image_url = blob.public_url
            
            # Remove the temporary file
            os.remove(temp_path)
            
            return jsonify({'image_url': image_url})
        
        except Exception as e:
            # Clean up the temporary file in case of error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': str(e)}), 500

# Add these new routes to your Flask app

@app.route('/api/published-menus/<date_str>', methods=['GET'])
def get_published_menu(date_str):
    # Get the published menu for a specific date
    published_menus_ref = db.reference(f'published_menus/{date_str}')
    published_menu = published_menus_ref.get()
    
    if published_menu:
        return jsonify(published_menu)
    else:
        return jsonify({'error': 'No published menu found for this date'}), 404

@app.route('/api/default-menu-items', methods=['GET'])
@admin_required
def get_default_menu_items():
    # Get the default menu items (not date-specific)
    menu_items_ref = db.reference('menu_items')
    menu_items = menu_items_ref.get() or {}
    
    # Create a copy of the menu items to avoid modifying the original
    default_items = {}
    for item_id, item in menu_items.items():
        default_items[item_id] = item.copy()
        # Reset in_stock and special flags for default items
        default_items[item_id]['in_stock'] = False
        default_items[item_id]['special'] = False
    
    return jsonify(default_items)

# Update the publish_menu route to accept items in the request
@app.route('/api/menu-items', methods=['POST'])
@admin_required
def add_menu_item():
    data = request.json
    item_id = data.get('id')
    
    # Generate a unique ID if not provided
    if not item_id:
        item_id = str(uuid.uuid4())
    
    # Ensure stock status consistency
    stock_count = int(data.get('stock_count', 0))
    in_stock = data.get('in_stock', False)
    
    # If stock_count is 0 or negative, ensure in_stock is False
    if stock_count <= 0:
        in_stock = False
    
    # If in_stock is False, ensure stock_count is 0
    if not in_stock:
        stock_count = 0
    
    # Prepare the menu item data
    menu_item = {
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'price': float(data.get('price', 0)),
        'category': data.get('category', ''),
        'image_url': data.get('image_url', ''),
        'in_stock': in_stock,
        'stock_count': stock_count,
        'special': data.get('special', False),
        'discount': int(data.get('discount', 0))
    }
    
    # Save to Firebase
    menu_items_ref = db.reference('menu_items')
    menu_items_ref.child(item_id).set(menu_item)
    
    return jsonify(menu_item), 201

@app.route('/api/menu-items/<item_id>', methods=['PUT'])
@admin_required
def update_menu_item(item_id):
    data = request.json
    
    # Ensure stock status consistency
    stock_count = int(data.get('stock_count', 0))
    in_stock = data.get('in_stock', False)
    
    # If stock_count is 0 or negative, ensure in_stock is False
    if stock_count <= 0:
        in_stock = False
    
    # If in_stock is False, ensure stock_count is 0
    if not in_stock:
        stock_count = 0
    
    # Prepare the menu item data
    menu_item = {
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'price': float(data.get('price', 0)),
        'category': data.get('category', ''),
        'image_url': data.get('image_url', ''),
        'in_stock': in_stock,
        'stock_count': stock_count,
        'special': data.get('special', False),
        'discount': int(data.get('discount', 0))
    }
    
    # Update in Firebase
    menu_items_ref = db.reference(f'menu_items/{item_id}')
    menu_items_ref.update(menu_item)
    
    return jsonify(menu_item)

@app.route('/api/menu-items/<item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Get details for a specific menu item"""
    # Get today's date in YYYYMMDD format for checking published menu first
    today = datetime.now().strftime('%Y%m%d')
    
    # First check if this item exists in today's published menu
    published_menus_ref = db.reference(f'published_menus/{today}')
    published_menu = published_menus_ref.get()
    
    if published_menu and 'items' in published_menu and item_id in published_menu['items']:
        # Return the item from today's published menu
        item = published_menu['items'][item_id]
        # Add the ID to the item
        item['id'] = item_id
        return jsonify(item)
    
    # If not found in today's menu, check the default menu items
    menu_items_ref = db.reference(f'menu_items/{item_id}')
    item = menu_items_ref.get()
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Add the ID to the item
    item['id'] = item_id
    
    return jsonify(item)

@app.route('/api/publish-menu', methods=['POST'])
@admin_required
def publish_menu():
    data = request.json
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    items = data.get('items', {})
    
    # Ensure stock status consistency
    for item_id, item in items.items():
        # If stock_count is 0 or negative, ensure in_stock is False
        if item.get('stock_count', 0) <= 0:
            item['in_stock'] = False
        # If in_stock is False, ensure stock_count is 0
        if not item.get('in_stock', False):
            item['stock_count'] = 0
    
    # Create a published menu entry with the date
    published_menu = {
        'date': date,
        'published_at': datetime.now().isoformat(),
        'published_by': session.get('user_id', 'unknown'),
        'items': items
    }
    
    # Save to Firebase
    published_menus_ref = db.reference('published_menus')
    published_menus_ref.child(date.replace('-', '')).set(published_menu)
    
    return jsonify({'success': True, 'message': f'Menu published for {date}'})


# Add a route to publish today's menu (for testing)
@app.route('/api/publish-today-menu', methods=['GET'])
@admin_required
def publish_today_menu():
    """Publish today's menu with some default items for testing"""
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Get all menu items
    menu_items_ref = db.reference('menu_items')
    all_items = menu_items_ref.get() or {}
    
    # Set some items as in_stock for testing
    published_items = {}
    for item_id, item in all_items.items():
        # Make a copy of the item to avoid modifying the original
        published_item = item.copy()
        # Set all items as in stock for testing
        published_item['in_stock'] = True
        # Set some items as special
        published_item['special'] = item_id in ['appam', 'chicken-biryani', 'mango-lassi']
        published_items[item_id] = published_item
    
    # Create a published menu entry
    published_menu = {
        'date': today,
        'published_at': datetime.now().isoformat(),
        'published_by': session.get('user_id', 'unknown'),
        'items': published_items
    }
    
    # Save to Firebase
    published_menus_ref = db.reference('published_menus')
    published_menus_ref.child(today).set(published_menu)
    
    return jsonify({
        'success': True, 
        'message': f'Menu published for today ({today})'
    })

# Add a route to get today's published menu for non-admin users
@app.route('/api/published-menus/<date>', methods=['GET'])
def get_published_menu_public(date):
    """Get the published menu for a specific date (public access)"""
    published_menus_ref = db.reference(f'published_menus/{date}')
    published_menu = published_menus_ref.get()
    
    if published_menu:
        return jsonify(published_menu)
    else:
        return jsonify({'error': 'No published menu found for this date'}), 404
@app.route('/search', methods=['GET'])
def search():
    """Render the search page and handle search functionality"""
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
        
    try:
        # Get date from query parameter or use today's date
        date = request.args.get('date')
        if not date:
            today = datetime.now()
            date = today.strftime('%Y%m%d')
        else:
            # Format date for database key (remove hyphens if present)
            date = date.replace('-', '')
        
        # Fetch today's published menu
        published_menus_ref = db.reference(f'published_menus/{date}')
        published_menu = published_menus_ref.get()
        
        if not published_menu:
            return render_template('search.html')
        
        # Get all menu items
        menu_items = published_menu.get('items', {})
        
        # Organize items by category
        organized_items = {
            'breakfast': [],
            'lunch': [],
            'drinks': [],
            'desserts': [],
            'curry': []
        }
        
        for item_id, item in menu_items.items():
            category = item.get('category', '').lower()
            if category in organized_items:
                item_with_id = dict(item)
                item_with_id['id'] = item_id
                organized_items[category].append(item_with_id)
        
        return render_template('search.html', menu_items=organized_items)
        
    except Exception as e:
        print(f"Error in search: {str(e)}")
        flash(f'Error retrieving menu data: {str(e)}', 'error')
        return render_template('search.html')


# Add a cart route
@app.route('/cart')
def cart():
    """Render the cart page"""
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
    
    # Fetch user data
    user_id = session['user_id']
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    return render_template('cart.html', user_data=user_data)

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add an item to the user's cart"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    data = request.json
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    
    if not item_id:
        return jsonify({'error': 'Item ID is required', 'success': False}), 400
    
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Fetch today's published menu to check stock status
    published_menus_ref = db.reference(f'published_menus/{today}')
    published_menu = published_menus_ref.get()
    
    if not published_menu or not published_menu.get('items') or item_id not in published_menu.get('items', {}):
        return jsonify({'error': 'Item not available in today\'s menu', 'success': False}), 400
    
    # Get the item from today's menu
    item = published_menu['items'][item_id]
    
    # Check if item is in stock and has stock count > 0
    if not item.get('in_stock', False) or item.get('stock_count', 0) <= 0:
        return jsonify({'error': 'Item is out of stock', 'success': False}), 400
    
    # Check if quantity is valid
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than 0', 'success': False}), 400
    
    if quantity > item.get('stock_count', 0):
        return jsonify({'error': 'Not enough items in stock', 'success': False}), 400
    
    # Get user's cart
    user_id = session['user_id']
    cart_ref = db.reference(f'carts/{user_id}')
    cart = cart_ref.get() or {}
    
    # Add date to cart item to track when it was added
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Update cart
    if item_id in cart:
        # Check if new total quantity exceeds stock
        new_quantity = cart[item_id]['quantity'] + quantity
        if new_quantity > item.get('stock_count', 0):
            return jsonify({'error': f'Cannot add {quantity} more. Only {item.get("stock_count", 0)} items available in stock', 'success': False}), 400
        
        # Update quantity if item exists
        cart[item_id]['quantity'] = new_quantity
        cart[item_id]['updated_at'] = current_date
    else:
        # Add new item to cart
        cart[item_id] = {
            'item_id': item_id,
            'name': item.get('name', ''),
            'price': item.get('price', 0),
            'image_url': item.get('image_url', ''),
            'quantity': quantity,
            'added_at': current_date,
            'menu_date': today  # Store the menu date this item was added from
        }
    
    # Save updated cart
    cart_ref.set(cart)
    
    return jsonify({
        'success': True,
        'message': f'Added {quantity} {item.get("name", "item")}(s) to cart'
    })
def clear_old_cart_items():
    """Clear old cart items that are not in today's menu"""
    # Get all users
    users_ref = db.reference('users')
    users = users_ref.get() or {}
    
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Fetch today's published menu
    published_menus_ref = db.reference(f'published_menus/{today}')
    published_menu = published_menus_ref.get()
    
    if not published_menu or not published_menu.get('items'):
        # No menu published for today, nothing to do
        return
    
    today_items = published_menu.get('items', {})
    
    # Process each user's cart
    for user_id in users:
        cart_ref = db.reference(f'carts/{user_id}')
        cart = cart_ref.get() or {}
        
        if not cart:
            continue
        
        # Filter cart to only include items in today's menu
        updated_cart = {}
        for item_id, item in cart.items():
            if item_id in today_items and today_items[item_id].get('in_stock', False):
                # Item is in today's menu and in stock, keep it
                updated_cart[item_id] = item
        
        # Update cart if items were removed
        if len(cart) != len(updated_cart):
            cart_ref.set(updated_cart)
            print(f"Cleared old cart items for user {user_id}")

@app.route('/update-cart-item', methods=['POST'])
def update_cart_item():
    """Update the quantity of an item in the cart"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    data = request.json
    item_id = data.get('item_id')
    quantity_change = data.get('quantity_change', 0)
    
    if not item_id:
        return jsonify({'error': 'Item ID is required', 'success': False}), 400
    
    # Get user's cart
    user_id = session['user_id']
    cart_ref = db.reference(f'carts/{user_id}')
    cart = cart_ref.get() or {}
    
    # Check if item exists in cart
    if item_id not in cart:
        return jsonify({'error': 'Item not found in cart', 'success': False}), 404
    
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Fetch today's published menu to check stock status
    published_menus_ref = db.reference(f'published_menus/{today}')
    published_menu = published_menus_ref.get()
    
    if not published_menu or not published_menu.get('items') or item_id not in published_menu.get('items', {}):
        # Item is not in today's menu, remove it from cart
        cart.pop(item_id)
        cart_ref.set(cart)
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart as it is not available in today\'s menu',
            'item': {
                'id': item_id,
                'price': 0,
                'quantity': 0,
                'stock_count': 0
            },
            'cart': {
                'items': {},
                'total': 0
            }
        })
    
    # Get the item from today's menu
    menu_item = published_menu['items'][item_id]
    
    # Get current quantity
    current_quantity = cart[item_id].get('quantity', 1)
    
    # Calculate new quantity
    new_quantity = current_quantity + quantity_change
    
    # Handle removal if quantity becomes 0 or negative
    if new_quantity <= 0:
        cart.pop(item_id)
    else:
        # Check if new quantity exceeds stock
        if new_quantity > menu_item.get('stock_count', 0):
            return jsonify({
                'error': f'Cannot add more items. Only {menu_item.get("stock_count", 0)} items available in stock',
                'success': False
            }), 400
        
        # Update quantity
        cart[item_id]['quantity'] = new_quantity
        cart[item_id]['updated_at'] = datetime.now().strftime('%Y-%m-%d')
    
    # Save updated cart
    cart_ref.set(cart)
    
    # Calculate price with discount
    price = menu_item.get('price', 0)
    discount = menu_item.get('discount', 0)
    discounted_price = price - (price * discount / 100) if discount > 0 else price
    
    # Process cart items with current prices and calculate total
    processed_items = {}
    total = 0
    
    for cart_item_id, cart_item in cart.items():
        if cart_item_id in published_menu.get('items', {}):
            item = published_menu['items'][cart_item_id]
            item_price = item.get('price', 0)
            item_discount = item.get('discount', 0)
            item_discounted_price = item_price - (item_price * item_discount / 100) if item_discount > 0 else item_price
            
            total += item_discounted_price * cart_item.get('quantity', 1)
            
            processed_items[cart_item_id] = {
                'id': cart_item_id,
                'name': item.get('name', ''),
                'price': item_discounted_price,
                'original_price': item_price,
                'discount': item_discount,
                'image_url': item.get('image_url', ''),
                'quantity': cart_item.get('quantity', 1),
                'in_stock': item.get('in_stock', False),
                'stock_count': item.get('stock_count', 0)
            }
    
    return jsonify({
        'success': True,
        'message': 'Cart updated successfully',
        'item': {
            'id': item_id,
            'price': discounted_price,
            'quantity': new_quantity if new_quantity > 0 else 0,
            'stock_count': menu_item.get('stock_count', 0)
        },
        'cart': {
            'items': processed_items,
            'total': total
        }
    })

# Add these routes to your Flask app for Razorpay integration

import razorpay
import json
import hmac
import hashlib

# Initialize Razorpay client
razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")
razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))


@app.route('/create-razorpay-order', methods=['POST'])
def create_razorpay_order():
    """Create a Razorpay order or reuse an existing pending order"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    try:
        data = request.json
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return jsonify({'error': 'Invalid amount', 'success': False}), 400
        
        # Get user details
        user_id = session['user_id']
        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get() or {}
        
        # Get cart items
        cart_ref = db.reference(f'carts/{user_id}')
        cart = cart_ref.get() or {}
        
        # Check for existing pending orders for this user (within past 24 hours)
        orders_ref = db.reference('orders')
        # Use indexOn in Firebase rules to optimize this query if you have many orders
        # Get all orders and filter on the client side
        all_orders = orders_ref.get() or {}
        
        # Find recent pending orders for this user
        pending_order = None
        one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        
        for order_id, order in all_orders.items():
            if (order.get('user_id') == user_id and 
                order.get('payment_status') == 'pending' and 
                order.get('created_at', '') > one_day_ago):
                # Found a pending order for this user
                pending_order = order
                pending_order_id = order_id
                break
        
        # If we found a pending order, update it rather than creating a new one
        if pending_order:
            # Update the existing order with new cart items and amount
            order_ref = db.reference(f'orders/{pending_order_id}')
            order_ref.update({
                'amount': amount / 100,  # Convert to rupees for storage
                'items': cart,
                'updated_at': datetime.now().isoformat()
            })
            
            # Get the Razorpay order ID
            razorpay_order_id = pending_order.get('order_id')
            
            # Check if we need to create a new Razorpay order (if amount changed)
            if pending_order.get('amount') != amount / 100:
                # Create a new Razorpay order
                order_data = {
                    'amount': amount,  # amount in paise
                    'currency': 'INR',
                    'receipt': f'order_{int(time.time())}',
                    'payment_capture': 1  # auto-capture
                }
                
                order = razorpay_client.order.create(data=order_data)
                razorpay_order_id = order['id']
                
                # Update the order with the new Razorpay order ID
                order_ref.update({
                    'order_id': razorpay_order_id
                })
            
            return jsonify({
                'success': True,
                'order_id': razorpay_order_id,
                'razorpay_key_id': razorpay_key_id,
                'user_name': user_data.get('name', ''),
                'user_email': user_data.get('email', ''),
                'user_phone': user_data.get('phone', '')
            })
        else:
            # No pending order found, create a new one
            order_data = {
                'amount': amount,  # amount in paise
                'currency': 'INR',
                'receipt': f'order_{int(time.time())}',
                'payment_capture': 1  # auto-capture
            }
            
            order = razorpay_client.order.create(data=order_data)
            order_id = order['id']
            
            # Store order in database
            order_data = {
                'order_id': order_id,
                'user_id': user_id,
                'amount': amount / 100,  # Convert back to rupees for storage
                'currency': 'INR',
                'status': 'created',
                'created_at': datetime.now().isoformat(),
                'items': cart,
                'payment_status': 'pending'
            }
            
            orders_ref.child(order_id).set(order_data)
            
            return jsonify({
                'success': True,
                'order_id': order_id,
                'razorpay_key_id': razorpay_key_id,
                'user_name': user_data.get('name', ''),
                'user_email': user_data.get('email', ''),
                'user_phone': user_data.get('phone', '')
            })
    
    except Exception as e:
        print(f"Error creating/updating Razorpay order: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    """Verify Razorpay payment signature and update stock quantities"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    try:
        data = request.json
        
        # Get payment details
        payment_id = data.get('razorpay_payment_id', '')
        order_id = data.get('razorpay_order_id', '')
        signature = data.get('razorpay_signature', '')
        
        if not payment_id or not order_id or not signature:
            return jsonify({'error': 'Missing payment details', 'success': False}), 400
        
        # Verify signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id
        }
        
        # Generate signature
        generated_signature = hmac.new(
            razorpay_key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature == signature:
            # Signature is valid, update order status
            user_id = session['user_id']
            
            # Find the order in Firebase by Razorpay order ID
            orders_ref = db.reference('orders')
            order_found = False
            
            # Query orders to find the one with matching Razorpay order ID
            all_orders = orders_ref.get() or {}
            for firebase_order_id, order_data in all_orders.items():
                if order_data.get('order_id') == order_id:
                    # Found the matching order
                    order_ref = db.reference(f'orders/{firebase_order_id}')
                    order = order_data
                    order_found = True
                    break
            
            if not order_found:
                return jsonify({'error': 'Order not found', 'success': False}), 404
            
            # Update order status
            order_ref.update({
                'payment_id': payment_id,
                'payment_status': 'completed',
                'status': 'paid',
                'updated_at': datetime.now().isoformat()
            })
            
            # Update stock quantities
            if 'items' in order:
                # Get today's date in YYYYMMDD format
                today = datetime.now().strftime('%Y%m%d')
                
                # Get the published menu for today
                published_menu_ref = db.reference(f'published_menus/{today}')
                published_menu = published_menu_ref.get()
                
                if published_menu and 'items' in published_menu:
                    # Update stock for each item in the order
                    updates = {}
                    
                    for item_id, item_data in order['items'].items():
                        if item_id in published_menu['items']:
                            menu_item = published_menu['items'][item_id]
                            quantity = item_data.get('quantity', 1)
                            
                            # Calculate new stock count
                            current_stock = menu_item.get('stock_count', 0)
                            new_stock = max(0, current_stock - quantity)
                            
                            # Update stock count
                            updates[f'items/{item_id}/stock_count'] = new_stock
                            
                            # Update in_stock status if stock becomes 0
                            if new_stock == 0:
                                updates[f'items/{item_id}/in_stock'] = False
                    
                    # Apply updates to the published menu
                    if updates:
                        published_menu_ref.update(updates)
                        
                        # Also update the default menu items for future reference
                        default_menu_ref = db.reference('menu_items')
                        for item_id, item_data in order['items'].items():
                            default_item_ref = default_menu_ref.child(item_id)
                            default_item = default_item_ref.get()
                            
                            if default_item:
                                quantity = item_data.get('quantity', 1)
                                current_stock = default_item.get('stock_count', 0)
                                new_stock = max(0, current_stock - quantity)
                                
                                default_item_ref.update({
                                    'stock_count': new_stock,
                                    'in_stock': new_stock > 0
                                })
            
            # Clear user's cart after successful payment
            cart_ref = db.reference(f'carts/{user_id}')
            cart_ref.delete()
            
            return jsonify({
                'success': True,
                'message': 'Payment verified successfully',
                'order_id': order_id
            })
        else:
            # Invalid signature
            return jsonify({
                'success': False,
                'error': 'Invalid payment signature'
            }), 400
    
    except Exception as e:
        print(f"Error verifying payment: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

# Add a helper function to get pending orders for frontend use
@app.route('/api/get-pending-orders', methods=['GET'])
def get_pending_orders():
    """Get pending orders for the current user"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    try:
        user_id = session['user_id']
        
        # Get all orders and filter for pending ones
        orders_ref = db.reference('orders')
        all_orders = orders_ref.get() or {}
        
        # Find all pending orders for this user (within the last 24 hours)
        pending_orders = []
        one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        
        for order_id, order in all_orders.items():
            if (order.get('user_id') == user_id and 
                order.get('payment_status') == 'pending' and 
                order.get('created_at', '') > one_day_ago):
                # Found a pending order for this user
                order['firebase_order_id'] = order_id
                pending_orders.append(order)
        
        return jsonify({
            'success': True,
            'pending_orders': pending_orders
        })
    
    except Exception as e:
        print(f"Error getting pending orders: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/get-razorpay-key', methods=['GET'])
def get_razorpay_key():
    """Return the Razorpay key ID for the frontend"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    return jsonify({
        'success': True,
        'razorpay_key_id': razorpay_key_id
    })

@app.route('/order-confirmation/<order_id>')
def order_confirmation(order_id):
    """Show order confirmation page"""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
    
    # Get order details from Firebase
    order_ref = db.reference(f'orders/{order_id}')
    order = order_ref.get()
    
    if not order or order.get('user_id') != session['user_id']:
        flash('Order not found', 'error')
        return redirect(url_for('home'))
    
    # Ensure order has required fields
    if 'order_id' not in order:
        order['order_id'] = order_id
    
    # Process the items from the nested structure
    processed_items = []

    if 'items' in order and order['items']:
        for item_id, item_data in order['items'].items():
            # Check if item_data is a dictionary
            if isinstance(item_data, dict):
                # Get the menu date this item was ordered from
                menu_date = item_data.get('menu_date', datetime.now().strftime('%Y%m%d'))
                
                # Get the published menu for that date to check for discount
                published_menu_ref = db.reference(f'published_menus/{menu_date}')
                published_menu = published_menu_ref.get()
                
                # Initialize variables with defaults
                quantity = item_data.get('quantity', 1)
                original_price = item_data.get('price', 0)
                discount = item_data.get('discount', 0)
                final_price = original_price
                
                # Try to get discount information from the published menu
                if published_menu and 'items' in published_menu and item_id in published_menu['items']:
                    published_item = published_menu['items'][item_id]
                    original_price = published_item.get('price', original_price)
                    discount = published_item.get('discount', discount)
                
                # Apply discount if available
                if discount > 0:
                    final_price = original_price - (original_price * discount / 100)
                
                # Create item info object
                item_info = {
                    'name': item_data.get('name', 'Unknown Item'),
                    'price': final_price,
                    'original_price': original_price,
                    'discount': discount,
                    'quantity': quantity,
                    'image_url': item_data.get('image_url', '')
                }
                
                processed_items.append([item_id, item_info])

    # Update the order object with processed items
    order['order_items'] = processed_items
    
    # Calculate total amount based on processed items
    total_amount = sum(item[1]['price'] * item[1]['quantity'] for item in processed_items)
    
    # Update the amount if it doesn't match our calculation (with a small tolerance for floating point comparison)
    if 'amount' not in order or abs(order['amount'] - total_amount) > 0.01:
        order['amount'] = total_amount
        order_ref.update({'amount': total_amount})
    
    # Check if the order is cancellable (within 30 minutes of creation)
    if 'created_at' in order:
        try:
            order_time = datetime.fromisoformat(order['created_at'])
        except (ValueError, TypeError):
            order_time = datetime.now()
    else:
        order_time = datetime.now()
        
    current_time = datetime.now()
    time_diff = current_time - order_time
    
    # Order is cancellable if it's within 30 minutes and status is not cancelled
    is_cancellable = (time_diff.total_seconds() < 1800) and order.get('status') != 'cancelled'
    
    # Calculate minutes left for cancellation
    minutes_left = max(0, 30 - int(time_diff.total_seconds() / 60))
    
    # Add cancellation info to order object
    order['cancellable'] = is_cancellable
    order['minutes_left'] = minutes_left
    
    # Add debugging info
    print(f"Order ID: {order_id}")
    print(f"Order Items Count: {len(processed_items)}")
    print(f"Order Items: {processed_items}")
    
    # Render the template with the order data
    return render_template('order-confirmation.html', order=order)

# Modify the get-cart-items route to only return today's items
@app.route('/get-cart-items')
def get_cart_items():
    """Get all items in the user's cart, filtering for today's items only"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    # Get user's cart
    user_id = session['user_id']
    cart_ref = db.reference(f'carts/{user_id}')
    cart = cart_ref.get() or {}
    
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Fetch today's published menu to get current prices and stock status
    published_menus_ref = db.reference(f'published_menus/{today}')
    published_menu = published_menus_ref.get()
    
    # Process cart items with current prices and stock status
    processed_items = {}
    total = 0
    
    if published_menu and published_menu.get('items'):
        menu_items = published_menu.get('items', {})
        
        # Filter cart items to only include items that are in today's menu
        for item_id, cart_item in cart.items():
            if item_id in menu_items:
                menu_item = menu_items[item_id]
                
                # Only include items that are in stock
                if menu_item.get('in_stock', False) and menu_item.get('stock_count', 0) > 0:
                    # Calculate price with discount
                    price = menu_item.get('price', 0)
                    discount = menu_item.get('discount', 0)
                    discounted_price = price - (price * discount / 100) if discount > 0 else price
                    
                    # Ensure quantity doesn't exceed current stock
                    quantity = min(cart_item.get('quantity', 1), menu_item.get('stock_count', 0))
                    
                    # Calculate item total
                    item_total = discounted_price * quantity
                    total += item_total
                    
                    # Add processed item to result
                    processed_items[item_id] = {
                        'id': item_id,
                        'name': menu_item.get('name', ''),
                        'price': discounted_price,
                        'original_price': price,
                        'discount': discount,
                        'image_url': menu_item.get('image_url', ''),
                        'quantity': quantity,
                        'in_stock': menu_item.get('in_stock', True),
                        'stock_count': menu_item.get('stock_count', 0)
                    }
    
    # Update the cart in the database to remove items that are not in today's menu
    if cart and len(cart) != len(processed_items):
        # Only keep items that are in processed_items
        updated_cart = {item_id: cart[item_id] for item_id in processed_items}
        cart_ref.set(updated_cart)
    
    return jsonify({
        'success': True,
        'cart': {
            'items': processed_items,
            'total': total
        }
    })
@app.route('/api/update-stock', methods=['POST'])
def update_stock():
    try:
        data = request.json
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID is required'}), 400
        
        # Fetch order details
        order_ref = db.reference(f'orders/{order_id}')
        order = order_ref.get()
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get today's date in YYYYMMDD format
        today = datetime.now().strftime('%Y%m%d')
        
        # Get the published menu for today
        published_menu_ref = db.reference(f'published_menus/{today}')
        published_menu = published_menu_ref.get()
        
        if not published_menu or not published_menu.get('items'):
            return jsonify({'success': False, 'error': 'Menu not found'}), 404
        
        # Update stock for each item in the order
        updates = {}
        stock_updated = False
        
        if 'items' in order:
            for item_id, item_data in order['items'].items():
                if item_id in published_menu['items']:
                    menu_item = published_menu['items'][item_id]
                    quantity = item_data.get('quantity', 1)
                    
                    # Calculate new stock count
                    current_stock = menu_item.get('stock_count', 0)
                    new_stock = max(0, current_stock - quantity)
                    
                    # Update stock count
                    updates[f'items/{item_id}/stock_count'] = new_stock
                    
                    # Update in_stock status if stock becomes 0
                    if new_stock == 0:
                        updates[f'items/{item_id}/in_stock'] = False
                    
                    stock_updated = True
        
        # Apply updates to the published menu
        if stock_updated:
            published_menu_ref.update(updates)
            
            # Also update the default menu items for future reference
            default_menu_ref = db.reference('menu_items')
            for item_id, item_data in order['items'].items():
                default_item_ref = default_menu_ref.child(item_id)
                default_item = default_item_ref.get()
                
                if default_item:
                    quantity = item_data.get('quantity', 1)
                    current_stock = default_item.get('stock_count', 0)
                    new_stock = max(0, current_stock - quantity)
                    
                    default_item_ref.update({
                        'stock_count': new_stock,
                        'in_stock': new_stock > 0
                    })
        
        # Update order status to indicate stock has been updated
        order_ref.update({'stock_updated': True})
        
        return jsonify({'success': True, 'message': 'Stock updated successfully'})
    
    except Exception as e:
        print(f"Error updating stock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Generate and download invoice for an order
@app.route('/download-invoice/<order_id>', methods=['GET'])
def download_invoice(order_id):
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'error': 'User not logged in', 'success': False}), 401
        
        # Fetch order details
        order_ref = db.reference(f'orders/{order_id}')
        order = order_ref.get()
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Check if the order belongs to the logged-in user
        if order.get('user_id') != session['user_id']:
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        
        # Fetch user details
        user_ref = db.reference(f'users/{order["user_id"]}')
        user = user_ref.get() or {'name': 'Customer'}
        
        # Get order status (default to pending if not available)
        order_status = order.get('status', 'pending').upper()
        
        # Process items to ensure discounts are correctly applied
        processed_items = []
        if 'items' in order:
            for item_id, item_data in order['items'].items():
                if isinstance(item_data, dict):
                    # Get the menu date this item was ordered from
                    menu_date = item_data.get('menu_date', datetime.now().strftime('%Y%m%d'))
                    
                    # Get the published menu for that date to check for discount
                    published_menu_ref = db.reference(f'published_menus/{menu_date}')
                    published_menu = published_menu_ref.get()
                    
                    # Initialize variables with defaults
                    name = item_data.get('name', 'Unknown Item')
                    quantity = item_data.get('quantity', 1)
                    original_price = item_data.get('price', 0)
                    discount = 0
                    
                    # Try to get discount information from the published menu
                    if published_menu and 'items' in published_menu and item_id in published_menu['items']:
                        published_item = published_menu['items'][item_id]
                        name = published_item.get('name', name)
                        original_price = published_item.get('price', original_price)
                        discount = published_item.get('discount', 0)
                    
                    # Calculate final price with discount
                    final_price = original_price
                    if discount > 0:
                        final_price = original_price - (original_price * discount / 100)
                    
                    processed_items.append({
                        'name': name,
                        'price': final_price,
                        'original_price': original_price,
                        'discount': discount,
                        'quantity': quantity,
                        'total': final_price * quantity
                    })
        
        # Create a PDF buffer
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Create custom style for prices and status
        price_style = ParagraphStyle(
            'PriceStyle',
            parent=normal_style,
            alignment=2,  # Right aligned
            fontName='Helvetica'
        )
        
        # Create status style with appropriate color
        status_color = colors.black
        if order_status.lower() == 'cancelled':
            status_color = colors.red
        elif order_status.lower() == 'approved':
            status_color = colors.green
        elif order_status.lower() == 'paid':
            status_color = colors.blue
            
        status_style = ParagraphStyle(
            'StatusStyle',
            parent=subtitle_style,
            textColor=status_color
        )
        
        # Add title
        elements.append(Paragraph("OrderByte", title_style))
        
        # Create a table for the header to place Invoice and Status side by side
        header_data = [
            [Paragraph("INVOICE", subtitle_style), 
             Paragraph(f"Status: {order_status}", status_style)]
        ]
        header_table = Table(header_data, colWidths=[4*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)
        
        # Add watermark for cancelled orders
        if order_status.lower() == 'cancelled':
            # Using a flowable watermark technique
            class Watermark(Flowable):
                def __init__(self, text="CANCELLED"):
                    Flowable.__init__(self)
                    self.text = text
                
                def draw(self):
                    canvas = self.canv
                    canvas.saveState()
                    canvas.setFont('Helvetica-Bold', 72)
                    canvas.setFillColor(colors.red)
                    canvas.setFillAlpha(0.3)  # Set transparency
                    canvas.translate(letter[0]/2, letter[1]/2)  # Center of the page
                    canvas.rotate(45)  # Rotate 45 degrees
                    canvas.drawCentredString(0, 0, self.text)
                    canvas.restoreState()
            
            elements.append(Watermark())
        
        elements.append(Spacer(1, 0.25*inch))
        
        # Add invoice details
        elements.append(Paragraph(f"Invoice #: {order_id[:8]}", normal_style))
        # Add payment ID if available
        if 'payment_id' in order and order['payment_id']:
            elements.append(Paragraph(f"Payment ID: {order['payment_id']}", normal_style))
        elements.append(Paragraph(f"Date: {order.get('created_at', '').split('T')[0]}", normal_style))
        elements.append(Paragraph(f"Time: {order.get('created_at', '').split('T')[1][:8]}", normal_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add customer details
        elements.append(Paragraph("Bill To:", normal_style))
        elements.append(Paragraph(f"Name: {user.get('name', 'Customer')}", normal_style))
        elements.append(Paragraph(f"Email: {user.get('email', 'N/A')}", normal_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add order items table
        table_data = [['Item', 'Price', 'Quantity', 'Total']]
        
        subtotal = 0
        total_savings = 0
        
        for item in processed_items:
            name = item['name']
            price = item['price']
            original_price = item['original_price']
            quantity = item['quantity']
            total = price * quantity
            
            # Calculate savings if there's a discount
            if item['discount'] > 0:
                savings = (original_price - price) * quantity
                total_savings += savings
                price_text = f"Rs. {price:.2f} ({item['discount']}% off)"
            else:
                price_text = f"Rs. {price:.2f}"
            
            table_data.append([
                name,
                Paragraph(price_text, price_style),
                str(quantity),
                Paragraph(f"Rs. {total:.2f}", price_style)
            ])
            
            subtotal += total
        
        # Create the table
        table = Table(table_data, colWidths=[3*inch, 1.5*inch, 0.5*inch, 1*inch])
        
        # Add style to the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Center align quantity column
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),   # Right align price column
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Right align total column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE') # Vertically center all cells
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add total with proper currency formatting
        total_table_data = [
            ['Subtotal:', Paragraph(f"Rs. {subtotal:.2f}", price_style)]
        ]
        
        # Add savings row if there are discounts
        if total_savings > 0:
            total_table_data.append(['You Saved:', Paragraph(f"Rs. {total_savings:.2f}", price_style)])
        
        total_table_data.extend([
            ['Tax (0%):', Paragraph("Rs. 0.00", price_style)],
            ['Total:', Paragraph(f"Rs. {subtotal:.2f}", price_style)]
        ])
        
        total_table = Table(total_table_data, colWidths=[4*inch, 2*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(total_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Add a note for cancelled orders
        if order_status.lower() == 'cancelled':
            cancelled_style = ParagraphStyle(
                'CancelledNote',
                parent=normal_style,
                textColor=colors.red,
                fontSize=12,
                fontName='Helvetica-Bold'
            )
            elements.append(Paragraph(
                "Note: This order has been cancelled. No payment is due.", 
                cancelled_style
            ))
            elements.append(Spacer(1, 0.25*inch))
        
        # Add footer
        elements.append(Paragraph("Thank you for your order!", normal_style))
        elements.append(Paragraph("OrderByte - Delicious food at your fingertips", normal_style))
        
        # Build the PDF
        doc.build(elements)
        
        # Reset buffer position
        buffer.seek(0)
        
        # Create response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice-{order_id[:8]}.pdf'
        
        return response
    
    except Exception as e:
        print(f"Error generating invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Order cancellation route
@app.route('/api/orders/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order if it's within 30 minutes of creation"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    try:
        # Get the order
        order_ref = db.reference(f'orders/{order_id}')
        order = order_ref.get()
        
        if not order:
            return jsonify({'error': 'Order not found', 'success': False}), 404
        
        # Check if the order belongs to the current user
        if order.get('user_id') != session['user_id']:
            return jsonify({'error': 'Unauthorized access', 'success': False}), 403
        
        # Check if the order is already cancelled
        if order.get('status') == 'cancelled':
            return jsonify({'error': 'Order is already cancelled', 'success': False}), 400
        
        # Check if the order is within 30 minutes
        created_at = datetime.fromisoformat(order.get('created_at').replace('Z', '+00:00'))
        current_time = datetime.now(created_at.tzinfo)
        time_diff = current_time - created_at
        
        if time_diff.total_seconds() > 30 * 60:  # 30 minutes in seconds
            return jsonify({'error': 'Order cancellation window has expired (30 minutes)', 'success': False}), 400
        
        # Update order status
        # For Razorpay test mode, we'll use 'cancelled' for status but keep payment_status as 'paid'
        # This prevents showing 'refunded' when using test mode
        order_ref.update({
            'status': 'cancelled',
            'payment_status': 'paid',  # Keep as 'paid' instead of 'refunded' for test mode
            'cancellation_note': 'Order cancelled by user within 30-minute window',
            'cancelled_at': datetime.now().isoformat(),
            'cancelled_by': session['user_id']
        })
        
        # If this was a real app with real payments, you would:
        # 1. Process refund through Razorpay API
        # 2. Update inventory/stock counts
        # 3. Send cancellation notification emails
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully',
            'order_id': order_id
        })
        
    except Exception as e:
        print(f"Error cancelling order: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

# Profile page route
@app.route('/profile')
def profile():
    """Render the user profile page"""
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
    
    # Fetch user data
    user_id = session['user_id']
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    # Fetch user's orders
    orders_ref = db.reference('orders')
    all_orders = orders_ref.get() or {}
    
    # Filter orders for this user and sort by date (newest first)
    user_orders = []
    for order_id, order in all_orders.items():
        if order.get('user_id') == user_id:
            # Add order_id to the order data
            order['order_id'] = order_id
            
            # Format the date for display
            if 'created_at' in order:
                created_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                order['date'] = created_date.strftime('%Y-%m-%d')
                order['time'] = created_date.strftime('%H:%M:%S')
            
            # Check if order is cancellable (within 30 minutes)
            order['cancellable'] = False
            if order.get('status') != 'cancelled' and 'created_at' in order:
                created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                current_time = datetime.now(created_at.tzinfo)
                time_diff = current_time - created_at
                
                if time_diff.total_seconds() <= 30 * 60:  # 30 minutes in seconds
                    order['cancellable'] = True
                    minutes_left = 30 - int(time_diff.total_seconds() / 60)
                    order['minutes_left'] = minutes_left
            
            user_orders.append(order)
    
    # Sort orders by created_at date (newest first)
    user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('profile.html', user_data=user_data, user_id=user_id, orders=user_orders)

# API route to update user profile
@app.route('/api/user/<user_id>/profile', methods=['POST'])
def update_user_profile(user_id):
    try:
        # Check if user_id is "admin" (special case)
        if user_id == "admin":
            # Try to get the actual admin user ID from the session
            actual_user_id = session.get('user_id')
            if actual_user_id:
                user_id = actual_user_id
            else:
                # Get the admin user from admins collection
                admins_ref = db.reference('admins')
                admins = admins_ref.get()
                if admins:
                    # Get the first admin ID
                    admin_id = list(admins.keys())[0]
                    user_id = admin_id
        
        # First get the existing user data to preserve all fields
        user_ref = db.reference('users').child(user_id)
        existing_user_data = user_ref.get() or {}
        
        # Create updates object, preserving existing data
        updates = existing_user_data.copy()
        
        # Get form data and update only if provided
        if 'name' in request.form and request.form['name']:
            updates['name'] = request.form['name']
        if 'email' in request.form and request.form['email']:
            updates['email'] = request.form['email']
        if 'phone' in request.form and request.form['phone']:
            updates['phone'] = request.form['phone']
        
        # Handle profile picture upload if present
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Create a secure filename
                filename = secure_filename(file.filename)
                # Create unique filename with timestamp
                unique_filename = f"{user_id}_{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                # Save the file
                file.save(file_path)
                # Update the profile picture path
                updates['profile_picture'] = f"/static/uploads/{unique_filename}"
        
        # Update the user data in the database
        user_ref.set(updates)  # Use set instead of update to ensure complete data update
        
        # Return updated profile data for UI refresh
        return jsonify({
            'success': True, 
            'data': {
                'profile_picture': updates.get('profile_picture', '/static/uploads/default_user.png')
            }
        })
    except Exception as e:
        app.logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
# API route to get user orders
@app.route('/api/user/<user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """Get all orders for a user"""
    if 'user_id' not in session or session['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized', 'success': False}), 403
    
    try:
        # Fetch all orders
        orders_ref = db.reference('orders')
        all_orders = orders_ref.get() or {}
        
        # Filter orders for this user and sort by date (newest first)
        user_orders = []
        for order_id, order in all_orders.items():
            if order.get('user_id') == user_id:
                # Add order_id to the order data
                order['order_id'] = order_id
                
                # Format the date for display
                if 'created_at' in order:
                    created_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    order['date'] = created_date.strftime('%Y-%m-%d')
                    order['time'] = created_date.strftime('%H:%M:%S')
                
                # Check if order is cancellable (within 30 minutes)
                order['cancellable'] = False
                if order.get('status') != 'cancelled' and 'created_at' in order:
                    created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    current_time = datetime.now(created_at.tzinfo)
                    time_diff = current_time - created_at
                    
                    if time_diff.total_seconds() <= 30 * 60:  # 30 minutes in seconds
                        order['cancellable'] = True
                        minutes_left = 30 - int(time_diff.total_seconds() / 60)
                        order['minutes_left'] = minutes_left
                
                # Process items for display
                if 'items' in order:
                    item_names = []
                    total_amount = 0
                    
                    for item_id, item_data in order['items'].items():
                        # Get the item details from the menu_items collection
                        menu_item_ref = db.reference(f'menu_items/{item_id}')
                        menu_item = menu_item_ref.get()
                        
                        if menu_item and isinstance(item_data, dict):
                            # Add item name to the list
                            item_names.append(menu_item.get('name', 'Unknown Item'))
                            
                            # Calculate price with discount
                            price = menu_item.get('price', 0)
                            discount = menu_item.get('discount', 0)
                            quantity = item_data.get('quantity', 1)
                            
                            if discount > 0:
                                price = price - (price * discount / 100)
                            
                            total_amount += price * quantity
                    
                    order['item_list'] = item_names
                    
                    # Update the amount to reflect discounts if not already set
                    if 'amount' not in order or order['amount'] == 0:
                        order['amount'] = total_amount
                
                user_orders.append(order)
        
        # Sort orders by created_at date (newest first)
        user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'orders': user_orders
        })
        
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/user/current', methods=['GET'])
def get_current_user():
    """Get current user data"""
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in', 'success': False}), 401
    
    try:
        user_id = session['user_id']
        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get()
        
        if not user_data:
            return jsonify({'error': 'User not found', 'success': False}), 404
        
        # Add user_id to the data
        user_data['user_id'] = user_id
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        print(f"Error fetching user data: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/order', methods=['GET'])
def order():
    """Render the order page with orders from Firebase Realtime Database sorted by date"""
    # Initialize user_data as None
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    # Get user data if logged in
    user_id = session.get('user_id')
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    # Get date parameter from query string or use today's date
    date_param = request.args.get('date')
    if date_param:
        # Format date for database key (remove hyphens if present)
        filter_date = date_param.replace('-', '')
    else:
        # Use today's date by default
        today = datetime.now()
        filter_date = today.strftime('%Y%m%d')
    
    try:
        # Fetch all orders from the 'orders' node
        orders_ref = db.reference('orders')
        orders_data = orders_ref.get()
        
        # If no orders exist, initialize as empty dict
        if orders_data is None:
            orders_data = {}
        
        # Process orders to match the expected format in the JavaScript
        processed_orders = {}
        for order_id, order in orders_data.items():
            # Skip orders without timestamp/created_at
            if not order.get('created_at') and not order.get('order_date'):
                continue
                
            # Get order date for filtering
            order_date = None
            timestamp = None
            if order.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(order.get('created_at').replace('Z', '+00:00'))
                    order_date = created_at.strftime('%Y%m%d')
                    timestamp = order.get('created_at')  # Keep the original timestamp
                except (ValueError, AttributeError):
                    pass
            elif order.get('order_date'):
                order_date = order.get('order_date').replace('-', '')
                timestamp = order.get('order_date')
            
            # Skip if order date doesn't match filter date (only show today's orders by default)
            if order_date != filter_date:
                continue
                
            processed_order = {
                'id': order_id,  # Ensure we have the ID
                'timestamp': timestamp,
                'status': order.get('status'),  # Get the actual status first
                'payment_status': order.get('payment_status'),
                'amount': float(order.get('amount', 0)),  # Keep original amount field
                'total': float(order.get('amount', 0)),  # Convert string to float and map to total
                'customerName': 'Customer',  # Default name
                'items': order.get('items', {})
            }
            
            # Look up customer info if user_id is available
            if 'user_id' in order:
                user_ref = db.reference(f'users/{order["user_id"]}')
                user_info = user_ref.get()
                if user_info:
                    processed_order['customerName'] = user_info.get('name', 'Customer')
                    processed_order['customerPhone'] = user_info.get('phone', 'N/A')
                    processed_order['customerAddress'] = user_info.get('address', 'N/A')
            
            processed_orders[order_id] = processed_order
        
        # Always pass user_data to the template
        return render_template('order.html', orders=processed_orders, user_data=user_data)
    
    except Exception as e:
        # Log the error and return an empty orders dict
        print(f"Error retrieving orders: {str(e)}")
        return render_template('order.html', orders={}, user_data=user_data, error=str(e))

# Add a new route to get orders by date (for AJAX requests)
@app.route('/api/orders/by-date/<date_str>', methods=['GET'])
@admin_required
def get_orders_by_date(date_str):
    """Get orders for a specific date"""
    try:
        # Format date for database key (remove hyphens if present)
        filter_date = date_str.replace('-', '')
        
        # Fetch all orders from the 'orders' node
        orders_ref = db.reference('orders')
        orders_data = orders_ref.get() or {}
        
        # Filter orders by date
        filtered_orders = {}
        for order_id, order in orders_data.items():
            # Get order date for filtering
            order_date = None
            timestamp = None
            if order.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(order.get('created_at').replace('Z', '+00:00'))
                    order_date = created_at.strftime('%Y%m%d')
                    timestamp = order.get('created_at')
                except (ValueError, AttributeError):
                    pass
            elif order.get('order_date'):
                order_date = order.get('order_date').replace('-', '')
                timestamp = order.get('order_date')
            
            # Include order if date matches
            if order_date == filter_date:
                # Process the order for the frontend
                processed_order = {
                    'id': order_id,  # Include the order ID
                    'timestamp': timestamp,
                    'status': order.get('status'),
                    'payment_status': order.get('payment_status'),
                    'amount': float(order.get('amount', 0)),
                    'total': float(order.get('amount', 0)),
                    'customerName': 'Customer',  # Default name
                    'items': order.get('items', {})
                }
                
                # Look up customer info if user_id is available
                if 'user_id' in order:
                    user_ref = db.reference(f'users/{order["user_id"]}')
                    user_info = user_ref.get()
                    if user_info:
                        processed_order['customerName'] = user_info.get('name', 'Customer')
                        processed_order['customerPhone'] = user_info.get('phone', 'N/A')
                        processed_order['customerEmail'] = user_info.get('email', 'N/A')
                filtered_orders[order_id] = processed_order
        
        return jsonify({
            'success': True,
            'date': date_str,
            'orders': filtered_orders,
            'count': len(filtered_orders)
        })
    
    except Exception as e:
        print(f"Error retrieving orders by date: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# Add a route to get order details with discounted prices
@app.route('/admin/order-details/<order_id>', methods=['GET'])
@admin_required
def admin_order_details(order_id):
    """Get detailed order information for admin view with discounted prices"""
    try:
        # Fetch the specific order from Firebase
        order_ref = db.reference(f'orders/{order_id}')
        order_data = order_ref.get()
        
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Add the order_id to the data for display purposes
        order_data['order_id'] = order_id
        
        # Make sure total is available - use amount if total is not present
        if 'amount' in order_data and not 'total' in order_data:
            order_data['total'] = float(order_data['amount'])
        
        # Look up customer information if user_id is available
        if 'user_id' in order_data:
            user_ref = db.reference(f'users/{order_data["user_id"]}')
            user_info = user_ref.get()
            if user_info:
                order_data['customerName'] = user_info.get('name', 'Customer')
                order_data['customerPhone'] = user_info.get('phone', 'N/A')
                order_data['customerAddress'] = user_info.get('address', 'N/A')
                order_data['customerEmail'] = user_info.get('email', 'N/A')
        # Ensure timestamp is available
        if not order_data.get('timestamp'):
            order_data['timestamp'] = order_data.get('created_at') or order_data.get('order_date')
        
        # Process items to include discount information
        if 'items' in order_data and order_data['items']:
            processed_items = {}
            
            for item_id, item in order_data['items'].items():
                if isinstance(item, dict):
                    # Get the menu date this item was ordered from
                    menu_date = item.get('menu_date', datetime.now().strftime('%Y%m%d'))
                    
                    # Get the published menu for that date to check for discount
                    published_menu_ref = db.reference(f'published_menus/{menu_date}')
                    published_menu = published_menu_ref.get()
                    
                    # Initialize variables with defaults
                    name = item.get('name', 'Unknown Item')
                    quantity = item.get('quantity', 1)
                    original_price = item.get('price', 0)
                    discount = 0
                    
                    # Try to get discount information from the published menu
                    if published_menu and 'items' in published_menu and item_id in published_menu['items']:
                        published_item = published_menu['items'][item_id]
                        name = published_item.get('name', name)
                        original_price = published_item.get('price', original_price)
                        discount = published_item.get('discount', 0)
                    
                    # Calculate final price with discount
                    final_price = original_price
                    if discount > 0:
                        final_price = original_price - (original_price * discount / 100)
                    
                    # Update the item with discount information
                    processed_item = item.copy()
                    processed_item['name'] = name
                    processed_item['original_price'] = original_price
                    processed_item['discount'] = discount
                    processed_item['price'] = final_price
                    processed_item['quantity'] = quantity
                    
                    processed_items[item_id] = processed_item
                else:
                    # If item is not a dictionary, keep it as is
                    processed_items[item_id] = item
            
            # Replace the original items with processed items
            order_data['items'] = processed_items
        
        return jsonify({'success': True, 'order': order_data})
    except Exception as e:
        print(f"Error fetching order details: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/order-details/<order_id>', methods=['GET'])
def get_order_details(order_id):
    """Get detailed order information from Firebase"""
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        # Fetch the specific order from Firebase
        db = firebase_admin.db.reference()
        order_ref = db.child('orders').child(order_id)
        order_data = order_ref.get()
        
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Add the order_id to the data for display purposes
        order_data['order_id'] = order_id
        
        # Look up customer information if user_id is available
        if 'user_id' in order_data:
            user_ref = db.child('users').child(order_data['user_id'])
            user_info = user_ref.get()
            if user_info:
                order_data['customerName'] = user_info.get('name', 'Customer')
                order_data['customerPhone'] = user_info.get('phone', 'N/A')
                order_data['customerAddress'] = user_info.get('address', 'N/A')
                order_data['customerEmail'] = user_info.get('email', 'N/A')
        # Ensure timestamp is available
        if not order_data.get('timestamp'):
            order_data['timestamp'] = order_data.get('created_at') or order_data.get('order_date')
        
        return jsonify({'success': True, 'order': order_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/approve-order/<order_id>', methods=['POST'])
@admin_required
def approve_order(order_id):
    """Approve an order and update its status in the database"""
    try:
        # Update the order status in Firebase
        order_ref = db.reference(f'orders/{order_id}')
        order_data = order_ref.get()
        
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Update both status fields for maximum compatibility
        order_ref.update({
            'status': 'approved',
            'payment_status': 'paid'
        })
        
        return jsonify({
            'success': True,
            'message': 'Order approved successfully'
        })
    except Exception as e:
        print(f"Error approving order: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/reject-order/<order_id>', methods=['POST'])
@admin_required
def reject_order(order_id):
    """Reject an order and update its status in the database"""
    try:
        # Update the order status in Firebase
        order_ref = db.reference(f'orders/{order_id}')
        order_data = order_ref.get()
        
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Update both status fields for maximum compatibility
        order_ref.update({
            'status': 'cancelled',
            'payment_status': 'cancelled'
        })
        
        return jsonify({
            'success': True,
            'message': 'Order rejected successfully'
        })
    except Exception as e:
        print(f"Error rejecting order: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
# Admin Profile Page
@app.route('/admin/profile')
@admin_required
def admin_profile():
    # Get admin data from database
    user_id = session.get('user_id')
    admin_ref = db.reference(f'users/{user_id}')
    admin_data = admin_ref.get() or {}

    # Also get user_data for navbar avatar
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    return render_template('admin_profile.html', admin_data=admin_data, user_data=user_data)

# API route to update admin profile
@app.route('/api/admin/<user_id>/profile', methods=['POST'])
@admin_required
def update_admin_profile(user_id):
    try:
        # First get the existing user data to preserve all fields
        user_ref = db.reference('users').child(user_id)
        existing_user_data = user_ref.get() or {}
        
        # Create updates object, preserving existing data
        updates = existing_user_data.copy()
        
        # Get form data and update only if provided
        if 'name' in request.form and request.form['name']:
            updates['name'] = request.form['name']
        if 'email' in request.form and request.form['email']:
            updates['email'] = request.form['email']
        if 'phone' in request.form and request.form['phone']:
            updates['phone'] = request.form['phone']
        
        # Handle profile picture upload if present
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Create a secure filename
                filename = secure_filename(file.filename)
                # Create unique filename with timestamp
                unique_filename = f"{user_id}_{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                # Save the file
                file.save(file_path)
                # Update the profile picture path
                updates['profile_picture'] = f"/static/uploads/{unique_filename}"
        
        # Update the user data in the database
        user_ref.set(updates)  # Use set instead of update to ensure complete data update
        
        # Return updated profile data for UI refresh
        return jsonify({
            'success': True, 
            'data': {
                'profile_picture': updates.get('profile_picture', '/static/uploads/default_user.png')
            }
        })
    except Exception as e:
        app.logger.error(f"Error updating admin profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# User Complaint Submission Form
@app.route('/complaint')
def complaint():
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
    
    # Get user data
    user_id = session.get('user_id')
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    return render_template('complaint.html', user_data=user_data)

# Submit complaint
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user_id' not in session:
        flash('Please sign in to submit a complaint.', 'error')
        return redirect(url_for('signin'))
    
    try:
        # Get form data
        order_number = request.form.get('orderNumber', '')
        user_email = request.form.get('userEmail', '')
        complaint_type = request.form.get('complaintType', '')
        description = request.form.get('description', '')
        
        # Validate required fields
        if not complaint_type or not description:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('complaint'))
        
        # Generate a unique ID for the complaint
        complaint_id = f"COMP-{uuid.uuid4().hex[:8]}"
        
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Get user ID from session
        user_id = session.get('user_id')
        
        # Process uploaded images
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    # Create a secure filename
                    filename = secure_filename(file.filename)
                    # Create unique filename with timestamp
                    unique_filename = f"complaint_{complaint_id}_{len(images)}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    # Save the file
                    file.save(file_path)
                    # Add the file path to images list
                    images.append(f"/static/uploads/{unique_filename}")
        
        # Create complaint object
        complaint_data = {
            'id': complaint_id,
            'date': timestamp,
            'order_number': order_number,
            'user_email': user_email,
            'complaint_type': complaint_type,
            'description': description,
            'status': 'pending',
            'user_id': user_id,
            'images': images
        }
        
        # Save complaint to database
        complaints_ref = db.reference('complaints')
        complaints_ref.child(complaint_id).set(complaint_data)
        
        # Also save to user's complaints list
        user_complaints_ref = db.reference(f'users/{user_id}/complaints')
        user_complaints_ref.child(complaint_id).set(True)
        
        # Send email notifications
        send_complaint_emails(complaint_data)
        
        flash('Your complaint has been submitted successfully. We will review it shortly.', 'success')
        return redirect(url_for('complaint_history', from_submission='true'))
        
    except Exception as e:
        app.logger.error(f"Error submitting complaint: {str(e)}")
        flash(f'Error submitting complaint: {str(e)}', 'error')
        return redirect(url_for('complaint'))

# Helper function to send complaint emails
def send_complaint_emails(complaint_data):
    try:
        # Get email configuration
        email_host = EMAIL_HOST
        email_port = EMAIL_PORT
        email_user = EMAIL_USER
        email_password = EMAIL_PASSWORD
        admin_email = NOTIFICATION_EMAIL
        
        # Create admin notification email
        admin_subject = f"New Complaint: {complaint_data['id']}"
        admin_html = f"""
        <html>
        <body>
            <h1>New Complaint Received</h1>
            <p><strong>ID:</strong> {complaint_data['id']}</p>
            <p><strong>Date:</strong> {datetime.fromisoformat(complaint_data['date']).strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Order Number:</strong> {complaint_data['order_number'] or 'N/A'}</p>
            <p><strong>Customer Email:</strong> {complaint_data['user_email']}</p>
            <p><strong>Type:</strong> {complaint_data['complaint_type']}</p>
            <p><strong>Description:</strong> {complaint_data['description']}</p>
            <p><a href="{url_for('admin_complaints', _external=True)}">View in Admin Dashboard</a></p>
        </body>
        </html>
        """
        
        # Create customer confirmation email
        customer_subject = f"Your Complaint Has Been Received: {complaint_data['id']}"
        customer_html = f"""
        <html>
        <body>
            <h1>Your Complaint Has Been Received</h1>
            <p>Thank you for submitting a complaint. We will review it shortly.</p>
            <p><strong>Complaint ID:</strong> {complaint_data['id']}</p>
            <p><strong>Date:</strong> {datetime.fromisoformat(complaint_data['date']).strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Order Number:</strong> {complaint_data['order_number'] or 'N/A'}</p>
            <p><strong>Type:</strong> {complaint_data['complaint_type']}</p>
            <p><strong>Description:</strong> {complaint_data['description']}</p>
            <p>Please keep your complaint ID for reference. We will update you on the status of your complaint.</p>
            <p>If you have any questions, please contact our support team.</p>
            </body>
        </html>
        """
        
        # Send admin email
        admin_msg = MIMEMultipart('alternative')
        admin_msg['Subject'] = admin_subject
        admin_msg['From'] = email_user
        admin_msg['To'] = admin_email
        admin_msg.attach(MIMEText(admin_html, 'html'))
        
        # Send customer email if email is provided
        if complaint_data['user_email']:
            customer_msg = MIMEMultipart('alternative')
            customer_msg['Subject'] = customer_subject
            customer_msg['From'] = email_user
            customer_msg['To'] = complaint_data['user_email']
            customer_msg.attach(MIMEText(customer_html, 'html'))
        
        # Connect to SMTP server and send emails
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            
            # Send admin email
            server.send_message(admin_msg)
            
            # Send customer email if email is provided
            if complaint_data['user_email']:
                server.send_message(customer_msg)
        
        app.logger.info(f"Complaint notification emails sent for {complaint_data['id']}")
        return True
    except Exception as e:
        app.logger.error(f"Error sending complaint emails: {str(e)}")
        return False

# User Complaint History
@app.route('/complaint/history')
def complaint_history():
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
    
    # Get user data
    user_id = session.get('user_id')
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    # Get user's complaints
    user_complaints = []
    user_complaints_ref = db.reference(f'users/{user_id}/complaints')
    user_complaints_ids = user_complaints_ref.get() or {}
    
    if user_complaints_ids:
        complaints_ref = db.reference('complaints')
        for complaint_id in user_complaints_ids:
            complaint = complaints_ref.child(complaint_id).get()
            if complaint:
                # Format date for display
                complaint_date = datetime.fromisoformat(complaint['date'])
                complaint['date'] = complaint_date.strftime('%Y-%m-%d %H:%M:%S')
                
                # Get type display name
                type_map = {
                    'product': 'Food Issue',
                    'service': 'Customer Service',
                    'billing': 'Billing Issue',
                    'website': 'Website Problem',
                    'other': 'Other'
                }
                complaint['type_display'] = type_map.get(complaint['complaint_type'], complaint['complaint_type'])
                
                user_complaints.append(complaint)
    
    # Sort complaints by date (newest first)
    user_complaints.sort(key=lambda x: x['date'], reverse=True)
    
    # Check if coming from submission
    from_submission = request.args.get('from_submission') == 'true'
    
    return render_template('complaint_history.html', 
                          user_data=user_data, 
                          complaints=user_complaints, 
                          from_submission=from_submission)

# Complaint Detail Page
@app.route('/complaint/<complaint_id>')
def complaint_detail(complaint_id):
    if 'user_id' not in session:
        flash('Please sign in to access this page.', 'error')
        return redirect(url_for('signin'))
    
    # Get user data
    user_id = session.get('user_id')
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    # Get complaint data
    complaints_ref = db.reference('complaints')
    complaint = complaints_ref.child(complaint_id).get()
    
    if not complaint:
        flash('Complaint not found.', 'error')
        return redirect(url_for('complaint_history'))
    
    # Check if complaint belongs to user
    if complaint.get('user_id') != user_id:
        flash('You do not have permission to view this complaint.', 'error')
        return redirect(url_for('complaint_history'))
    
    # Format date for display
    complaint_date = datetime.fromisoformat(complaint['date'])
    complaint['date'] = complaint_date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get type display name
    type_map = {
        'product': 'Food Issue',
        'service': 'Customer Service',
        'billing': 'Billing Issue',
        'website': 'Website Problem',
        'other': 'Other'
    }
    complaint['type_display'] = type_map.get(complaint['complaint_type'], complaint['complaint_type'])
    
    return render_template('complaint_detail.html', user_data=user_data, complaint=complaint)

# Admin Complaints Dashboard
@app.route('/admin/complaints')
@admin_required
def admin_complaints():
    # Get all complaints
    complaints_ref = db.reference('complaints')
    all_complaints = complaints_ref.get() or {}
    
    # Convert to list and sort by date (newest first)
    complaints = []
    for complaint_id, complaint in all_complaints.items():
        complaints.append(complaint)
    
    complaints.sort(key=lambda x: x['date'], reverse=True)
    
    # Format dates and add type display names
    for complaint in complaints:
        # Format date for display
        complaint_date = datetime.fromisoformat(complaint['date'])
        complaint['date'] = complaint_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get type display name
        type_map = {
            'product': 'Food Issue',
            'service': 'Customer Service',
            'billing': 'Billing Issue',
            'website': 'Website Problem',
            'other': 'Other'
        }
        # Use get() with a default value if the key doesn't exist
        complaint_type = complaint.get('complaint_type', 'other')
        complaint['type_display'] = type_map.get(complaint_type, 'Other')
    
    # Get user data for avatar
    user_id = session.get('user_id')
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get() or {}
    
    return render_template('admin_complaints.html', complaints=complaints, user_data=user_data)
# API route to get filtered complaints
@app.route('/api/admin/complaints')
@admin_required
def get_admin_complaints():
    # Get filter parameters
    status = request.args.get('status', 'all')
    complaint_type = request.args.get('type', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '').lower()
    
    # Get all complaints
    complaints_ref = db.reference('complaints')
    all_complaints = complaints_ref.get() or {}
    
    # Convert to list
    complaints = []
    for complaint_id, complaint in all_complaints.items():
        complaints.append(complaint)
    
    # Apply filters
    filtered_complaints = []
    for complaint in complaints:
        # Status filter
        if status != 'all' and complaint['status'] != status:
            continue
        
        # Type filter
        if complaint_type != 'all' and complaint['complaint_type'] != complaint_type:
            continue
        
        # Date range filter
        complaint_date = datetime.fromisoformat(complaint['date'])
        
        if date_from:
            from_date = datetime.fromisoformat(date_from)
            if complaint_date < from_date:
                continue
        
        if date_to:
            to_date = datetime.fromisoformat(date_to)
            # Set time to end of day
            to_date = to_date.replace(hour=23, minute=59, second=59)
            if complaint_date > to_date:
                continue
        
        # Search filter
        if search:
            # Search in ID, email, order number, and description
            search_fields = [
                complaint['id'].lower(),
                complaint['user_email'].lower(),
                complaint.get('order_number', '').lower(),
                complaint['description'].lower()
            ]
            
            if not any(search in field for field in search_fields):
                continue
        
        filtered_complaints.append(complaint)
    
    # Sort by date (newest first)
    filtered_complaints.sort(key=lambda x: x['date'], reverse=True)
    
    return jsonify(filtered_complaints)

# API route to update complaint status
@app.route('/api/admin/complaints/<complaint_id>/status', methods=['PUT'])
@admin_required
def update_complaint_status(complaint_id):
    try:
        data = request.json
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        # Validate status
        if new_status not in ['pending', 'resolved', 'rejected']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        # Update complaint status
        complaint_ref = db.reference(f'complaints/{complaint_id}')
        complaint = complaint_ref.get()
        
        if not complaint:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Update status
        complaint_ref.update({'status': new_status})
        
        # If status changed to resolved or rejected, send email notification
        if new_status in ['resolved', 'rejected'] and complaint.get('status') != new_status:
            send_status_update_email(complaint, new_status)
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating complaint status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API route to add response to complaint
@app.route('/api/admin/complaints/<complaint_id>/response', methods=['POST'])
@admin_required
def add_complaint_response(complaint_id):
    try:
        data = request.json
        response = data.get('response')
        
        if not response:
            return jsonify({'success': False, 'message': 'Response is required'}), 400
        
        # Update complaint with response
        complaint_ref = db.reference(f'complaints/{complaint_id}')
        complaint = complaint_ref.get()
        
        if not complaint:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Update response and status
        complaint_ref.update({
            'response': response,
            'status': 'resolved',
            'response_date': datetime.now().isoformat(),
            'responded_by': session.get('user_id')
        })
        
        # Send email notification
        send_response_email(complaint, response)
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error adding complaint response: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API route to delete complaint
@app.route('/api/admin/complaints/<complaint_id>', methods=['DELETE'])
@admin_required
def delete_complaint(complaint_id):
    try:
        # Get complaint data
        complaint_ref = db.reference(f'complaints/{complaint_id}')
        complaint = complaint_ref.get()
        
        if not complaint:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Delete complaint images if any
        if 'images' in complaint and complaint['images']:
            for image_path in complaint['images']:
                # Remove /static/ prefix to get the relative path
                relative_path = image_path.replace('/static/', '')
                file_path = os.path.join(app.static_folder, relative_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Delete complaint from database
        complaint_ref.delete()
        
        # Delete from user's complaints list
        if 'user_id' in complaint:
            user_complaints_ref = db.reference(f'users/{complaint["user_id"]}/complaints/{complaint_id}')
            user_complaints_ref.delete()
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error deleting complaint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API route to export complaints
@app.route('/api/admin/complaints/export')
@admin_required
def export_complaints():
    try:
        # Get all complaints
        complaints_ref = db.reference('complaints')
        all_complaints = complaints_ref.get() or {}
        
        # Convert to list
        complaints = []
        for complaint_id, complaint in all_complaints.items():
            complaints.append(complaint)
        
        # Sort by date (newest first)
        complaints.sort(key=lambda x: x['date'], reverse=True)
        
        # Create CSV file
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Date', 'Order Number', 'Email', 'Type', 'Description', 'Status', 'Response'])
        
        # Write data
        for complaint in complaints:
            writer.writerow([
                complaint['id'],
                complaint['date'],
                complaint.get('order_number', ''),
                complaint['user_email'],
                complaint['complaint_type'],
                complaint['description'],
                complaint['status'],
                complaint.get('response', '')
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=complaints.csv'
        response.headers['Content-type'] = 'text/csv'
        
        return response
    except Exception as e:
        app.logger.error(f"Error exporting complaints: {str(e)}")
        flash(f'Error exporting complaints: {str(e)}', 'error')
        return redirect(url_for('admin_complaints'))

# Helper function to send status update email
def send_status_update_email(complaint, new_status):
    try:
        # Get email configuration
        email_host = EMAIL_HOST
        email_port = EMAIL_PORT
        email_user = EMAIL_USER
        email_password = EMAIL_PASSWORD
        
        # Only send if user email is provided
        if not complaint.get('user_email'):
            return False
        
        # Create email
        subject = f"Complaint Status Update: {complaint['id']}"
        
        # Create email body based on status
        if new_status == 'resolved':
            body = f"""
            <html>
            <body>
                <h1>Your Complaint Has Been Resolved</h1>
                <p>We're pleased to inform you that your complaint has been resolved.</p>
                <p><strong>Complaint ID:</strong> {complaint['id']}</p>
                <p><strong>Status:</strong> Resolved</p>
                <p>If you have any further questions, please don't hesitate to contact us.</p>
                <p>Thank you for your patience.</p>
            </body>
            </html>
            """
        else:  # rejected
            body = f"""
            <html>
            <body>
                <h1>Update on Your Complaint</h1>
                <p>We've reviewed your complaint and unfortunately, we are unable to proceed further with it at this time.</p>
                <p><strong>Complaint ID:</strong> {complaint['id']}</p>
                <p><strong>Status:</strong> Closed</p>
                <p>If you have any questions or would like to discuss this further, please contact our customer service team.</p>
            </body>
            </html>
            """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = complaint['user_email']
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        app.logger.info(f"Status update email sent for complaint {complaint['id']}")
        return True
    except Exception as e:
        app.logger.error(f"Error sending status update email: {str(e)}")
        return False

# Helper function to send response email
def send_response_email(complaint, response):
    try:
        # Get email configuration
        email_host = EMAIL_HOST
        email_port = EMAIL_PORT
        email_user = EMAIL_USER
        email_password = EMAIL_PASSWORD
        
        # Only send if user email is provided
        if not complaint.get('user_email'):
            return False
        
        # Create email
        subject = f"Response to Your Complaint: {complaint['id']}"
        body = f"""
        <html>
        <body>
            <h1>Response to Your Complaint</h1>
            <p>We've reviewed your complaint and have the following response:</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #4f46e5; margin: 15px 0;">
                <p>{response}</p>
            </div>
            <p><strong>Complaint ID:</strong> {complaint['id']}</p>
            <p><strong>Status:</strong> Resolved</p>
            <p>If you have any further questions, please don't hesitate to contact us.</p>
            <p>Thank you for your patience.</p>
        </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = complaint['user_email']
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        app.logger.info(f"Response email sent for complaint {complaint['id']}")
        return True
    except Exception as e:
        app.logger.error(f"Error sending response email: {str(e)}")
        return False

# Add this function to ensure discounts are properly calculated and displayed
def get_server_side_props(order_id):
    try:
        # Fetch order details
        order_ref = db.reference(f'orders/{order_id}')
        order = order_ref.get()

        if not order:
            return {
                "notFound": True,
            }

        # Process items to ensure discounts are correctly applied
        if order.get('items'):
            total_amount = 0
            processed_items = []

            for item_id, item in order['items'].items():
                if isinstance(item, dict):
                    # Get the menu date this item was ordered from
                    menu_date = item.get('menu_date', datetime.now().strftime('%Y%m%d'))
                    
                    # Get the published menu for that date to check for discount
                    published_menu_ref = db.reference(f'published_menus/{menu_date}')
                    published_menu = published_menu_ref.get()
                    
                    if published_menu and 'items' in published_menu and item_id in published_menu['items']:
                        published_item = published_menu['items'][item_id]
                        original_price = published_item.get('price', item.get('price', 0))
                        discount = published_item.get('discount', 0)
                    else:
                        # Fallback to the item's own data
                        original_price = item.get('price', 0)
                        discount = item.get('discount', 0)

                    # Calculate discounted price
                    discounted_price = original_price
                    if discount > 0:
                        discounted_price = original_price - (original_price * discount / 100)

                    quantity = item.get('quantity', 1)
                    item_total = discounted_price * quantity
                    total_amount += item_total

                    processed_items.append([
                        item_id,
                        {
                            "name": item.get('name', "Unknown Item"),
                            "price": discounted_price,
                            "original_price": original_price,
                            "discount": discount,
                            "quantity": quantity,
                            "image_url": item.get('image_url', ""),
                        },
                    ])

            # Update the order with processed items and correct total
            order['order_items'] = processed_items

            # Update the order amount if it doesn't match calculated total
            if abs(order.get('amount', 0) - total_amount) > 0.01:
                order_ref.update({"amount": total_amount})
                order['amount'] = total_amount

        return {
            "props": {
                "order": order,
                "order_id": order_id,
            },
        }
    except Exception as e:
        print(f"Error fetching order: {str(e)}")
        return {
            "props": {
                "error": str(e),
            },
        }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
