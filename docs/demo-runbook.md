# Final review - demo runbook

The live demo, written down so any of us can run it under pressure. Every
number in here came from an actual run on Nov 5, not from memory. The whole
thing is about 5 minutes including talking.

Before our slot: laptop charged, terminal open, camera and mic already
tested, repo fetched once (git fetch origin). After that the demo needs no
internet - the data file is read from the local git copy.

## Part 0 - setup (2 minutes before we start)

    cd ~/CAN-Sentinel
    git checkout member-3
    python3 --version        # 3.10.x is what we test on

## Part 1 - the whole pipeline in 30 seconds

    python3 -m alerts.demo

What comes out: six numbered steps. A DoS flood folds 10 events into 1
alert (occurrences=10). An airbag alert jumps to HIGH because 0x0D2 is on
the critical-ID list. A malformed event gets rejected and logged, nothing
crashes. One alert is acknowledged, one resolved. At the end, the exact
JSON the dashboard renders.

While it runs, say: "One command, the whole alert pipeline - dedupe,
severity, validation, lifecycle, and the dashboard feed."

## Part 2 - real attack data (the main event)

This pipes the real GEM e6 capture from the shared branch straight into
the replay:

    git show origin/develop:GEM_Attack_Scenario_Raw_Labeled.csv | python3 -m alerts.replay_gem - --base 1793318400 --vehicle gem_e6

What comes out (verified Nov 5):

    replayed: events=42405 row-rejected=0 manager-rejected=0 alerts=1292

and a triage list with one row per attacked system:

    0x000       1 alert,    41080 occurrences   HIGH  (DoS flood)
    0x18FF00F9  654 alerts, 663 occurrences     HIGH  (brake tampering)
    0x18FF70F9  637 alerts, 662 occurrences     HIGH  (steering tampering)

While it runs, say: "Real vehicle capture, 42 thousand attack messages.
Watch the triage list - the DoS is 41,080 messages on ID 0x000, the
highest-priority ID on a CAN bus, and it lands as one folded alert."

Numbers to know by heart if they ask:

- 42,405 attack events replayed, zero rejected
- 41,080 DoS messages folded into a single alert (dedupe window)
- brake 0x18FF00F9 and steering 0x18FF70F9 are the tampered PACMod IDs
- timestamps change between runs (that is the --base anchor); counts do not

The --vehicle gem_e6 flag matters. Without it the pipeline uses the mock
profile and the three systems above do not escalate. If the output looks
different, check that flag first.

## Part 3 - optional: normal driving, zero alerts

    git show origin/develop:GEM_CAN_Dataset.csv | python3 -m alerts.replay_gem - --vehicle gem_e6

The false-positive check: normal driving through the same pipeline,
should end with alerts=0. We did not rehearse this one yet - run it once
before using it live.

## If an evaluator asks "is this live detection?"

Honest answer: no. The GEM file is labeled ground truth, so the label acts
as the detector. What we are showing is the alerting pipeline on real
vehicle data - validation, severity, critical-ID escalation, dedupe
folding, persistence, reporting. Label-free detection on this data is the
ML track. Saying it plainly is better than getting caught overselling it.

## If something breaks

- "No module named alerts" - wrong folder. cd ~/CAN-Sentinel and retry.
- import error from demo.py - wrong branch. git checkout member-3.
- "did not match any file" on the git show line - the CSV moved on the
  shared branch. Find it with: git ls-tree --name-only origin/develop | grep GEM
- numbers look different - you probably dropped --vehicle gem_e6.
- wifi dies - nothing stops. Everything runs from the local machine.
