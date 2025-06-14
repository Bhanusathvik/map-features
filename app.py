from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.secret_key = 'event_ease_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://BhanuSathvik:new_password@localhost/event_ease_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)

class Event(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_email = db.Column(db.String(100), db.ForeignKey('user.email'))
    user_name = db.Column(db.String(100))
    vendor_email = db.Column(db.String(100))
    vendor_name = db.Column(db.String(100))
    vendor_services = db.Column(db.String(200))
    vendor_phone = db.Column(db.String(20))
    venue_owner_email = db.Column(db.String(100))
    venue_owner_name = db.Column(db.String(100))
    venue_location_lat = db.Column(db.String(50))
    venue_location_lng = db.Column(db.String(50))
    venue_phone = db.Column(db.String(20))
    reminder_date = db.Column(db.String(100))

@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.')
            return redirect(url_for('register'))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Welcome back, {user.name}!')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password. Please try again.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    return render_template('home.html', 
                           user_name=session['user_name'], 
                           user_role=session['user_role'])

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_id = str(uuid.uuid4())
        title = request.form.get('title')
        description = request.form.get('description')
        vendor_email = request.form.get('vendor')
        venue_owner_email = request.form.get('venue_owner')
        vendor_services = request.form.get('vendor_services')
        vendor_phone = request.form.get('vendor_phone')
        venue_location_lat = request.form.get('venue_location_lat')
        venue_location_lng = request.form.get('venue_location_lng')
        venue_phone = request.form.get('venue_phone')
        reminder_date = request.form.get('reminder_date')

        vendor = User.query.filter_by(email=vendor_email).first()
        venue_owner = User.query.filter_by(email=venue_owner_email).first()

        new_event = Event(
            id=event_id,
            title=title,
            description=description,
            user_email=session['user_email'],
            user_name=session['user_name'],
            vendor_email=vendor_email,
            vendor_name=vendor.name if vendor else 'Unknown',
            venue_owner_email=venue_owner_email,
            venue_owner_name=venue_owner.name if venue_owner else 'Unknown',
            vendor_services=vendor_services,
            vendor_phone=vendor_phone,
            venue_location_lat=venue_location_lat,
            venue_location_lng=venue_location_lng,
            venue_phone=venue_phone,
            reminder_date=reminder_date
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Event created successfully!')
        return redirect(url_for('my_events'))

    vendors = User.query.filter_by(role='Vendor').all()
    venue_owners = User.query.filter_by(role='Venue Owner').all()
    return render_template('create_event.html', vendors=vendors, venue_owners=venue_owners)

@app.route('/my_events')
def my_events():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    events = Event.query.filter_by(user_email=session['user_email']).all()
    return render_template('my_events.html', events=events)

@app.route('/vendor_bookings')
def vendor_bookings():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if session['user_role'] != 'Vendor':
        flash('Only vendors can view vendor bookings.')
        return redirect(url_for('home'))

    events = Event.query.filter_by(vendor_email=session['user_email']).all()
    return render_template('vendor_bookings.html', events=events)

@app.route('/venue_bookings')
def venue_bookings():
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    if session['user_role'] != 'Venue Owner':
        flash('Only venue owners can view venue bookings.')
        return redirect(url_for('home'))

    events = Event.query.filter_by(venue_owner_email=session['user_email']).all()
    return render_template('venue_bookings.html', events=events)

@app.route('/event/<event_id>')
def view_event(event_id):
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    event = Event.query.filter_by(id=event_id).first()

    if not event:
        flash('Event not found.')
        return redirect(url_for('home'))

    user_email = session['user_email']
    if (user_email != event.user_email and 
        user_email != event.vendor_email and 
        user_email != event.venue_owner_email):
        flash('You do not have permission to view this event.')
        return redirect(url_for('home'))

    return render_template('view_event.html', event=event)

@app.route('/event/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    if 'user_email' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    event = Event.query.filter_by(id=event_id).first()

    if not event:
        flash('Event not found.')
        return redirect(url_for('home'))

    if session['user_email'] != event.user_email:
        flash('You do not have permission to delete this event.')
        return redirect(url_for('home'))

    db.session.delete(event)
    db.session.commit()

    flash('Event deleted successfully.')
    return redirect(url_for('my_events'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
