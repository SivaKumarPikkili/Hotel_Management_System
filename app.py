from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import re
import uuid
import secrets
from dotenv import load_dotenv

# Google Calendar API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os.path

# 🔥 GEMINI AI imports (NOT OpenAI)
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

# Use environment variable for secret key or generate one
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Database configuration for different environments
if os.environ.get('DATABASE_URL'):
    # Production (PostgreSQL)
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'workplc666@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'jets glvk phho kyyp')

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
mail = Mail(app)

# 🔥 Configure Gemini AI (NOT OpenAI)
try:
    genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel("gemini-2.5-pro")
except Exception as e:
    print(f"Gemini AI configuration error: {e}")
    gemini_model = None

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    food_orders = db.relationship('FoodOrder', backref='user', lazy=True)

class RoomType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rooms = db.relationship('Room', backref='room_type', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='room', lazy=True)
    images = db.relationship('RoomImage', backref='room', lazy=True, cascade='all, delete-orphan')

class RoomImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    special_requests = db.Column(db.Text, default='')
    is_approved = db.Column(db.Boolean, default=False)

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # breakfast, lunch, dinner, snacks
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FoodOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, preparing, delivered
    special_instructions = db.Column(db.Text, default='')
    food_item = db.relationship('FoodItem', backref='orders')

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CustomerLoyalty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loyalty_level = db.Column(db.String(20), default='bronze')  # bronze, silver, gold, platinum
    total_bookings = db.Column(db.Integer, default=0)
    discount_percentage = db.Column(db.Float, default=0.0)

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return f"uploads/{unique_filename}"
    return None

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

def send_email(to, subject, body):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def get_room_availability(room_id, start_date, end_date):
    """Check if a room is available for the given date range"""
    conflicting_bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status.in_(['confirmed', 'pending']),
        db.or_(
            db.and_(Booking.check_in <= start_date, Booking.check_out > start_date),
            db.and_(Booking.check_in < end_date, Booking.check_out >= end_date),
            db.and_(Booking.check_in >= start_date, Booking.check_out <= end_date)
        )
    ).first()
    return conflicting_bookings is None

def update_customer_loyalty(user_id):
    """Update customer loyalty level based on booking history"""
    loyalty = CustomerLoyalty.query.filter_by(user_id=user_id).first()
    if not loyalty:
        loyalty = CustomerLoyalty(user_id=user_id)
        db.session.add(loyalty)
    
    loyalty.total_bookings += 1
    
    # Set loyalty level and discount
    if loyalty.total_bookings >= 10:
        loyalty.loyalty_level = 'platinum'
        loyalty.discount_percentage = 15.0
    elif loyalty.total_bookings >= 5:
        loyalty.loyalty_level = 'gold'
        loyalty.discount_percentage = 10.0
    elif loyalty.total_bookings >= 2:
        loyalty.loyalty_level = 'silver'
        loyalty.discount_percentage = 5.0
    
    db.session.commit()

