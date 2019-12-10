from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError, Email, EqualTo
from app.models import User


class LoginForm(FlaskForm):
    # DataRequired，当你在当前表格没有输入而直接到下一个表格时会提示你输入
    username = StringField('Username', validators=[DataRequired(message='Please input username')])
    password = PasswordField('Password', validators=[DataRequired(message='Please input password')])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign in')


class RegistrationForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'comfirmed password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Repeated Username')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Repeated Email')


from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='请输入用户名!')])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')
