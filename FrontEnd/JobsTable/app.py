from flask import Flask, render_template, request, redirect, url_for, flash, abort
from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask_mail import Mail, Message
from models import db, Job, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'EDUMATCHWEBAPP'  # Change this to a secure secret key

# Flask-Mail configuration for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nkosingiphilebhekithemba@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'mrkj vyyo lyws ubqd'  # Your Gmail password

# Initialize Flask-Mail
mail = Mail(app)

# Initialize URLSafeTimedSerializer with a secret key
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Initialize SQLAlchemy
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    jobs = Job.query.all()
    return render_template('index.html', jobs=jobs)

@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    job = Job.query.get(job_id)

    if not job:
        abort(404)  # Handle job not found

    db.session.delete(job)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
def update_job(job_id):
    job = Job.query.get(job_id)

    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.requirements = request.form['requirements']
        job.hours = request.form['hours']

        db.session.commit()

        return redirect(url_for('index'))

    return render_template('update_job.html', job=job)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        requirements = request.form['requirements']
        hours = request.form['hours']

        new_job = Job(title=title, description=description, requirements=requirements, hours=hours)

        db.session.add(new_job)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('post_job.html')

# Define the route for signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        username = request.form['email']  # Use email as username
        email = request.form['email']
        student_number = request.form['student_number']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate form data
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", 'error')
            return redirect(url_for('signup'))

        # Check if the username or email already exists in the database
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or email already exists. Please choose a different one.", 'error')
            return redirect(url_for('signup'))

        # Create a new user instance and save it to the database
        new_user = User(username=username, email=email, student_number=student_number,
                        first_name=first_name, last_name=last_name)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please log in.", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Define the route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Find user by username in the database
        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Implement login logic, e.g., session management
            flash("Login successful!", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password. Please try again.", 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Define the route for forgot password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a token for password reset
            token = serializer.dumps(email, salt='password-reset')

            # Send the password reset link to the user via email
            reset_link = url_for('reset_password', token=token, _external=True)

            # Send email
            msg = Message(subject="Password Reset Request",
                          recipients=[email],
                          body=f"Hi {user.username},\n\n"
                               f"Please follow this link to reset your password: {reset_link}\n\n"
                               f"If you didn't request this, please ignore this email.",
                          sender="mlungisimnembe075@gmail.com")  # Change this to your email address
            mail.send(msg)

            flash("Password reset link has been sent to your email.", 'success')
            return redirect(url_for('login'))
        else:
            flash("Email address not found. Please try again.", 'error')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

# Define the route for password reset with token
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Decrypt the token to get the email address
        email = serializer.loads(token, salt='password-reset', max_age=3600)  # Token expires after 1 hour
    except BadSignature:
        flash("Invalid or expired token.", 'error')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()

    if request.method == 'POST':
        # Update the user's password
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", 'error')
            return redirect(url_for('reset_password', token=token))

        user.set_password(password)
        db.session.commit()

        flash("Password reset successful! Please log in with your new password.", 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(debug=True)