# 🚀 DATABASE INITIALIZATION FUNCTION
def initialize_database():
    """Initialize database with tables and sample data"""
    try:
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Create admin user if not exists
        admin_email = "admin@hotel.com"
        if not User.query.filter_by(email=admin_email).first():
            admin_user = User(
                username="admin",
                email=admin_email,
                password_hash=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(admin_user)
            print("✅ Admin user created!")
        
        # Add sample room types if not exists
        if not RoomType.query.first():
            room_types_data = [
                {
                    'name': 'Deluxe Suite',
                    'description': 'Luxurious suite with city view, king-size bed, and premium amenities.',
                    'base_price': 200.0,
                    'capacity': 2,
                    'amenities': 'King Bed, City View, Mini Bar, Room Service, Free WiFi'
                },
                {
                    'name': 'Standard Room',
                    'description': 'Comfortable room with modern amenities, perfect for solo travelers or couples.',
                    'base_price': 100.0,
                    'capacity': 2,
                    'amenities': 'Queen Bed, TV, Free WiFi, Coffee Maker'
                },
                {
                    'name': 'Family Room',
                    'description': 'Spacious room perfect for families with multiple beds and extra space.',
                    'base_price': 150.0,
                    'capacity': 4,
                    'amenities': '2 Queen Beds, Extra Space, Kids Amenities, Free WiFi'
                },
                {
                    'name': 'Executive Suite',
                    'description': 'Premium suite with business amenities, separate living area, and work space.',
                    'base_price': 300.0,
                    'capacity': 2,
                    'amenities': 'King Bed, Living Area, Work Desk, Premium WiFi, Business Services'
                }
            ]
            
            for rt_data in room_types_data:
                room_type = RoomType(**rt_data)
                db.session.add(room_type)
            print("✅ Sample room types added!")
        
        # Add sample rooms if not exists
        if not Room.query.first():
            room_type_map = {rt.name: rt.id for rt in RoomType.query.all()}
            sample_rooms = [
                {'room_number': '101', 'type_name': 'Deluxe Suite'},
                {'room_number': '102', 'type_name': 'Deluxe Suite'},
                {'room_number': '201', 'type_name': 'Standard Room'},
                {'room_number': '202', 'type_name': 'Standard Room'},
                {'room_number': '203', 'type_name': 'Standard Room'},
                {'room_number': '301', 'type_name': 'Family Room'},
                {'room_number': '302', 'type_name': 'Family Room'},
                {'room_number': '401', 'type_name': 'Executive Suite'},
            ]
            
            for room_data in sample_rooms:
                if room_data['type_name'] in room_type_map:
                    room = Room(
                        room_number=room_data['room_number'],
                        room_type_id=room_type_map[room_data['type_name']]
                    )
                    db.session.add(room)
            print("✅ Sample rooms added!")
        
        # Add sample food items if not exists
        if not FoodItem.query.first():
            food_items = [
                FoodItem(name='Continental Breakfast', description='Fresh pastries, coffee, and juice', price=15.0, category='breakfast'),
                FoodItem(name='Full English Breakfast', description='Eggs, bacon, toast, and tea', price=20.0, category='breakfast'),
                FoodItem(name='Caesar Salad', description='Fresh romaine lettuce with Caesar dressing', price=12.0, category='lunch'),
                FoodItem(name='Grilled Chicken Sandwich', description='Grilled chicken with vegetables', price=18.0, category='lunch'),
                FoodItem(name='Beef Steak', description='Premium beef steak with sides', price=35.0, category='dinner'),
                FoodItem(name='Pasta Carbonara', description='Creamy pasta with bacon and cheese', price=22.0, category='dinner'),
                FoodItem(name='French Fries', description='Crispy golden fries', price=8.0, category='snacks'),
                FoodItem(name='Chocolate Cake', description='Rich chocolate cake with cream', price=10.0, category='snacks'),
            ]
            
            for food_item in food_items:
                db.session.add(food_item)
            print("✅ Sample food items added!")
        
        db.session.commit()
        print("✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        db.session.rollback()

# 🔥 INITIALIZE DATABASE ON APP STARTUP
@app.before_request
def setup_database():
    if not hasattr(app, 'initialized'):
        initialize_database()
        app.initialized = True


# Routes with error handling
@app.route('/')
def index():
    try:
        room_types = RoomType.query.all()
    except Exception as e:
        print(f"Database error in index route: {e}")
        # Try to initialize database if tables don't exist
        try:
            initialize_database()
            room_types = RoomType.query.all()
        except Exception as init_error:
            print(f"Failed to initialize database: {init_error}")
            room_types = []
    
    return render_template('index.html', room_types=room_types)

@app.route('/rooms')
def rooms():
    try:
        room_types = RoomType.query.all()
    except Exception as e:
        print(f"Database error in rooms route: {e}")
        room_types = []
    
    return render_template('rooms.html', room_types=room_types)

@app.route('/room_type/<int:type_id>')
def room_type_detail(type_id):
    room_type = db.session.get(RoomType, type_id)
    if not room_type:
        flash('Room type not found!')
        return redirect(url_for('rooms'))
    rooms = Room.query.filter_by(room_type_id=type_id).all()
    return render_template('room_type_detail.html', room_type=room_type, rooms=rooms)

@app.route('/check_availability/<int:room_id>')
def check_availability(room_id):
    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    bookings = Booking.query.filter_by(room_id=room_id, status='confirmed').all()
    booked_dates = []
    for booking in bookings:
        current_date = booking.check_in
        while current_date < booking.check_out:
            booked_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    return jsonify({
        'room_number': room.room_number,
        'room_type': room.room_type.name,
        'booked_dates': booked_dates
    })

@app.route('/gallery')
def gallery():
    # Dummy sample rooms for gallery display
    rooms = [
        {"name": "Deluxe Room", "description": "Spacious and luxurious", "capacity": 2, "price": 200, "room_type": {"name": "Deluxe"}},
        {"name": "Suite", "description": "For ultimate comfort", "capacity": 4, "price": 350, "room_type": {"name": "Suite"}},
        {"name": "Single Room", "description": "Ideal for solo travelers", "capacity": 1, "price": 120, "room_type": {"name": "Single"}},
        {"name": "Executive Suite", "description": "Perfect for business stays", "capacity": 3, "price": 300, "room_type": {"name": "Executive"}},
        {"name": "Family Room", "description": "Spacious and cozy", "capacity": 5, "price": 400, "room_type": {"name": "Family"}},
        {"name": "Penthouse", "description": "Top floor with city view", "capacity": 2, "price": 500, "room_type": {"name": "Penthouse"}},
    ]
    return render_template("gallery.html", rooms=rooms)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, subject, message]):
            flash('Please fill in all fields!')
            return redirect(url_for('contact'))

        contact_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(contact_msg)
        db.session.commit()

        flash('Your message has been sent! Thank you for contacting us.')
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long!')
            return redirect(url_for('register'))

        if not validate_email(email):
            flash('Please enter a valid email address!')
            return redirect(url_for('register'))

        if not validate_password(password):
            flash('Password must be at least 6 characters long!')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect(url_for('register'))

        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Please enter both username and password!')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login successful! Welcome back!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('index'))

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    if 'user_id' not in session:
        flash('Please login to book a room!')
        return redirect(url_for('login'))

    room = db.session.get(Room, room_id)
    if not room:
        flash('Room not found!')
        return redirect(url_for('rooms'))

    if request.method == 'POST':
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        special_requests = request.form.get('special_requests', '')

        if not check_in or not check_out:
            flash('Please select both check-in and check-out dates!')
            return redirect(url_for('book_room', room_id=room_id))

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format!')
            return redirect(url_for('book_room', room_id=room_id))

        # Validation
        if check_in_date >= check_out_date:
            flash('Check-out date must be after check-in date!')
            return redirect(url_for('book_room', room_id=room_id))

        if check_in_date < datetime.now().date():
            flash('Check-in date cannot be in the past!')
            return redirect(url_for('book_room', room_id=room_id))

        if not get_room_availability(room_id, check_in_date, check_out_date):
            flash('Room is not available for the selected dates!')
            return redirect(url_for('book_room', room_id=room_id))

        # Calculate total price
        days = (check_out_date - check_in_date).days
        total_price = room.room_type.base_price * days

        booking = Booking(
            user_id=session['user_id'],
            room_id=room_id,
            check_in=check_in_date,
            check_out=check_out_date,
            total_price=total_price,
            special_requests=special_requests
        )

        db.session.add(booking)
        db.session.commit()

        # Update customer loyalty
        update_customer_loyalty(session['user_id'])

        # Send emails
        user = db.session.get(User, session['user_id'])
        if user:
            send_email(
                user.email,
                'Booking Confirmation - Pending Approval',
                f'Your booking for Room {room.room_number} from {check_in_date} to {check_out_date} has been submitted and is pending admin approval.'
            )

        flash('Booking submitted successfully! Please wait for admin approval.')
        return redirect(url_for('my_bookings'))

    return render_template('book_room.html', room=room, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        flash('Please login to view your bookings!')
        return redirect(url_for('login'))

    bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.booking_date.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash('Please login to cancel bookings!')
        return redirect(url_for('login'))

    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash('Booking not found!')
        return redirect(url_for('my_bookings'))

    if booking.user_id != session['user_id'] and not session.get('is_admin'):
        flash('You can only cancel your own bookings!')
        return redirect(url_for('my_bookings'))

    if booking.status == 'cancelled':
        flash('This booking is already cancelled!')
        return redirect(url_for('my_bookings'))

    booking.status = 'cancelled'
    db.session.commit()

    flash('Booking cancelled successfully!')
    return redirect(url_for('my_bookings'))

@app.route('/food_menu/<int:booking_id>')
def food_menu(booking_id):
    if 'user_id' not in session:
        flash('Please login to access food menu!')
        return redirect(url_for('login'))

    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash('Booking not found!')
        return redirect(url_for('my_bookings'))

    if booking.user_id != session['user_id']:
        flash('Access denied!')
        return redirect(url_for('my_bookings'))

    if not booking.is_approved:
        flash('Food menu is only available for approved bookings!')
        return redirect(url_for('my_bookings'))

    food_items = FoodItem.query.filter_by(is_available=True).all()
    return render_template('food_menu.html', booking=booking, food_items=food_items)

@app.route('/order_food', methods=['POST'])
def order_food():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login to order food!'}), 401

    data = request.get_json()
    booking_id = data.get('booking_id')
    items = data.get('items', [])
    special_instructions = data.get('special_instructions', '')

    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != session['user_id'] or not booking.is_approved:
        return jsonify({'success': False, 'message': 'Invalid or unauthorized booking!'})

    for item in items:
        food_item = db.session.get(FoodItem, item['id'])
        if not food_item:
            continue

        try:
            quantity = int(item['quantity'])
            if quantity <= 0:
                continue
        except:
            continue

        total_price = food_item.price * quantity

        food_order = FoodOrder(
            user_id=session['user_id'],
            booking_id=booking_id,
            food_item_id=food_item.id,
            quantity=quantity,
            total_price=total_price,
            special_instructions=special_instructions
        )
        db.session.add(food_order)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Food order placed successfully!'})

# Admin routes
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied! Admin privileges required.')
        return redirect(url_for('index'))

    total_bookings = Booking.query.count()
    total_users = User.query.count()
    total_rooms = Room.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Booking.total_price)).filter_by(status='confirmed').scalar() or 0

    # Get monthly stats
    current_month = datetime.now().month
    monthly_bookings = Booking.query.filter(
        db.extract('month', Booking.booking_date) == current_month
    ).count()

    return render_template('admin/dashboard.html',
                          total_bookings=total_bookings,
                          total_users=total_users,
                          total_rooms=total_rooms,
                          pending_bookings=pending_bookings,
                          total_revenue=total_revenue,
                          monthly_bookings=monthly_bookings,
                          recent_bookings=recent_bookings)

