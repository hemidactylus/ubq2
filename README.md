----------------------------
UBQ 2 SERVER-SIDE TECH SPECS
----------------------------

# Doing and to-do

- svg digits

- Logging system, tracking system, their plot with D3 and a smart way of archiving historical data
- do it via status,return on all DB calls! (some already have it)
    A single table with various types of logged messages? Or a different table per message type?

        (userID, AgentHeader, date, counter)    firstReq, lastReq, numReqs
            for each requestor, progressively update usage stats

        (date, counter)                         startTime, endTime, number
            for each counter and number, record the permanence

        (date, counter)                         stateChange(off->on, on->off), time
        (date, counter)                         modeChange(prevmode-newmode), time
            for each counter log the pointlike off/online changes and mode setting change

        (date) anomalyCode, anomalyString
            (more generic) email sent, malformed/wrongcode requests...

    A weekly archiving of such events...? Or a separate DB from the start (perhaps better)

- For (anon) user logging, set permanent cookie in client browser, see http://stackoverflow.com/questions/11773385/setting-a-cookie-in-flask ?
    * Options:
        User-Agent
        session (i.e. temp cookie)
        explicitly persistent cookied with a uuid

    * Plan:
        set a 2-year-cookie with uuid if it does not exist,
        else use that as an identifier.


**********

    print(request.headers.get('User-Agent'))

    if 'identity' in session:
        print('KNOWN ALREADY "%s"' % session['identity'])
    else:
        newID=uuid.uuid4()
        print('SETTING THIS GUY TO "%s"' % newID)
        session['identity']=newID

    # this replaces the usual render_template!

    if 'SampleCookie' in request.cookies:
        print('THERE ALREADY')
    resp=make_response( render_template(
        'counterframe.html',
        user=user,
        counter=counterDict
    ))
    if 'SampleCookie' not in request.cookies:
        print('SETTING COOKIE TO "%s"')
        resp.set_cookie('SampleCookie','AAA',max_age=86400*365)
    return resp


**********


- all email notification unified service is to be done

# General notes

* Counter modes:
    'a'     Active
                responds to updates
                raises warnings on offlines
                visible in the list page
    'p'     Private
                responds to updates
                raises warnings on offlines
                visible only for iframes that know the code
    'm'     Maintenance
                responds to updates
                raises warnings on offlines
                displays "--" / "Maintenance" in any case
    'o'     Off
                does NOT respond to updates (yields a 2 'key unregistered')
                does NOT raise warnings
                displays "--" / "Counter off" in any case

* Functionalities:
    - must serve html contents, one per counter, with the boxed number and the timer and the info
        (possibly with cookie-based proper access stats)
    - must serve a digest page with a list of all counters
    - must receive (password-protected) update-requests and update the counter accordingly
    
    - must allow a panel-based editing of the counter features:
        - create/edit/delete counter
        - counter status: maintenance, active, etc
        - counter operation hours/days
        - counter's right to be in the digest

    - must provide an email-sending interface e.g. for alerts
    
    - must have cron-based log analysis and stats
    - must have cron-based offline checks

* Ordinary requests:
    - http://www.salamandrina.net/ubq/update1.php?N=<STATUS_NUMBER>&K=<COUNTER_KEY>
    - http://salamandrina.net/ubq/index.html
    - http://salamandrina.net/ubq/<COUNTER_ID>/ubq_cnt.html
        COUNTER_ID = CC1, EM1, ...
    
    (there's some css and an iframe embedding at the moment)

* Sending gmail from python with an application API
    SOLVED in library added to this project

* The periodic checks on all counters are triggered by the infinite-loop script trigger_checkbeat.py
    which does not pass through any request and adapts in real-time to the configured frequency.
    This has to become an upstart job
