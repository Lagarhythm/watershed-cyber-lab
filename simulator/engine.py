"""Deterministic teaching simulation. No sockets, subprocesses or real host actions."""
import base64
import copy
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'research-07': 'Research workstation', 'research-08': 'Backup workstation',
         'portal-01': 'Research portal', 'archive-01': 'Research archive'}
START = datetime(2026, 9, 14, 9, 14, tzinfo=timezone.utc)

def stamp(tick):
    return (START + timedelta(seconds=tick * 10)).strftime('%H:%M:%S')

class Simulation:
    def __init__(self):
        self.tick = 0
        self.running = False
        self.speed = 1
        self.selected = 'research-07'
        self.isolated = []
        self.patched = False
        self.remediated = False
        self.file_access = False
        self.beacons = 0
        self.integrity = []
        self.decoded = None
        self.correlated = False
        self.query_mode = 'unsafe'
        self.query_checked = False
        self.query_result = None
        self.hash_result = None
        self.hints = 0
        self.finished = False
        self.history = []
        self.journal = []
        self.trace = [{'tick': 0, 'suspicious': 0, 'routine': 3}]
        self.message = 'Select a host to inspect it. Start the simulation when you are ready.'
        self.events = [dict(time='09:14:00', kind='alert', host='research-07', text='New process sync_agent detected. Investigate before drawing conclusions.')]

    def active(self):
        return not self.remediated and 'research-07' not in self.isolated

    def event(self, kind, host, text):
        self.events.append(dict(time=stamp(self.tick), kind=kind, host=host, text=text))

    def record(self, action, detail):
        self.history.append(dict(time=stamp(self.tick), action=action, detail=detail))
        self.message = detail

    def dispatch(self, command, record=True):
        if not isinstance(command, dict):
            return
        action = command.get('type')
        if action == 'reset':
            self.__init__()
            return
        if action == 'restore':
            journal = command.get('journal')
            if not isinstance(journal, list) or len(journal) > 1500:
                self.message = 'Saved session could not be restored. Start a new simulation.'
                return
            candidate = Simulation()
            try:
                for entry in journal:
                    if not isinstance(entry, dict) or entry.get('type') in ('restore', 'reset'):
                        raise ValueError()
                    candidate.dispatch(entry)
            except (ValueError, TypeError, KeyError):
                self.message = 'Saved session could not be restored. Start a new simulation.'
                return
            candidate.running = False
            candidate.message = 'Saved decisions restored. The simulation is paused; press Resume when ready.'
            self.__dict__.update(candidate.__dict__)
            return
        allowed = {'play', 'pause', 'speed', 'tick', 'select', 'isolate', 'restore_host', 'scan', 'decode', 'correlate', 'query', 'patch', 'remediate', 'hint', 'finish', 'hash'}
        if action not in allowed:
            return
        if self.finished and action not in {'select', 'hash', 'pause'}:
            self.message = 'This attempt is complete. Review the debrief or reset to try another strategy.'
            return
        # Keep a replayable local record; transient selections/hash experiments do not affect the case.
        if record and action not in {'select', 'hash'}:
            self.journal.append(copy.deepcopy(command))
        if action == 'play':
            if self.tick < 72: self.running = True
            self.message = 'Simulation running. At 1×, each real second advances 10 simulated seconds. Pause whenever you need.'
        elif action == 'pause':
            self.running = False
            self.message = 'Paused. You can inspect evidence and make decisions without time pressure.'
        elif action == 'speed':
            self.speed = 4 if command.get('value') == 4 else 1
        elif action == 'tick':
            if not self.running: return
            for _ in range(self.speed):
                if self.tick >= 72:
                    self.running = False
                    break
                self.tick += 1
                suspicious = 0
                routine = 3 if not {'research-08', 'archive-01'}.intersection(self.isolated) else 0
                if self.tick % 6 == 0 and self.active():
                    self.beacons += 1
                    suspicious = 1
                    self.event('network', 'research-07', 'sync_agent → 203.0.113.77:443 · 128 bytes outbound')
                if self.tick % 18 == 0:
                    if self.patched or 'portal-01' in self.isolated:
                        self.event('blocked', 'portal-01', 'New malformed login rejected. Existing workstation process is unaffected.')
                    else:
                        self.event('alert', 'portal-01', 'Another malformed login was accepted. The portal still concatenates user input.')
                if self.tick == 54:
                    if self.active():
                        self.file_access = True
                        self.event('critical', 'research-07', 'sync_agent read watershed_private.csv. File access observed; exfiltration is not established.')
                    else:
                        self.event('blocked', 'research-07', 'Scheduled sensitive-file access prevented in this simulation.')
                if self.tick % 3 == 0:
                    self.trace.append(dict(tick=self.tick, suspicious=suspicious, routine=routine))
            if self.tick >= 72:
                self.running = False
                self.message = 'Scenario window ended. Finish your investigation and open the debrief; actions remain available.'
        elif action == 'select':
            host = command.get('host')
            if host in HOSTS: self.selected = host
        elif action in {'isolate', 'restore_host'}:
            host = command.get('host', self.selected)
            if host not in HOSTS: return
            if action == 'isolate' and host not in self.isolated:
                self.isolated.append(host)
                detail = f'{host} isolated. Its network activity stops, and its service is unavailable.'
                if host == 'research-07':
                    detail += ' In this simplified model, containment also prevents the scheduled file read; real network isolation alone does not stop local file access.'
                self.record('Contain host', detail)
                self.event('action', host, 'Analyst isolated this host.')
            elif action == 'restore_host' and host in self.isolated:
                self.isolated.remove(host)
                detail = f'{host} restored.'
                if host == 'research-07' and not self.remediated:
                    detail += ' sync_agent is still present; its communication can resume.'
                self.record('Restore service', detail)
                self.event('action', host, detail)
        elif action == 'scan':
            with (ROOT/'data/evidence_manifest.csv').open() as handle:
                self.integrity = []
                for row in csv.DictReader(handle):
                    digest = hashlib.sha256((ROOT/'data'/row['filename']).read_bytes()).hexdigest()
                    self.integrity.append(dict(filename=row['filename'], expected=row['expected_sha256'], actual=digest, matches=digest == row['expected_sha256']))
            self.record('Verify evidence', 'Integrity check complete: one file differs from the trusted baseline. A mismatch establishes change, not intent.')
        elif action == 'decode':
            filename = command.get('filename')
            if filename not in {'collector_config.txt', 'research_notes.txt', 'readme.txt'}: return
            try:
                decoded = base64.b64decode((ROOT/'data'/filename).read_bytes().strip(), validate=True).decode()
                self.decoded = json.loads(decoded)
                self.record('Decode artifact', 'Recovered an account, host and process. Verify those leads against the telemetry.')
            except (ValueError, UnicodeError):
                self.message = 'That file is not Base64 JSON. Compare the integrity results and try the modified artifact.'
        elif action == 'correlate':
            if not self.decoded:
                self.message = 'Decode the modified artifact first so you have a lead to test.'
            elif self.tick < 6:
                self.message = 'No outbound record has arrived yet. Run the simulation to at least 09:15, then compare the stream.'
            elif (command.get('host'), command.get('process'), command.get('destination')) == ('research-07','sync_agent','203.0.113.77') and self.beacons:
                self.correlated = True
                self.record('Correlate evidence', 'Host, process and destination match the decoded lead and observed traffic. Regularity alone was not sufficient evidence.')
            else:
                self.record('Recheck correlation', 'Those fields do not match an observed stream linked to the artifact. Compare host + process + destination; routine backups are also periodic.')
        elif action == 'query':
            mode = command.get('mode', 'unsafe')
            if mode not in {'unsafe', 'bound'}: return
            value = str(command.get('value', 'riley'))[:200]
            self.query_mode = mode
            with sqlite3.connect(':memory:') as db:
                db.execute('CREATE TABLE users (username TEXT)')
                db.executemany('INSERT INTO users VALUES (?)', [('riley',), ('jordan',), ("o'neil",)])
                try:
                    if mode == 'bound': rows = db.execute('SELECT username FROM users WHERE username = ?', (value,)).fetchall()
                    else: rows = db.execute("SELECT username FROM users WHERE username = '" + value + "'").fetchall()
                    self.query_result = dict(mode=mode, input=value, rows=[row[0] for row in rows], error=None)
                except sqlite3.Error:
                    self.query_result = dict(mode=mode, input=value, rows=[], error='The input broke the query syntax. Bound parameters treat punctuation as data.')
            if mode == 'bound':
                self.query_checked = True
                self.message = 'Bound parameters keep the input separate from SQL. Apply this repair to block new malformed logins.'
            else:
                self.message = 'Observe how input changes the result. Try the test payload, then compare bound parameters.'
        elif action == 'patch':
            if not self.query_checked:
                self.message = 'Test the bound-parameter design in the portal workbench before applying it.'
            elif not self.patched:
                self.patched = True
                self.record('Repair portal', 'Parameterized queries deployed. New malformed logins are blocked; the existing sync_agent process still needs containment.')
                self.event('action', 'portal-01', 'Input is now passed as bound parameters.')
        elif action == 'remediate':
            if 'research-07' not in self.isolated:
                self.message = 'Contain research-07 before removing the simulated process.'
            elif not (self.integrity and self.decoded and self.correlated):
                self.message = 'Preserve the evidence first: verify files, decode the artifact, and correlate an observed stream.'
            elif not self.remediated:
                self.remediated = True
                self.record('Remove process', 'Evidence preserved; simulated sync_agent removed. You can now restore research-07 without restarting its traffic.')
                self.event('action', 'research-07', 'Simulated process removed; no real system was modified.')
        elif action == 'hash':
            original = str(command.get('original', 'Research sample'))[:2000]
            changed = str(command.get('changed', 'research sample'))[:2000]
            a,b = [hashlib.sha256(s.encode()).hexdigest() for s in (original,changed)]
            self.hash_result = dict(original=a, changed=b, bits=sum((x^y).bit_count() for x,y in zip(bytes.fromhex(a),bytes.fromhex(b))))
        elif action == 'hint':
            self.hints += 1
            hints = ['Start with the trusted manifest. Which file changed?', 'Decode the changed file and compare its host and process with the network stream.', 'Observe at least one sync_agent connection, then preserve evidence, contain research-07, test bound parameters and apply the repair. Remove the process before restoring service.']
            self.message = hints[min(self.hints-1,2)]
        elif action == 'finish':
            self.running = False
            self.finished = True
            self.record('Close attempt', 'Attempt closed. Review the evidence, operational tradeoffs and next steps in your debrief.')

    def snapshot(self):
        penalties = {'research-07':25, 'research-08':20, 'portal-01':45, 'archive-01':10}
        availability = 100-sum(penalties[h] for h in self.isolated)
        contained = not self.active()
        goals = [dict(label='Verify collected files',done=bool(self.integrity)),dict(label='Decode the changed artifact',done=bool(self.decoded)),dict(label='Correlate an observed stream',done=self.correlated),dict(label='Contain or remove sync_agent',done=contained),dict(label='Repair the portal',done=self.patched)]
        evidence_score = sum(g['done'] for g in goals[:3])*20
        score = evidence_score + (15 if contained else 0) + (15 if self.patched else 0) + (10 if self.remediated and not self.isolated else 0)
        with (ROOT/'data/system_events.csv').open() as f:
            system = [r for r in csv.DictReader(f) if r['host']=='research-07' and r['timestamp']<='2026-09-14T09:14:00Z']
        return dict(tick=self.tick,time=stamp(self.tick),running=self.running,speed=self.speed,selected=self.selected,
            isolated=self.isolated,patched=self.patched,remediated=self.remediated,file_access=self.file_access,
            beacons=self.beacons,bytes_sent=self.beacons*128,availability=availability,contained=contained,
            integrity=self.integrity,decoded=self.decoded,correlated=self.correlated,query_result=self.query_result,
            query_checked=self.query_checked,hash_result=self.hash_result,hints=self.hints,finished=self.finished,
            trace=self.trace,events=self.events[-80:],history=self.history,goals=goals,score=score,
            message=self.message,system=system,journal=self.journal)
