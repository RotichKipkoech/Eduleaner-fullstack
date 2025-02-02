from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    submit = SubmitField('Login')

class CreateStudentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=100)])  # Changed 'name' to 'username'
    course_name = StringField('Course (e.g., Mathematics, Science)', validators=[DataRequired(), Length(max=50)])  # Renamed 'class_name' to 'course'
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    submit = SubmitField('Create Student')

class CreateTeacherForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Create Teacher')

class CreateFinanceForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    submit = SubmitField('Create Finance')
