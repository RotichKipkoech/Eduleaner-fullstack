# Existing imports
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from forms import LoginForm, CreateStudentForm, CreateTeacherForm, CreateFinanceForm
from models import db, User, Student, Teacher, Finance, Assignment, Remark, Attendance, Fee, Mark, PasswordResetRequest

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduleaner.db'  # Update if necessary
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Check for Admin credentials
        if form.username.data == "Admin" and form.password.data == "Admin@123":
            admin_user = User.query.filter_by(username="Admin").first()
            if not admin_user:
                # Create Admin user if it does not exist. Admin username and password are already set.
                admin_user = User(username="Admin", password=generate_password_hash("Admin@123"), role='Admin')
                db.session.add(admin_user)
                db.session.commit()
            
            login_user(admin_user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        # Normal user login
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to user dashboard

        flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect users based on role
    if current_user.role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'Teacher':
        return redirect(url_for('teacher_dashboard'))
    elif current_user.role == 'Student':
        return redirect(url_for('student_dashboard'))
    elif current_user.role == 'Finance':
        return redirect(url_for('finance_dashboard'))
    return render_template('dashboard.html')

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()  # Fetch all users to display
    reset_requests = PasswordResetRequest.query.all()  # Fetch password reset requests
    return render_template('admin_dashboard.html', users=users, reset_requests=reset_requests)

from werkzeug.security import generate_password_hash

@app.route('/create_student', methods=['GET', 'POST'])
@login_required
def create_student():
    if current_user.role != 'Admin':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    form = CreateStudentForm()
    if form.validate_on_submit():
        # Generate admission number for the student
        admission_number = Student.generate_admission_number()

        # Create the User object with 'Student' role
        user = User(username=form.username.data, 
                    password=generate_password_hash(form.password.data), 
                    role='Student')
        db.session.add(user)
        db.session.commit()  # Commit to generate the user.id

        # Create the Student object and associate it with the created user
        student = Student(
            user_id=user.id,
            admission_number=admission_number,
            course_name=form.course_name.data  # This should match the model's field
        )
        db.session.add(student)
        db.session.commit()

        flash('Student created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_student.html', form=form)


@app.route('/create_teacher', methods=['GET', 'POST'])
@login_required
def create_teacher():
    if current_user.role != 'Admin':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))
    form = CreateTeacherForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=generate_password_hash(form.password.data), role='Teacher')
        db.session.add(user)
        db.session.commit()
        teacher = Teacher(user_id=user.id, subject=form.subject.data)
        db.session.add(teacher)
        db.session.commit()
        flash('Teacher created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_teacher.html', form=form)


@app.route('/create_finance', methods=['GET', 'POST'])
@login_required
def create_finance():
    if current_user.role != 'Admin':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))
    form = CreateFinanceForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=generate_password_hash(form.password.data), role='Finance')
        db.session.add(user)
        db.session.commit()
        finance = Finance(user_id=user.id)
        db.session.add(finance)
        db.session.commit()
        flash('Finance account created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_finance.html', form=form)

# Teacher Dashboard Route
@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'Teacher':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))
    
    # Fetch assignments for the logged-in teacher
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()

    # Fetch all students and their associated marks
    students = Student.query.all()
    student_performance = []

    for student in students:
        # Calculate average score for each student
        marks = Mark.query.filter_by(student_id=student.id).all()
        if marks:
            average_score = sum(mark.score for mark in marks) / len(marks)
        else:
            average_score = 0

        student_performance.append({
            'student': student,
            'average_score': average_score
        })

    # Sort students by average score in descending order (highest first)
    student_performance.sort(key=lambda x: x['average_score'], reverse=True)

    return render_template('teacher_dashboard.html', assignments=assignments, student_performance=student_performance)



@app.route('/create_assignment', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')  # Expecting a string in 'YYYY-MM-DD' format
        teacher_id = current_user.id  # Assuming the current user is a teacher
        student_id = request.form.get('student_id')  # Get selected student ID from the form

        # Convert due_date_str to a date object
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()  # Convert to date object
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", 'danger')
            return redirect(url_for('create_assignment'))

        # Create the assignment instance
        new_assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            teacher_id=teacher_id,
            student_id=student_id  # Associate assignment with the selected student
        )

        try:
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('view_assignments'))  # Adjust redirection as needed
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
            return redirect(url_for('create_assignment'))

    # Fetching the list of students to display in the form
    students = Student.query.all()
    return render_template('create_assignment.html', students=students)

# Create fee
@app.route('/create_fee', methods=['POST'])
@login_required
def create_fee():
    if current_user.role != 'Finance':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    # Retrieve form data
    student_id = request.form.get('student_id', type=int)
    amount_due = request.form.get('amount_due', type=float)
    amount_paid = request.form.get('amount_paid', type=float)
    due_date_str = request.form.get('due_date')
    status = request.form.get('status')

    # Convert due_date_str to a date object
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", 'danger')
        return redirect(url_for('finance_dashboard'))

    # Create a new Fee instance
    new_fee = Fee(
        student_id=student_id,
        amount_due=amount_due,
        amount_paid=amount_paid,
        due_date=due_date,
        status=status
    )

    try:
        db.session.add(new_fee)
        db.session.commit()
        flash('New fee record created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while creating the fee record: {e}', 'danger')

    return redirect(url_for('finance_dashboard'))


