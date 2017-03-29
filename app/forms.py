import pytz
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

from app.utils.validators import (
    ColorExpression,
    IntegerString,
    NoDuplicateID,
    TimeExpression,
)
from app.database.staticValues import counterModes
from config import DEFAULT_COUNTER_MODE

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

class EditCounterForm(FlaskForm):
    counterid=StringField('id',validators=[DataRequired(),NoDuplicateID()])
    fullname=StringField('fullname',validators=[DataRequired()])
    notes=StringField('notes')
    key=StringField('key',validators=[DataRequired(),IntegerString(allowEmpty=False)])
    mode=SelectField('mode', choices=counterModes, default=DEFAULT_COUNTER_MODE)
    fcolor=StringField('fcolor',validators=[DataRequired(),ColorExpression()])
    bcolor=StringField('bcolor',validators=[DataRequired(),ColorExpression()])
    ncolor=StringField('ncolor',validators=[DataRequired(),ColorExpression()])
    submit=SubmitField('Save')

    def setExistingIDs(self,existingIDs):
        self.existingIDs=existingIDs
        self.newItem=True

    def setThisID(self,thisID):
        self.thisID=thisID
        self.newItem=False

class SettingsForm(FlaskForm):
    checkbeatfrequency=IntegerField('checkbeatfrequency',validators=[NumberRange(min=1)])
    offlinetimeout=IntegerField('offlinetimeout',validators=[NumberRange(min=1)])
    alerttimeout=IntegerField('alerttimeout',validators=[NumberRange(min=1)])
    backonlinealerttimeout=IntegerField('backonlinealerttimeout',validators=[NumberRange(min=1)])
    alertwindowstart=StringField('alertwindowstart',validators=[TimeExpression()])
    alertwindowend=StringField('alertwindowend',validators=[TimeExpression()])
    workingtimezone=SelectField('workingtimezones',choices=[(t,t) for t in sorted(pytz.common_timezones)])
    submit=SubmitField('Save settings')