# Add all your other admin routes here (room_types, rooms, bookings, users, food)
# I'll include a few key ones to keep the response manageable

@app.route('/admin/bookings')
def admin_bookings():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied!')
        return redirect(url_for('index'))

    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/<int:booking_id>/<action>')
def admin_booking_action(booking_id, action):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied!')
        return redirect(url_for('index'))

    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash('Booking not found!')
        return redirect(url_for('admin_bookings'))

    if action == 'approve':
        booking.status = 'confirmed'
        booking.is_approved = True
        flash('Booking approved!')

        # Send confirmation email to user
        user = db.session.get(User, booking.user_id)
        if user:
            send_email(
                user.email,
                'Booking Confirmed!',
                f'Your booking for Room {booking.room.room_number} from {booking.check_in} to {booking.check_out} has been confirmed!'
            )

    elif action == 'cancel':
        booking.status = 'cancelled'
        flash('Booking cancelled!')
    elif action == 'complete':
        booking.status = 'completed'
        flash('Booking marked as completed!')

    db.session.commit()
    return redirect(url_for('admin_bookings'))

# 🔥 GEMINI AI Chatbot Route
@app.route('/api/chat', methods=['POST'])
def api_chat():
    if not gemini_model:
        return jsonify({'success': False, 'error': 'AI service not available'}), 500
    
    data = request.get_json() or {}
    user_text = (data.get('message') or '').strip()

    if not user_text:
        return jsonify({'success': False, 'error': 'Empty message'}), 400

    # Optional: include session context (username or booking hints)
    username = session.get('username')
    context_prefix = f"User: {username}. " if username else ""

    # 🔥 Call GEMINI AI (NOT OpenAI)
    try:
        # Start chat session with Gemini
        chat = gemini_model.start_chat(history=[])
        
        # Send message with context
        prompt = f"{context_prefix}You are a helpful hotel assistant. Answer briefly and clearly. Message: {user_text}"
        response = chat.send_message(prompt)

        # Extract text from Gemini response
        text = response.text if response.text else "Sorry, I couldn't generate a response."

        return jsonify({'success': True, 'reply': text})

    except Exception as e:
        print("Gemini AI error:", e)
        return jsonify({'success': False, 'error': 'AI service error'}), 500

# 🔥 PRODUCTION-READY APP STARTUP
if __name__ == '__main__':
    # For production deployment (Render.com, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Initialize database in application context
    with app.app_context():
        initialize_database()
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
else:
    # For production servers (gunicorn, etc.)
    with app.app_context():
        initialize_database()
