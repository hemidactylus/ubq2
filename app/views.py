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
from time import time
from markupsafe import Markup

from app import app, lm
from config import (
    dbFullName,
    NOT_FOUND_COUNTER_MESSAGE,
    NOT_FOUND_COUNTER_VALUE,
    DEFAULT_COUNTER_COLORS,
    COUNTER_OFF_MESSAGE,
    COUNTER_OFF_VALUE,
    COUNTER_MAINTENANCE_MESSAGE,
    COUNTER_MAINTENANCE_VALUE,
    COUNTER_OFFLINE_MESSAGE_TEMPLATE,
    COUNTER_OFFLINE_VALUE,
    MODE_ICON_MAP,
    IFRAME_EMBED_CODE,
    APP_COMPLETE_ADDRESS,
)
from .forms import (
    LoginForm,
    UserSettingsForm,
    ChangePasswordForm,
    EditCounterForm,
    SettingsForm,
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
    dbGetSetting,
    dbSaveSetting,
)
from app.database.models import (
    User,
    Counter,
)
from app.database.staticValues import (
    counterModeMap,
)
from app.counters.counters import signalNumberToCounter, checkCounterActivity
from app.utils.htmlColors import htmlColors
from app.utils.dateformats import formatTimestamp, formatTimeinterval
from app.utils.parsing import integerOrNone

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
    '''
        this call, which sends a number-signal to a counter,
        historically has NO COUNTER ID. Identification of counter
        relies on the secret-key (ugly, future fix?)
    '''
    newNumber=integerOrNone(request.args.get('N'))
    counterKey=integerOrNone(request.args.get('K'))
    # this function must return:
    #   3   if malformed request
    #   2   key is unregistered
    #   1   not enough arguments
    #   0   all well (including when N is out of bounds, in which case -> -1)
    if newNumber is None or counterKey is None:
        return '3'
    else:
        return signalNumberToCounter(counterKey, newNumber)

@app.route('/checkbeat')
def ep_checkbeat():
    '''
        this is called from a heartbeat job and triggers offline-counter-checks
    '''
    db=dbOpenDatabase(dbFullName)
    allCounters=dbGetCounters(db)
    for cnt in allCounters:
        checkCounterActivity(db, cnt.id)
    db.commit()
    return '0'

@app.route('/embedcode/<counterid>')
@login_required
def ep_embedcode(counterid):
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counter=dbGetCounter(db, counterid)
    iframeCode=IFRAME_EMBED_CODE.format(
        prefix=APP_COMPLETE_ADDRESS,
        url=url_for('ep_showcounter',counterid=counterid)
    )
    return render_template(
        'embedcode.html',
        user=user,
        embedcode=[escape(li) for li in iframeCode.split('\n') if li.strip()!=''],
        fullname=counter.fullname,
    )

@app.route('/showcounter/<counterid>')
def ep_showcounter(counterid):
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counterDict=dbGetCounter(db, counterid, keepAsDict=True)
    #
    if counterDict is not None:
        counterStatus=dbGetCounterStatus(db, counterDict['id'], keepAsDict=True)
        if counterStatus is not None:
            # HERE the logic to decide what to show
            if counterDict['mode']=='o':
                counterDict['message']=COUNTER_OFF_MESSAGE
                counterDict['value']=COUNTER_OFF_VALUE
            elif counterDict['mode'] in ['a','p']:
                if counterStatus['online']:
                    # online display
                    counterDict['message']=formatTimestamp(
                        counterStatus['lastchange'],
                        dbGetSetting(db,'WORKING_TIMEZONE')
                    )
                    counterDict['value']=str(counterStatus['value'])
                else:
                    # offline display
                    counterDict['message']=COUNTER_OFFLINE_MESSAGE_TEMPLATE % \
                        formatTimeinterval(time()-counterStatus['lastupdate'])
                    counterDict['value']=COUNTER_OFFLINE_VALUE
            elif counterDict['mode']=='m':
                counterDict['message']=COUNTER_MAINTENANCE_MESSAGE
                counterDict['value']=COUNTER_MAINTENANCE_VALUE
            else:
                raise ValueError('Invalid counterdict.mode (counter %s)' % counterid)
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
        cnt['modedesc']=counterModeMap[cnt['mode']]
        cnt['modeicon']=MODE_ICON_MAP[cnt['mode']]

    return render_template(
        'counters.html',
        user=user,
        title='Counter Listing',
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
        print('CounterID=%s (isnone=%s)' % (counterid, counterid is None))
        if counterid is not None:
            status,msg=dbUpdateCounter(db, newCnt)
        else:
            print('dbAC')
            status,msg=dbAddCounter(db, newCnt)
        if status==0:
            db.commit()
            flashMessage(
                'success',
                'Done',
                '%s %sed successfully' % (
                    cntName,
                    ('updat' if counterid else 'insert')
                )
            )
        else:
            flashMessage(
                'error',
                'Could not proceed',
                'error while updating record (%s)' % msg,
            )
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
        else:
            f.fcolor.data=DEFAULT_COUNTER_COLORS['fcolor'] if not f.fcolor.data else f.fcolor.data
            f.bcolor.data=DEFAULT_COUNTER_COLORS['bcolor'] if not f.bcolor.data else f.bcolor.data
            f.ncolor.data=DEFAULT_COUNTER_COLORS['ncolor'] if not f.ncolor.data else f.ncolor.data
        return render_template(
            'editcounter.html',
            title='Counter Properties',
            user=user,
            form=f,
        )

@app.route('/colorhelp')
def ep_colorhelp():
    user=g.user
    colors=sorted(list(htmlColors.items()))
    return render_template(
        'colorhelp.html',
        title='Color Help',
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

@app.route('/generalsettings', methods=['GET', 'POST'])
@login_required
def ep_generalsettings():
    user=g.user
    db=dbOpenDatabase(dbFullName)
    f=SettingsForm()
    if f.validate_on_submit():
        # load and validate values in form and save them to DB
        dbSaveSetting(db,'COUNTER_OFFLINE_TIMEOUT',f.offlinetimeout.data)
        db.commit()
        flashMessage('info','Done','settings updated')
        return redirect(url_for('ep_index'))
    else:
        # load settings from DB to the form
        f.offlinetimeout.data=dbGetSetting(db,'COUNTER_OFFLINE_TIMEOUT')
        f.alerttimeout.data=dbGetSetting(db,'COUNTER_ALERT_TIMEOUT')
        f.alertwindowstart.data=dbGetSetting(db,'ALERT_WINDOW_START')
        f.alertwindowend.data=dbGetSetting(db,'ALERT_WINDOW_END')
        f.workingtimezone.data=dbGetSetting(db,'WORKING_TIMEZONE')
        # show the form
        return render_template(
            'generalsettings.html',
            user=user,
            title='General settings',
            form=f
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
            title='User Settings',
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