# Add Remark Endpoint
@app.route('/add_remark', methods=['GET', 'POST'])
@login_required
def add_remark():
    if current_user.role != 'Teacher':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')  # Get student ID from the form
        text = request.form.get('text')  # Get remark text from the form

        # Check if the text is empty
        if not text:
            flash('Remark text cannot be empty.', 'danger')
            return redirect(url_for('add_remark'))  # Optionally redirect back to the form

        new_remark = Remark(student_id=student_id, teacher_id=current_user.id, text=text)
        db.session.add(new_remark)
        db.session.commit()
        flash('Remark added successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    students = Student.query.all()  # Load students for the form
    return render_template('add_remark.html', students=students)


# Mark Attendance Endpoint
@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if current_user.role != 'Teacher':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')  # Get student ID from the form
        status = request.form.get('status')  # Get attendance status (Present/Absent)

        new_attendance = Attendance(student_id=student_id, status=status)
        db.session.add(new_attendance)
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    students = Student.query.all()  # Load students for the form
    return render_template('mark_attendance.html', students=students)

# Student Dashbaord route
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    # Ensure the logged-in user is a Student
    if current_user.role != 'Student':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))  # Redirect if the user is not a student

    # Fetch the student associated with the current user (ensure correct student data)
    student = Student.query.filter_by(user_id=current_user.id).first()

    # If no student is associated with the user, flash a message and redirect
    if not student:
        flash('No student record found for this user.', 'info')
        return redirect(url_for('dashboard'))  # Redirect to a safer page if no student is found

    # Fetch assignments, remarks, marks, and fees related to the student
    assignments = Assignment.query.filter_by(student_id=student.id).all()
    remarks = Remark.query.filter_by(student_id=student.id).all()
    marks = Mark.query.filter_by(student_id=student.id).all()

    # Fetch fees directly from the Fee model by student_id
    fees = Fee.query.filter_by(student_id=student.id).all()

    # If no fees are found, show a message in the template
    if not fees:
        flash("No fee records found for this student.", "info")

    # Render the student dashboard template with the student data
    return render_template(
        'student_dashboard.html',
        student=student,  # Pass the student object
        assignments=assignments,  # Pass the assignments
        remarks=remarks,  # Pass the remarks
        fees=fees,  # Pass the fees
        marks=marks  # Pass the marks
    )


# View Assingment by student
@app.route('/view_assignments', methods=['GET'])
@login_required
def view_assignments():
    if current_user.role != 'Student':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))
    
    # Fetch assignments for the student (current_user is the student)
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("No student found for this user.", 'info')
        return redirect(url_for('dashboard'))

    assignments = Assignment.query.filter_by(student_id=student.id).all()

    return render_template('view_assignments.html', assignments=assignments)


# View Attendance by student
@app.route('/view_attendance')
@login_required
def view_attendance():
    if current_user.role != 'Student':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    # Fetch attendance records for the student
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("No student found for this user.", 'info')
        return redirect(url_for('dashboard'))

    attendance_records = Attendance.query.filter_by(student_id=student.id).all()

    return render_template('view_attendance.html', attendance_records=attendance_records)


# Add Marks
from flask import request, redirect, url_for, flash
from models import db, Mark  # Make sure you have the Mark model imported

@app.route('/add_mark', methods=['GET', 'POST'])
@login_required
def add_mark():
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject = request.form['subject']
        score = request.form['score']
        test_type = request.form['test_type']

        new_mark = Mark(student_id=student_id, teacher_id=current_user.id, subject=subject, score=score, test_type=test_type)
        db.session.add(new_mark)
        db.session.commit()
        flash('Marks added successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))  # Redirect back to the teacher dashboard

    students = Student.query.all()  # Fetch all students from the database
    return render_template('add_marks.html', students=students)





# Finance Dashboard Route
@app.route('/finance_dashboard')
@login_required
def finance_dashboard():
    if current_user.role != 'Finance':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    # Fetch all fee records and student list
    fees = Fee.query.all()
    students = Student.query.all()  # List of students for the creation form

    return render_template('finance_dashboard.html', fees=fees, students=students)


# View Fees Endpoint (For Finance)
@app.route('/view_fees')
@login_required
def view_fees():
    if current_user.role != 'Finance':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    fees = Fee.query.all()  # Get all fees
    return render_template('view_fees.html', fees=fees)

@app.route('/update_fee/<int:fee_id>', methods=['POST'])
@login_required
def update_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)  # Fetch the fee record by ID
    if current_user.role != 'Finance':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    try:
        amount_paid = request.form.get('amount_paid', type=float)
        due_date_str = request.form.get('due_date')
        status = request.form.get('status')

        # Convert due_date_str to a date object
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()  # Convert to date object

        # Update the fee details
        fee.amount_paid = amount_paid
        fee.due_date = due_date
        fee.status = status

        db.session.commit()
        flash('Fee updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating fee: {e}', 'danger')

    return redirect(url_for('finance_dashboard'))


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'Admin':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    
    # You can create a form similar to CreateUserForm for editing
    # For simplicity, let's just use basic form fields
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.role = request.form.get('role')  # Ensure to handle role correctly
        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_user.html', user=user)  # Create edit_user.html

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'Admin':
        flash("Unauthorized access.", 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


from flask import render_template
from flask_login import current_user, login_required

@app.route('/profile')
@login_required
def profile():
    # Use current_user to get the logged-in user's details
    return render_template('profile.html', user=current_user)

@app.route('/request_password_reset', methods=['POST'])
@login_required
def request_password_reset():
    reason = request.form.get('reason')  # Extract reason from form
    user_id = current_user.id  # Get the current user's ID

    reset_request = PasswordResetRequest(user_id=user_id, reason=reason)
    db.session.add(reset_request)
    db.session.commit()
    flash('Password reset request submitted!', 'success')
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
