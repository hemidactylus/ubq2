from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms.fields.html5 import EmailField
from wtforms import (
                        StringField,
                        BooleanField,
                        PasswordField,
                        SelectField,
                        SelectMultipleField,
                        SubmitField,
                        HiddenField,
                        IntegerField,
                    )
from wtforms.validators import DataRequired, NumberRange, EqualTo, Required

class LoginForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    login = SubmitField('Log In')

class UserSettingsForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    subscribed = BooleanField('Receive Alerts')
    submit = SubmitField('Save settings')

class ChangePasswordForm(FlaskForm):
    submit = SubmitField('Change password')
    oldpassword = PasswordField('oldpassword', validators=[DataRequired()])
    newpassword = PasswordField('newpassword', [Required(),
                                                EqualTo('confirmpassword', message='New password mismatch')])
    confirmpassword  = PasswordField('confirmpassword')
