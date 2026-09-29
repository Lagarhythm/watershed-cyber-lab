# Facilitation guide

> This guide covers the optional code-oriented companion. For the current visual student app, use [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md).

Audience: faculty evaluating interactive teaching and introductory cybersecurity students. Familiarity with running a code cell helps; advanced Python is unnecessary. Students learn integrity verification, representation versus confidentiality, evidence filtering, temporal correlation, parameterized queries, and bounded incident conclusions.

## Pacing and discussion

| Section | Minutes | Facilitation prompt and expected result |
|---|---:|---|
| Briefing | 5 | “Which facts would we need before calling this a compromise?” Explain trusted manifest and UTC. |
| Integrity | 8 | Change one character, then equalize inputs. Students identify one mismatch; explain that it says nothing about intent. |
| Artifacts | 7 | “Did we need a secret key?” Students decode structured leads without executing the artifact. |
| Logs | 10 | “Is matching an account enough?” Require host, process, event type and timestamp together. |
| Network | 8 | Compare regular backup traffic with the selected process. Ask what telemetry cannot prove. |
| Secure coding | 10 | Run failing checks, repair the query, rerun. Ask why an apostrophe should work as ordinary data. |
| CTF and case note | 15 | Work in pairs; one analyst operates, one asks for evidence. Use progressive hints after a reasoned attempt. |
| Debrief / instructor view | 7 | Compare local feedback with the simulated cohort; identify one transferable pattern. |

For a faculty workshop, use the 20-minute demo script and allow a further 20 minutes for adaptation. For asynchronous use, give learners the student archive, objectives, 75-minute estimate, and submission instructions: save the notebook with the completed analyst note. Review reasoning manually alongside stage progress; local JSON is not an authoritative grade record.

## Expected misconceptions and scaffolding

- Hashing is not encryption, and a hash mismatch is not a malware verdict. Ask students to list benign reasons for change.
- Base64 is representation, not secrecy. Let learners try decoding an ordinary text file and interpret the format error.
- A familiar port does not certify safe traffic. Ask for the host/process/time correlation.
- Periodicity is not enough: backup_agent is an intentional benign counterexample.
- A login vulnerability does not inherently execute programs. The scenario explicitly includes a subsequent authorized job-runner feature abused by the obtained session.
- If repair checks keep failing, check that the learner reran the edited function cell before the assessment cell. `(username,)` must be a tuple, including its comma.
- If filters produce no rows, clear them and add one condition at a time.

Hints are conceptual, directional, then procedural. After roughly two minutes without a new hypothesis, offer level 1; after an attempted filter or calculation, offer level 2. Use level 3 when mechanics obscure the concept. Hints carry no score penalty; the dashboard records the highest level revealed for each stage.

## Instructor solution — keep out of student handouts

All events occur on 2026-09-14 UTC.

1. Hash the manifest's files: **collector_config.txt** differs from its trusted baseline. `research_notes.txt` and `readme.txt` match.
2. Decode that file as Base64 JSON. Username **riley**, host **research-07**, process **sync_agent**, event **SYS-042**.
3. Filter system events: **SYS-042** is the matching process start at **09:14**.
4. Filter network by that host and process. Destination **203.0.113.77** appears eight times, 09:15–09:22, with 60-second intervals and 128 bytes sent per record. This supports suspicious periodic communication, not proven exfiltration.
5. Name **SQL injection**. AUTH-041 at 09:11 records a predicate-changing login for session DEMO-7. Use this correction and rerun checks:

```python
def lookup_user(connection, username):
    return connection.execute(
        'SELECT username FROM users WHERE username = ?', (username,)
    ).fetchall()
```

6. Timeline: portal access (AUTH-041, 09:11) → research job invoked (SYS-040, 09:12) → collector file replaced (SYS-041, 09:13) → sync process started (SYS-042, 09:14) → first outbound communication (09:15) → sensitive file read (SYS-043, 09:23). Assign ranks to the labels, which appear in a deliberately shuffled order.

The final token is generated from the accepted scenario when stage 6 passes and shown in the progress panel. There is no token to search for in an artifact. Stage 5 requires the secure-code module to have passed as well as the vulnerability name.

## Case-note review and debrief

A strong note cites the mismatch, decoded clue, matching process event, first connection, portal login, and later file read. It distinguishes the recorded job invocation from inference and does not claim confirmed data exfiltration. Ask: “Which log could be missing or misleading?” “What would packet content or access-control logs add?” “How would you transfer this workflow to experimental evidence?”

The dashboard is a teaching demonstration. Local lesson checks are formative; CTF failures and hints are tracked by stage. The cohort numbers are invented and are never merged with the local session. Use the simulated network difficulty to discuss when to reteach correlation rather than simply reveal the answer.
