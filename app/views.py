from flask import (
    render_template,
    flash,
    redirect,
    session,
    url_for,
    request,
    g,
    abort,
    escape,
    make_response,
    jsonify,
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
import uuid
import hashlib

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
    USE_ANONYMOUS_COOKIES,
    COOKIE_DURATION_SECONDS,
    PERFORM_USER_IDENTIFICATION,
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
    dbGetSystemAlerts,
    dbGetSystemAlert,
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
from app.counters.counters import (
    signalNumberToCounter,
    checkCounterActivity,
    checkBeat,
)
from app.database.dblogging import (
    getCounterStatusSpans,
    logUserCounterRequest,
)
from app.utils.htmlColors import htmlColors
from app.utils.dateformats import (
    formatTimestamp,
    formatTimeinterval,
    stringToTimestamp,
    pastTimestamp,
    localDateFromTimestamp,
    toJavaTimestamp,
    makeJavaDay,
    javaTimestampToTimestamp,
)
from app.utils.parsing import integerOrDefault

from app.data_endpoints import (
    DATA_counterstats_timeplot_days,
    DATA_counterstats_timeplot_data,
    DATA_counter_duration_data,
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
    flash(Markup('<strong>%s: </strong> %s' % (escape(msgHeading),escape(msgBody))), msgType)

@app.route('/')
@app.route('/index')
def ep_index():
    user = g.user
    return render_template(
                            "index.html",
                            user=user,
                           )

@app.route('/update1')
@app.route('/update1.php')
def ep_update():
    '''
        this call, which sends a number-signal to a counter,
        historically has NO COUNTER ID. Identification of counter
        relies on the secret-key (ugly, future fix?)
    '''
    newNumber=integerOrDefault(request.args.get('N'))
    counterKey=integerOrDefault(request.args.get('K'))
    # this function must return:
    #   3   if malformed request
    #   2   key is unregistered
    #   1   not enough arguments
    #   0   all well (including when N is out of bounds, in which case -> -1)
    if newNumber is None or counterKey is None:
        return '3'
    else:
        return signalNumberToCounter(counterKey, newNumber, request)

@app.route('/checkbeat')
def ep_checkbeat():
    '''
        this can be called from a heartbeat job and triggers offline-counter-checks
    '''
    db=dbOpenDatabase(dbFullName)
    checkBeat(db)
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
    embedlines=[li for li in iframeCode.split('\n') if li.strip()!='']
    embedcode=[]
    for li in embedlines:
        nspaces=0
        for c in li:
            if c==' ':
                nspaces+=1
            else:
                break
        embedcode.append(
            {
                'br': True,
                'contents': escape(li[nspaces:]),
                'spaces': nspaces,
            }
        )
    embedcode[-1]['br']=False
    return render_template(
        'embedcode.html',
        user=user,
        embedcode=embedcode,
        fullname=counter.fullname,
    )

@app.route('/showcounter/<counterid>')
def ep_showcounter(counterid):
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counterDict=dbGetCounter(db, counterid, keepAsDict=True)
    #
    if counterDict is not None:
        # requestor identification is here
        userId=None
        if PERFORM_USER_IDENTIFICATION:
            try:
                if USE_ANONYMOUS_COOKIES:
                    userId=request.cookies.get('uuid',str(uuid.uuid4()))
                else:
                    userId=hashlib.sha1(request.headers.get('User-Agent','').encode()).hexdigest()
            except:
                pass
        if userId:
            logUserCounterRequest(db,userId,counterid)
        # end of req id
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
        # use of a 'response' to set the cookie if it's the case
        response=make_response(
            render_template(
                'counterframe.html',
                user=user,
                counter=counterDict
            )
        )
        # cookie setting, a one-year cookie
        if PERFORM_USER_IDENTIFICATION:
            if USE_ANONYMOUS_COOKIES:
                response.set_cookie('uuid',userId,max_age=COOKIE_DURATION_SECONDS)
        #
        return response
    else:
        # not a recognised counter
        abort(404)

@app.route('/system_alerts')
@app.route('/system_alerts/<count>')
@login_required
def ep_system_alerts(count=None):
    '''
        A simple query to retrieve [the latest] system alerts and view them as a basic list
    '''
    user=g.user
    db=dbOpenDatabase(dbFullName)
    dbTZ=dbGetSetting(db,'WORKING_TIMEZONE')
    alerts=sorted(dbGetSystemAlerts(db),reverse=True)
    if count is not None:
        alerts=alerts[:integerOrDefault(count,10)]
    #
    print(','.join(map(str,alerts)))
    return render_template(
        'system_alerts.html',
        user=user,
        alerts=[sA.prettyFormat(dbTZ) for sA in alerts],
        cutlist=count,
    )

@app.route('/display_alert/<alertid>')
@login_required
def ep_display_alert(alertid):
    '''
        A simple query to retrieve a given system alert and display it
    '''
    user=g.user
    db=dbOpenDatabase(dbFullName)
    dbTZ=dbGetSetting(db,'WORKING_TIMEZONE')
    alert=dbGetSystemAlert(db,alertid=integerOrDefault(alertid))
    return render_template(
        'show_alert.html',
        user=user,
        alert=alert.prettyFormat(dbTZ,splitMessage=True),
    )

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
        if counterid is not None:
            status,msg=dbUpdateCounter(db, newCnt)
        else:
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
        offlinetimeout=f.offlinetimeout.data
        alerttimeout=f.alerttimeout.data
        backonlinealerttimeout=f.backonlinealerttimeout.data
        workingtimezone=f.workingtimezone.data
        checkbeatfrequency=f.checkbeatfrequency.data
        if int(alerttimeout)<offlinetimeout:
            flashMessage('critical','Settings error','alert time automatically raised to offline timeout.')
            alerttimeout=offlinetimeout
        try:
            alertwindowstart=stringToTimestamp(f.alertwindowstart.data)
        except:
            alertwindowstart=None
        try:
            alertwindowend=stringToTimestamp(f.alertwindowend.data)
        except:
            alertwindowend=None
        if alertwindowstart is None:
            flashMessage('critical','Invalid time','alert time window start was forcefully reset.')
            alertwindowstart=time(0,1)
        if alertwindowend is None:
            flashMessage('critical','Invalid time','alert time window end was forcefully reset.')
            alertwindowend=time(0,1)
        if alertwindowstart>=alertwindowend:
            flashMessage('warning','Warning','Alert-time setting effectively'
                ' disable any alert. Correct if necessary.')
        #
        dbSaveSetting(db,'CHECKBEAT_FREQUENCY',checkbeatfrequency)
        dbSaveSetting(db,'COUNTER_OFFLINE_TIMEOUT',offlinetimeout)
        dbSaveSetting(db,'COUNTER_ALERT_TIMEOUT',alerttimeout)
        dbSaveSetting(db,'COUNTER_BACK_ONLINE_TIMESPAN',backonlinealerttimeout)
        dbSaveSetting(db,'WORKING_TIMEZONE',workingtimezone)
        dbSaveSetting(db,'ALERT_WINDOW_START',alertwindowstart.strftime('%H:%M'))
        dbSaveSetting(db,'ALERT_WINDOW_END',alertwindowend.strftime('%H:%M'))
        db.commit()
        flashMessage('info','Done','settings updated')
        return redirect(url_for('ep_index'))
    else:
        # load settings from DB to the form
        f.checkbeatfrequency.data=dbGetSetting(db,'CHECKBEAT_FREQUENCY')
        f.offlinetimeout.data=dbGetSetting(db,'COUNTER_OFFLINE_TIMEOUT')
        f.alerttimeout.data=dbGetSetting(db,'COUNTER_ALERT_TIMEOUT')
        f.backonlinealerttimeout.data=dbGetSetting(db,'COUNTER_BACK_ONLINE_TIMESPAN')
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

@app.route('/counterstats_timeplot/<counterid>')
@login_required
def ep_counterstats_timeplot(counterid):
    '''
        The page with the counter-specific time plot
    '''
    user=g.user
    return render_template(
        'counterstat_timeplot.html',
        user=user,
        title='Time plot for counter "%s"' % counterid,
        counterid=counterid,
    )

@app.route('/accessstats_usage_per_day/<counterid>')
@login_required
def ep_accessstats_usage_per_day(counterid):
    '''
        The page with the counter-specific per-day usage plot
    '''
    user=g.user
    return render_template(
        'accessstats_usage_per_day.html',
        user=user,
        title='Usage statistics per day "%s"' % counterid,
        counterid=counterid,
    )

@app.route('/accessstats_weekly_patterns/<counterid>')
@login_required
def ep_accessstats_weekly_patterns(counterid):
    '''
        The page with the counter-specific per-weekday usage histogram
    '''
    user=g.user
    return render_template(
        'accessstats_weekly_patterns.html',
        user=user,
        title='Usage weekly patterns for "%s"' % counterid,
        counterid=counterid,
    )

@app.route('/accessstats_recurring_users/<counterid>')
@login_required
def ep_accessstats_recurring_users(counterid):
    '''
        The page with the counter-specific chart of recurring users
    '''
    user=g.user
    return render_template(
        'accessstats_recurring_users.html',
        user=user,
        title='Recurring viewers for "%s"' % counterid,
        counterid=counterid,
    )

@app.route('/accessstats_frequent_users/<counterid>')
@login_required
def ep_accessstats_frequent_users(counterid):
    '''
        The page with the counter-specific histogram of n-days-per-users
    '''
    user=g.user
    return render_template(
        'accessstats_frequent_users.html',
        user=user,
        title='Frequent viewers for "%s"' % counterid,
        counterid=counterid,
    )

@app.route('/ep_accessstats_daily_volumes/<counterid>')
@login_required
def ep_accessstats_daily_volumes(counterid):
    '''
        The page with the counter-specific
        daily-volumes (n_numbers, n_accesses) plot
    '''
    user=g.user
    return render_template(
        'accessstats_daily_volumes.html',
        user=user,
        title='Daily volumes for "%s"' % counterid,
        counterid=counterid,
    )


@app.route('/counterstats_durations/<counterid>')
@login_required
def ep_counterstats_durations(counterid):
    '''
        The page with the counter-specific time plot
    '''
    user=g.user
    return render_template(
        'counterstat_durations.html',
        user=user,
        title='Number durations for counter "%s"' % counterid,
        counterid=counterid,
    )

@app.route('/counterstats')
@login_required
def ep_counterstats():
    '''
        simply prepare a list of counter IDs / name to choose from,
        to access the number-series plot
    '''
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counters=[
        {
            'id': cnt.id,
            'name': cnt.fullname,
        }
        for cnt in sorted(dbGetCounters(db))
    ]
    return render_template(
        'counterstats.html',
        user=user,
        title='Number stats main menu',
        counters=counters,
    )

@app.route('/accessstats')
@login_required
def ep_accessstats():
    '''
        analogous to counterstats, for usage/access statistics
    '''
    user=g.user
    db=dbOpenDatabase(dbFullName)
    counters=[
        {
            'id': cnt.id,
            'name': cnt.fullname,
        }
        for cnt in sorted(dbGetCounters(db))
    ]
    return render_template(
        'accessstats.html',
        user=user,
        title='Access stats main menu',
        counters=counters,
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

@app.route('/about')
def ep_about():
    user=g.user
    return render_template(
        'about.html',
        title='About UBIQueue',
        user=user,
        )

@app.route('/logout')
@login_required
def ep_logout():
    if g.user is not None and g.user.is_authenticated:
        flashMessage('info','Logged out successfully','goodbye')
        logout_user()
    return redirect(url_for('ep_index'))        
