----------------------------
UBQ 2 SERVER-SIDE TECH SPECS
----------------------------

# Doing and to-do

    Make the decision whether to put a label to the number-time-plot depend on the width in pixels and not the duration in minutes!

- Slowness in editing counters: to investigate. After 'save counter' there's sometimes a 1-2 sec delay
    before the ep_counters endpoint is queried. Seemingly out-of-my-code,
    perhaps DB related (i.e. race condition on transaction)?

- make all where-clauses in queries NOT TO encode their value in the text! (see e.g. getCounterStatusSpans)

- svg digits

- Javascript+D3
    * How to iterate bindings to keyup with a loop in counter editor
    * Color of curves on css for the daily usages

**********

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

    - must provide an email-sending interface e.g. for alerts / an alert table for historical or failovers
    
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

* system-side features: a trigger_checkbeat that periodically checks for going-offline/email-alerts,
  as a systemd service. This must be configured upon install.
