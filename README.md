----------------------------
UBQ 2 SERVER-SIDE TECH SPECS
----------------------------

# Counter modes:
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

# Doing and to-do

- do it via status,return on all DB calls! (some already have it)

- adjust all timezone issues (displays, time checks and so on)

# General notes

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

* Automated checks

* Data structure and panels

* Sending gmail from python with an application API
    SOLVED in library added to this project