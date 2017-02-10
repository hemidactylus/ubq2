----------------------------
UBQ 2 SERVER-SIDE TECH SPECS
----------------------------

# Doing and to-do

- Slowness in editing counters: to investigate. After 'save counter' there's sometimes a 1-2 sec delay
    before the ep_counters endpoint is queried. Seemingly out-of-my-code, perhaps DB related?

- svg digits

- Logging system, tracking system, their plot with D3 and a smart way of archiving historical data
- do it via status,return on all DB calls! (some already have it)
    A single table with various types of logged messages? Or a different table per message type?

        (userID, day, counter)    firstReq, lastReq, numReqs
            for each requestor, progressively update usage stats

        (day, counter)                         startTime, endTime, number
            for each counter and number, record the permanence
            Being offline counts as a number (e.g. -1 or so) and is a separate status

        (date, counter)                         modeChange(prevmode-newmode), time
            for each counter log the pointlike off/online changes and mode setting change

        (date) anomalyCode, anomalyString
            (more generic) email sent, malformed/wrongcode requests...

    A weekly archiving of such events...? Or a separate DB from the start (perhaps better)

Counter States Spans:
    each counter is represented by (n,start,stop), n= the number or -1 (offline)
    In signalnumbertocounter and checkcounteractivity this must happen:
        if change of number, use the date of last-update as start and record the
        just elapsed (n,start,stop)

        => Table 'stats_numbers'
            day, counter, number, starttime, endtime


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

* Usage stats through a cookie- and useragent-based anon ID.