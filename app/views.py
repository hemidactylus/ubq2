from flask import   (
                        render_template,
                        flash,
                        redirect,
                        session,
                        url_for,
                        request,
                        g,
                        abort,
                        escape,
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
from config import (
    dbFullName,
    NOT_FOUND_COUNTER_MESSAGE,
    NOT_FOUND_COUNTER_VALUE,
)
from .forms import (
    LoginForm,
    UserSettingsForm,
    ChangePasswordForm,
    EditCounterForm,
)
from app.database.dbtools import (
    dbGetUser,
    dbOpenDatabase,
    dbUpdateUser,
    dbGetCounters,
    dbGetCounter,
    dbGetCounterStatus,
    dbAddCounter,
    dbUpdateCounter,
    dbDeleteCounter,
)
from app.database.models import (
    User,
    Counter,
)
from app.database.staticValues import (
    counterModeMap,
)
from app.utils.htmlColors import htmlColors

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
    flash(Markup('<strong>%s: </strong> %s' % (escape(msgHeading),escape(msgBody))), msgType)

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
    return('We\'ll be there shortly.')

@app.route('/showcounter/<counterid>')
def ep_showcounter(counterid):
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counterDict=dbGetCounter(db, counterid, keepAsDict=True)
    #
    if counterDict is not None:
        counterStatus=dbGetCounterStatus(db, counterDict['id'], keepAsDict=True)
        if counterStatus is not None:
            counterDict['message']='Test Test!'
            counterDict['value']='19'
        else:
            # default: absence of anything
            counterDict['message']=NOT_FOUND_COUNTER_MESSAGE
            counterDict['value']=NOT_FOUND_COUNTER_VALUE
        #
        return render_template(
            'counterframe.html',
            user=user,
            counter=counterDict
        )
    else:
        # not a recognised counter
        abort(404)

@app.route('/counters')
def ep_counters():
    '''
        No login required: if logged in, edit facilities are there.
        Else, they aren't and this is just the overall view.
    '''
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counters=sorted(dbGetCounters(db))
    if not user.is_authenticated:
        # take out the private counters
        visibleCounters=[cnt.asDict() for cnt in filter(lambda c: c.mode!='p', counters)]
    else:
        visibleCounters=[cnt.asDict() for cnt in counters]

    # prepare for pretty output
    for cnt in visibleCounters:
        cnt['mode']=counterModeMap[cnt['mode']]

    return render_template(
        'counters.html',
        user=user,
        counters=visibleCounters,
    )

@app.route('/editcounter', methods=['GET','POST'])
@app.route('/editcounter/<counterid>', methods=['GET','POST'])
@login_required
def ep_editcounter(counterid=None):
    user=g.user
    f=EditCounterForm()
    db=dbOpenDatabase(dbFullName)
    counterIDs=[cnt.id for cnt in dbGetCounters(db)]
    f.setExistingIDs(counterIDs)
    if counterid:
        f.setThisID(counterid)
    if f.validate_on_submit():
        # it can be a savenew or a edit-existing. This is decided
        # by the presence of 'counterid'
        if counterid:
            if counterid != f.counterid.data:
                flashMessage('error', 'Forbidden edit', 'a change of id was detected and will be ignored')
                f.counterid.data=counterid
        else:
            if f.counterid.data in counterIDs:
                flashMessage('critical', 'Cannot create item', 'id exists already')
                return redirect(url_for('ep_counters'))
        # create the object
        newCnt=Counter(
            id=f.counterid.data,
            fullname=f.fullname.data,
            notes=f.notes.data,
            key=int(f.key.data),
            mode=f.mode.data,
            fcolor=f.fcolor.data,
            bcolor=f.bcolor.data,
            ncolor=f.ncolor.data,
        )
        cntName = str(newCnt)
        # save, give ok, redirect
        if counterid:
            dbUpdateCounter(db, newCnt)
        else:
            dbAddCounter(db, newCnt)
        db.commit()
        flashMessage(
            'success',
            'Done',
            '%s %sed successfully' % (
                cntName,
                ('updat' if counterid else 'insert')
            )
        )
        print('cntName="%s"' % cntName)
        return redirect(url_for('ep_counters'))
    else:
        if counterid is not None:
            counter=dbGetCounter(db,counterid)
            if counter is not None:
                f.counterid.data=counter.id
                f.fullname.data=counter.fullname
                f.notes.data=counter.notes
                f.key.data=str(counter.key)
                f.mode.data=counter.mode
                f.fcolor.data=counter.fcolor
                f.bcolor.data=counter.bcolor
                f.ncolor.data=counter.ncolor
            else:
                flashMessage('error','Wrong counter','cannot find the requested item.')
                return redirect(url_for('ep_counters'))
        return render_template(
            'editcounter.html',
            user=user,
            form=f,
        )

@app.route('/colorhelp')
def ep_colorhelp():
    user=g.user
    colors=sorted(list(htmlColors.items()))
    return render_template(
        'colorhelp.html',
        colors=colors,
        user=user,
    )

@app.route('/deletecounter/<counterid>')
@login_required
def ep_deletecounter(counterid):
    '''
        We allow deletion only if the counter is set to Off.
        This acts as a safety catch of sorts
    '''
    user=g.user
    db=dbOpenDatabase(dbFullName)
    tCounter=dbGetCounter(db, counterid)
    if tCounter:
        if tCounter.mode!='o':
            flashMessage('warning', 'Cannot delete', 'only counters with mode set to OFF can be deleted.')
        else:
            # actual delete
            dbDeleteCounter(db, tCounter.id)
            db.commit()
            flashMessage('success','Done','%s deleted successfully' % str(tCounter))
    else:
        flashMessage('error','Wrong counter','cannot find the requested item.')
    return redirect(url_for('ep_counters'))

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
