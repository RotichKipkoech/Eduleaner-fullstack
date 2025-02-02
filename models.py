from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# User model with roles
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Admin, Teacher, Student, Finance


# Student model with automatic admission number generation
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_number = db.Column(db.String(10), unique=True)
    course_name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    teacher = db.relationship('Teacher', backref='students', primaryjoin="Student.teacher_id == Teacher.id")

    user = db.relationship('User', backref='students', uselist=False)

    # Rename backref here to avoid conflict
    # fees = db.relationship('Fee', backref='student_fees', lazy=True)  # Changed 'fees_link' to 'student_fees'
    fees = db.relationship('Fee', back_populates='student')
    

    assignments = db.relationship('Assignment', backref='assigned_student', lazy=True)
    marks = db.relationship('Mark', backref='student_marks', lazy=True)
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    remarks = db.relationship('Remark', backref='student_remarks', lazy=True)

    @staticmethod
    def generate_admission_number():
        last_student = Student.query.order_by(Student.id.desc()).first()
        if last_student:
            new_admission_number = f"{int(last_student.admission_number) + 1:03}"
        else:
            new_admission_number = "001"
        return new_admission_number


# Teacher model
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)

    # Relationship with assignments, attendance, and remarks
    assignments = db.relationship('Assignment', backref='teacher_assignments', lazy=True)
    remarks = db.relationship('Remark', backref='teacher_remarks', lazy=True)


# Finance model to manage fees and payments
class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Add this line
    # student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    # total_amount = db.Column(db.Float, nullable=True)

    # # Establish relationship with the User model
    # user = db.relationship('User', backref='finances', lazy=True)
    # fees = db.relationship('Fee', backref='finance_fees', lazy=True)


# Fee structure for each student
class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    # finance_id = db.Column(db.Integer, db.ForeignKey('finance.id'), nullable=False)
    amount_due = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Pending")

    # Update the backref to avoid conflict
    # finance = db.relationship('Finance', backref='finance_fees')  # Changed 'fees' to 'finance_fees'
    # student = db.relationship('Student', backref='fees_student')  # Keep this change from previous
    student = db.relationship('Student', back_populates='fees')


# Attendance model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(10))  # Present, Absent


# Remark model for teachers to provide feedback for students
class Remark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='student_remarks')  # Change backref to avoid conflict
    teacher = db.relationship('Teacher', backref='teacher_remarks')  # Adjusted backref


# Assignment model for teachers to post assignments for students
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Assigned')

    # Update the backref to avoid conflict
    teacher = db.relationship('Teacher', backref='teacher_assignments')  # Changed 'assignments' to 'teacher_assignments'
    student = db.relationship('Student', backref='student_assignments')  # Kept change from previous


# Mark model to store student marks
class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)  # Subject for the marks
    score = db.Column(db.Float, nullable=False)  # The marks scored by the student
    test_type = db.Column(db.String(20), nullable=False)  # Assignment, CAT, or End Term
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Use a unique backref name to avoid conflict
    student = db.relationship('Student', backref='student_marks')  # This defines the backref
    teacher = db.relationship('Teacher', backref='teacher_marks')  # Adjusted backref


class PasswordResetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Assuming you have a User model
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='password_reset_requests')

    def __init__(self, user_id, reason):
        self.user_id = user_id
        self.reason = reason
