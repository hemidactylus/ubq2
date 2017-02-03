from flask import   (
                        render_template,
                        flash,
                        redirect,
                        session,
                        url_for,
                        request,
                        g,
                    )
from flask_login import  (
    login_user,
    logout_user,
    current_user,
    login_required,
)
from datetime import datetime
from markupsafe import Markup

from app import app, lm
from .forms import (
    LoginForm,
    UserSettingsForm,
    ChangePasswordForm,
)
from app.database.dbtools import (
    dbGetUser,
    dbOpenDatabase,
    dbUpdateUser,
)
from config import dbFullName
from app.database.models import (
    User,
)

@app.before_request
def before_request():
    g.user = current_user

# user loader function given to flask_login. This queries the db to fetch a user by id
@lm.user_loader
def load_user(id):
    db=dbOpenDatabase(dbFullName)
    return dbGetUser(db,id)

def flashMessage(msgType,msgHeading,msgBody):
    '''
        Enqueues a flashed structured message for use by the render template
        
            'msgType' can be: critical, error, warning, info
    '''
    flash(Markup('<strong>%s: </strong> %s' % (msgHeading,msgBody)), msgType)

@app.route('/')
@app.route('/index')
def ep_index():
    user = g.user
    return render_template(
                            "index.html",
                            user=user,
                           )

@app.route('/update1.php')
def ep_update():
    newNumber=request.args.get('N')
    counterKey=request.args.get('K')
    return('We`ll be there shortly.')

@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def ep_changepassword():
    user=g.user
    form=ChangePasswordForm()
    #
    if form.validate_on_submit():
        # actual password change. Alter current User object and save it back
        if user.checkPassword(form.oldpassword.data):
            user.passwordhash=User._hashString(form.newpassword.data)
            db=dbOpenDatabase(dbFullName)
            dbUpdateUser(db,user)
            db.commit()
            flashMessage('info','Done','password changed successfully')
        else:
            flashMessage('warning','Warning','wrong password.')
        return redirect(url_for('ep_index'))
    else:
        return render_template  (
                                    'changepassword.html',
                                    form=form,
                                    title='Change password',
                                    user=user,
                                )

@app.route('/login', methods=['GET', 'POST'])
def ep_login():
    user=g.user
    if user is not None and user.is_authenticated:
        return redirect(url_for('ep_index'))
    form = LoginForm()
    if form.validate_on_submit():
        db=dbOpenDatabase(dbFullName)
        qUser=dbGetUser(db, form.username.data)
        if qUser and qUser.checkPassword(form.password.data):
            login_user(qUser)
            #
            flashMessage('info','Login successful', 'welcome, %s!' % qUser.fullname)
            #
            return redirect(url_for('ep_index'))
        else:
            flashMessage('warning','Cannot log in','invalid username/password provided')
            return redirect(url_for('ep_index'))
    return render_template('login.html', 
                           title='Log in',
                           form=form,
                           user=user,
    )

@app.route('/usersettings', methods=['GET','POST'])
@login_required
def ep_usersettings():
    user=g.user
    f=UserSettingsForm()
    if f.validate_on_submit():
        user.email=f.email.data
        user.subscribed=int(f.subscribed.data)
        db=dbOpenDatabase(dbFullName)
        dbUpdateUser(db,user)
        db.commit()
        flashMessage('info','Done','settings updated')
        return redirect(url_for('ep_index'))
    else:
        f.email.data=user.email
        f.subscribed.data=bool(user.subscribed)
        return render_template(
            'usersettings.html',
            user=user,
            form=f,
        )

@app.route('/logout')
@login_required
def ep_logout():
    if g.user is not None and g.user.is_authenticated:
        flashMessage('info','Logged out successfully','goodbye')
        logout_user()
    return redirect(url_for('ep_index'))        
