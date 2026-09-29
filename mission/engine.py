"""Guided Watershed mission: one step at a time, no clock. No sockets, subprocesses or real host actions.

All student-facing wording lives in STEPS (lesson text) and HOST_INFO / PROCESSES (what students inspect),
so an instructor can edit the lesson without touching the UI.
"""
import base64
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'portal-01': 'Research portal', 'research-07': 'Research 07',
         'research-08': 'Research 08', 'archive-01': 'Data archive'}
SUSPICIOUS = {'research-07'}
# Share of the research service each host provides (illustrative).
SERVICE = {'research-07': 25, 'research-08': 20, 'portal-01': 45, 'archive-01': 10}
FILES = ['research_notes.txt', 'collector_config.txt', 'readme.txt']
CHANGED_FILE = 'collector_config.txt'
HASH_SAMPLE = 'Research sample'
CLUE_SLOTS = [('host', 'Computer'), ('username', 'User account'), ('process', 'Program')]
DESTINATIONS = ['192.0.2.200', '192.0.2.53', '203.0.113.80', '203.0.113.77']

HOST_INFO = {
    'portal-01': dict(job='Website researchers log in to. Starts research jobs on Research 07.', since='Installed 2023',
                      connections=[dict(program='web_portal', to='Research 07', where='inside', note='Starts research jobs when a researcher asks')]),
    'research-07': dict(job='Workstation where researchers run watershed models.', since='Installed 2024',
                        connections=[dict(program='browser', to='203.0.113.80 (university library website)', where='outside', note='Known website, used every day'),
                                     dict(program='resolver', to='192.0.2.53 (lab name server)', where='inside', note='Looks up website names, normal'),
                                     dict(program='sync_agent', to='203.0.113.77 (unknown)', where='outside', note='First seen today at 09:14. Nobody on the team recognizes it')]),
    'research-08': dict(job='Backs up research data to the Data archive.', since='Installed 2024',
                        connections=[dict(program='backup_agent', to='192.0.2.200 (Data archive)', where='inside', note='Every minute, as scheduled by IT')]),
    'archive-01': dict(job='Stores the lab\'s research data and backups.', since='Installed 2022',
                       connections=[dict(program='file_server', to='(only receives traffic)', where='inside', note='Accepts backups from Research 08')]),
}
PROCESSES = [
    dict(name='explorer', what='Desktop and file windows', since='Started 08:02 by riley'),
    dict(name='browser', what='Web browser', since='Started 08:15 by riley'),
    dict(name='resolver', what='Looks up website names', since='System service, started at boot'),
    dict(name='portal_worker', what='Runs jobs sent from the Research portal', since='System service, started at boot'),
    dict(name='sync_agent', what='(no description)', since='Started 09:14, loaded collector_config.txt'),
]
CONFIG_OPTIONS = [
    ('delete', 'Delete collector_config.txt'),
    ('restore', 'Replace it with the trusted copy from the lab backup'),
    ('keep', 'Leave it as it is'),
]
FORMAT_OPTIONS = [
    ('encrypted', 'Encrypted. We need a secret key to read it.'),
    ('base64', 'Base64 encoded. Only letters, digits, + and /, and it ends in =.'),
    ('garbage', 'Random, corrupted data. It can\'t be read.'),
]

STEPS = [
    dict(id='briefing', short='Briefing', title='You are the analyst on call',
         story='It is Monday morning at the Watershed Research Lab. The security system flagged a new program on one of the research computers. Your job is to find out what is going on, stop it, and get the lab back to normal without breaking anything that works.',
         learning='How a security analyst works through an incident: watch, gather evidence, confirm, contain, fix, and recover.',
         why='Real incidents are solved by following a careful order. Jumping to conclusions can shut down the wrong system or destroy the evidence you need.',
         learned='', learned_why='', check=None),
    dict(id='observe', short='Observe', title='Step 1 · Spot the unusual traffic',
         story='Every computer on the map talks to other computers. Most of that traffic is normal. Something new is also talking. Inspect each computer and decide which one needs investigating.',
         learning='How to tell normal network traffic apart from traffic that needs a closer look.',
         why='Analysts watch before they act. You cannot judge what is unusual until you know what normal looks like.',
         learned='Three computers only do their usual jobs. Research 07 is running a new program, sync_agent, first seen today and sending data to an address nobody recognizes. Research 07\'s browser also talks outside the lab, but to a known website it uses every day.',
         learned_why='"Leaving the lab" or "happening on a schedule" is not proof of anything. What made Research 07 stand out was something new and unexplained, compared with what normally happens.',
         check=dict(question='Research 07\'s browser also sends traffic outside the lab. Why didn\'t that make it suspicious?',
                    options=['Browsers cannot be hacked.', 'It goes to a known website the lab uses every day, so it matches normal behavior.', 'It sends less data than the backup.'],
                    answer=1, explain='Analysts compare against a baseline of normal behavior. Known, expected traffic is normal even when it leaves the network.')),
    dict(id='integrity', short='Verify', title='Step 2 · Check if the evidence was changed',
         story='Before the incident, the lab saved a trusted list of fingerprints (called hashes) for three files on Research 07. Compute today\'s fingerprints and compare them yourself.',
         learning='What a hash is and how it proves whether a file has been changed.',
         why='If you cannot trust your evidence, you cannot trust your conclusions. Investigators check evidence before relying on it, and courts expect the same.',
         learned='A hash is a fingerprint made from a file\'s exact contents. Changing one letter changed almost the whole fingerprint, and only the exact original text brought it back. collector_config.txt no longer matches its trusted fingerprint.',
         learned_why='A mismatch proves the file was changed. It does not tell you who changed it or why. That is what the next step is for.',
         check=dict(question='A file\'s hash no longer matches the trusted list. What does that prove?',
                    options=['The file is a virus.', 'The file was changed since the trusted list was made.', 'Someone encrypted the file.'],
                    answer=1, explain='A hash mismatch proves only that the contents changed. Finding out what changed and why takes more evidence.')),
    dict(id='decode', short='Decode', title='Step 3 · Decode the clue',
         story='The changed file looks like scrambled text. Open it, work out what kind of text it is, and pull out the clues hidden inside.',
         learning='The difference between encoding (anyone can reverse it) and encryption (you need a secret key).',
         why='Attackers often hide instructions in encoded text because it looks like gibberish at a glance. Recognizing encoding lets you read what they left behind.',
         learned='You recognized Base64 by its alphabet (letters, digits, + and /, with = at the end), and it decoded instantly with no key. The hidden note names a computer (research-07), a user account (riley), and a program (sync_agent).',
         learned_why='Encoding only changes how data looks. It does not protect it. Encryption uses a secret key, so without the key you cannot read it. Never mistake encoded data for protected data.',
         check=dict(question='Did you need a secret key to decode the Base64 text?',
                    options=['Yes, Base64 is a type of encryption.', 'No. Base64 is encoding, and anyone can reverse it.', 'Only for the first few characters.'],
                    answer=1, explain='Base64 is encoding. It hides nothing from anyone who knows to decode it. Encryption is what requires a key.')),
    dict(id='correlate', short='Connect', title='Step 4 · Connect the dots',
         story='The clue names a computer and a program. The lab\'s network log has 54 records from this morning. Filter the log using the clue and find out where that program is sending data.',
         learning='Correlation: confirming a finding by matching details from two independent sources.',
         why='One piece of evidence can be misleading. When a file clue and the network log point to the same computer, program and destination, your finding becomes much stronger.',
         learned='Filtering by research-07 still left three programs. Adding sync_agent narrowed 54 records to 8: a small message to 203.0.113.77 every minute, starting at 09:15, one minute after sync_agent started.',
         learned_why='You now have two independent sources that agree: a changed file and the network log. That is enough to act. Notice it still does not prove what data was sent.',
         check=dict(question='Why check the clue against the network log instead of trusting the file alone?',
                    options=['Two independent sources agreeing makes the finding much stronger.', 'The file might be too long to read.', 'Network logs are always correct.'],
                    answer=0, explain='Any single source can be wrong, incomplete or planted. Agreement between independent sources is what builds a solid case.')),
    dict(id='contain', short='Contain', title='Step 5 · Stop the spread',
         story='You have confirmed that sync_agent on Research 07 is sending data outside the lab. Contain it by isolating computers from the network, then test that it worked. Every isolated computer also stops doing its normal job.',
         learning='Containment, and the tradeoff between security and keeping services running.',
         why='Pulling every plug stops the attack but also stops the lab\'s work. Good responders contain the smallest area that stops the threat, then confirm it worked.',
         learned='Isolating only Research 07 stopped the suspicious traffic and kept 75% of the lab running. The connection test confirmed that sync_agent can no longer reach 203.0.113.77.',
         learned_why='Containment is a balance: stop the threat while keeping as much normal work going as possible. Always verify. An action you did not test is an action you are only hoping worked.',
         check=dict(question='Research 07 is now isolated. Is sync_agent gone?',
                    options=['Yes. Isolating a computer deletes the bad program.', 'No. Isolation cuts its network connection, but the program is still on the computer.', 'Yes, but only until someone restarts it.'],
                    answer=1, explain='Isolation is like closing a door. The program is still inside. You remove it later, in the recovery step.')),
    dict(id='repair', short='Repair', title='Step 6 · Close the way in',
         story='How did the attacker get in? The login log shows something strange on the research portal just before sync_agent appeared. The portal builds a database question (a SQL query) by pasting in whatever the user types. Reproduce the attack, then test the fix.',
         learning='SQL injection, and how parameterized queries (keeping user input separate from commands) prevent it.',
         why='If you remove the attacker but leave the door open, they can walk right back in. Fixing the way in is part of every recovery.',
         learned='On the original portal, the attacker\'s text changed the query itself and matched every account. The fixed portal treated the same text as a plain name and matched nobody, and a real name with an apostrophe (o\'neil) still worked.',
         learned_why='Never let user input become part of a command. Parameterized queries keep what the user typed ("data") separate from what the program runs ("instructions"), without breaking real users.',
         check=dict(question='Why does the fixed portal ignore the attack text?',
                    options=['It blocks every name that contains punctuation.', 'It sends the input separately, so the database treats it only as a name and never as part of the command.', 'It asks the user for a second password.'],
                    answer=1, explain='Parameterized queries keep data and instructions apart. That is also why o\'neil still works.')),
    dict(id='recover', short='Recover', title='Step 7 · Clean up and recover',
         story='The threat is contained and the way in is closed. Clean Research 07 while it is still isolated, then bring it back and confirm the lab is healthy.',
         learning='Recovery order: remove the threat and anything it changed, then reconnect and confirm.',
         why='Reconnecting a computer before it is fully cleaned lets the threat pick up right where it left off.',
         learned='You ended only sync_agent, put the trusted copy of collector_config.txt back so nothing could reload the attacker\'s version, reconnected Research 07, and confirmed no traffic to 203.0.113.77. The lab is back to 100%.',
         learned_why='Clean everything the attacker touched, not just the program you noticed. Then restore service and check that the problem is really gone.',
         check=dict(question='Why put back the trusted copy of collector_config.txt instead of deleting it?',
                    options=['Deleting files is against the rules.', 'The lab\'s real data collector needs that file. The trusted copy removes the attacker\'s changes without breaking it.', 'It doesn\'t matter once sync_agent is gone.'],
                    answer=1, explain='Recovery means returning to a known-good state. Deleting would break the collector, and leaving it would let the attacker\'s settings be reloaded.')),
    dict(id='debrief', short='Debrief', title='Mission complete · What you learned',
         story='You worked a full incident from first alert to recovery.',
         learning='', why='', learned='', learned_why='', check=None),
]


def load_network():
    with (ROOT / 'data/network_traffic.csv').open() as handle:
        rows = [dict(time=r['timestamp'][11:16], host=r['host'], process=r['process'], destination=r['destination_ip'],
                     bytes=int(r['bytes_sent'])) for r in csv.DictReader(handle)]
    return sorted(rows, key=lambda r: (r['time'], r['host'], r['process']))


class Mission:
    def __init__(self):
        self.step = 0
        self.done = {s['id']: False for s in STEPS}
        self.checked = {s['id']: False for s in STEPS}
        self.picked_answer = None
        self.feedback = None
        self.history = []
        # observe
        self.observed = False
        self.inspecting = None
        self.inspected = []
        self.labels = {}
        # integrity
        self.integrity = []
        self.verdicts = {}
        self.hash_input = HASH_SAMPLE
        self.hash_changed = False
        self.hash_restored = False
        # decode
        self.opened = None
        self.format_ok = False
        self.decoded = None
        self.clues = {}
        # correlate
        self.filter_host = ''
        self.filter_process = ''
        self.destination = None
        # contain
        self.isolated = []
        self.verify_result = None
        # repair
        self.portal_mode = 'unsafe'
        self.last_query = None
        self.repair_flags = dict(normal=False, attack=False, fixed_attack=False, apostrophe=False)
        self.attack_misses = 0
        self.patched = False
        # recover
        self.killed = False
        self.config = None
        self.reconnected = False
        self.confirmed = False

    # ---- helpers -------------------------------------------------------
    def current(self):
        return STEPS[self.step]

    def say(self, tone, text):
        self.feedback = dict(tone=tone, text=text)

    def log(self, text):
        self.history.append(dict(step=self.current()['short'], text=text))

    def availability(self):
        return 100 - sum(SERVICE[h] for h in self.isolated)

    def finish_if_done(self, summary):
        sid = self.current()['id']
        if not self.done[sid] and self.tasks() and all(d for _, d in self.tasks()):
            self.done[sid] = True
            self.log(summary)
            self.say('good', 'Task complete! Scroll down to read what you learned and answer the quick check.')

    def run_query(self, mode, value):
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE TABLE users (username TEXT)')
            db.executemany('INSERT INTO users VALUES (?)', [('riley',), ('jordan',), ("o'neil",)])
            try:
                if mode == 'bound':
                    rows = db.execute('SELECT username FROM users WHERE username = ?', (value,)).fetchall()
                else:
                    rows = db.execute("SELECT username FROM users WHERE username = '" + value + "'").fetchall()
                return [r[0] for r in rows], None
            except sqlite3.Error:
                return [], 'The database could not understand the command. An extra quote mark broke it.'

    def network_rows(self):
        rows = load_network()
        if self.filter_host:
            rows = [r for r in rows if r['host'] == self.filter_host]
        if self.filter_process:
            rows = [r for r in rows if r['process'] == self.filter_process]
        return rows

    # ---- actions -------------------------------------------------------
    def dispatch(self, command):
        if not isinstance(command, dict):
            return
        action = command.get('type')
        sid = self.current()['id']
        if action == 'reset':
            self.__init__()
            return
        if action == 'next':
            if sid == 'briefing' or (self.done[sid] and self.checked[sid]):
                if self.step < len(STEPS) - 1:
                    self.step += 1
                    self.feedback = None
                    self.picked_answer = None
            else:
                self.say('try', 'Finish the task and the quick check first.')
            return
        if action == 'answer':
            check = self.current().get('check')
            if not check or not self.done[sid]:
                return
            choice = command.get('choice')
            if not isinstance(choice, int) or not 0 <= choice < len(check['options']):
                return
            self.picked_answer = choice
            if choice == check['answer']:
                self.checked[sid] = True
                self.say('good', 'Correct. ' + check['explain'])
            else:
                self.say('try', 'Not quite. ' + check['explain'] + ' Try again.')
            return
        # Once a step's task is complete its stage is locked, so later clicks cannot undo the result.
        if self.done.get(sid):
            return
        handler = getattr(self, f'_{sid}', None)
        if handler:
            handler(action, command)

    def _observe(self, action, command):
        if action == 'observe':
            self.observed = True
            self.say('info', 'Traffic is flowing. Click each computer on the map to inspect what it is doing.')
        elif action == 'inspect' and self.observed:
            host = command.get('host')
            if host not in HOSTS:
                return
            self.inspecting = host
            if host not in self.inspected:
                self.inspected.append(host)
            left = len(HOSTS) - len(self.inspected)
            self.say('info', f'Read what {HOSTS[host]} is doing, then label it below the map.' + (f' {left} computer{"s" if left != 1 else ""} left to inspect.' if left else ''))
        elif action == 'label':
            host, verdict = command.get('host'), command.get('verdict')
            if host not in self.inspected or verdict not in ('normal', 'suspicious'):
                return
            correct = (verdict == 'suspicious') == (host in SUSPICIOUS)
            self.labels[host] = verdict
            if correct:
                self.say('good', f'Right: {HOSTS[host]} labeled {"needs investigation" if verdict == "suspicious" else "normal"}.')
            elif host == 'research-07':
                self.say('try', 'Look again at Research 07\'s programs. One of them is brand new today and talks to an address nobody recognizes.')
            elif host == 'research-08':
                self.say('try', 'Research 08 sends data every minute, but IT scheduled that backup and it goes to the lab\'s own archive. Regular is not the same as suspicious.')
            else:
                self.say('try', f'Everything {HOSTS[host]} does matches its usual job. Nothing new or unexplained.')
            self.finish_if_done('Inspected all four computers and flagged Research 07 (new sync_agent talking to an unknown address).')

    def _integrity(self, action, command):
        if action == 'scan':
            with (ROOT / 'data/evidence_manifest.csv').open() as handle:
                self.integrity = []
                for row in csv.DictReader(handle):
                    digest = hashlib.sha256((ROOT / 'data' / row['filename']).read_bytes()).hexdigest()
                    self.integrity.append(dict(filename=row['filename'], expected=row['expected_sha256'],
                                               actual=digest, matches=digest == row['expected_sha256']))
            self.say('info', 'Today\'s fingerprints are ready. Compare each one with the trusted fingerprint and mark the file Matches or Changed.')
        elif action == 'verdict' and self.integrity:
            name, verdict = command.get('filename'), command.get('verdict')
            record = next((f for f in self.integrity if f['filename'] == name), None)
            if not record or verdict not in ('match', 'changed'):
                return
            if (verdict == 'match') == record['matches']:
                self.verdicts[name] = verdict
                self.say('good', f'Correct: {name} {"matches" if verdict == "match" else "has changed"}.')
            else:
                self.verdicts.pop(name, None)
                self.say('try', f'Look again at {name}. Compare the two fingerprints character by character. The first few characters are enough to spot a difference.')
        elif action == 'hash':
            self.hash_input = str(command.get('text', ''))[:200]
            if self.hash_input != HASH_SAMPLE:
                if not self.hash_changed:
                    self.say('info', 'Almost every character changed! Now make the two fingerprints match again.')
                self.hash_changed = True
            elif self.hash_changed and not self.hash_restored:
                self.hash_restored = True
                self.say('good', 'The fingerprints match again. Only the exact original text gives the original fingerprint.')
        self.finish_if_done('Compared fingerprints: collector_config.txt no longer matches its trusted fingerprint.')

    def _decode(self, action, command):
        if action == 'open':
            name = command.get('filename')
            if name not in FILES:
                return
            if name != CHANGED_FILE:
                self.say('try', f'{name} matched its trusted fingerprint in Step 2, so it has not changed. Open the file that did change.')
                return
            self.opened = name
            self.say('info', 'Here is what the file contains. Look at which characters it uses, then decide what kind of text this is.')
        elif action == 'format' and self.opened:
            choice = command.get('choice')
            if choice == 'base64':
                self.format_ok = True
                self.decoded = json.loads(base64.b64decode((ROOT / 'data' / self.opened).read_bytes().strip(), validate=True))
                self.say('info', 'Decoded, with no key needed! Now click the values in the decoded text to fill in each clue.')
            elif choice == 'encrypted':
                self.say('try', 'Encrypted data usually uses every possible byte and looks like random symbols. This uses only letters, digits, + and /, and ends in =. That pattern is a giveaway.')
            elif choice == 'garbage':
                self.say('try', 'Corrupted data would not be this tidy. Every character comes from a 64-character alphabet, and it ends in = padding.')
        elif action == 'clue' and self.decoded:
            key = command.get('key')
            slot = next((k for k, _ in CLUE_SLOTS if k not in self.clues), None)
            if slot is None or key not in self.decoded:
                return
            label = dict(CLUE_SLOTS)[slot]
            if key == slot:
                self.clues[slot] = self.decoded[slot]
                self.say('good', f'{label}: {self.decoded[slot]}.')
            else:
                self.say('try', f'That value is the {key.replace("_", " ")}, not the {label.lower()}. Look for the field named "{slot}".')
        self.finish_if_done('Decoded the Base64 note: research-07, user riley, program sync_agent.')

    def _correlate(self, action, command):
        if action == 'filter':
            host, process = command.get('host', ''), command.get('process', '')
            if host not in ('', *HOSTS) or process not in ('', *{r['process'] for r in load_network()}):
                return
            self.filter_host, self.filter_process = host, process
            n = len(self.network_rows())
            if host and host != self.decoded_host():
                self.say('try', f'{n} records, but the clue names a different computer. Check the clue card.')
            elif process and process != self.decoded_process():
                self.say('try', f'{n} records, but that is not the program the clue names.')
            elif host and not process:
                self.say('info', f'{n} records from research-07, but it runs several programs. Narrow it down with the Program filter.')
            elif host and process:
                self.say('info', f'Down to {n} records. Where is this program sending data?')
            else:
                self.say('info', f'{n} records shown. Use the filters to narrow them down.')
        elif action == 'destination':
            ip = command.get('ip')
            if ip not in DESTINATIONS:
                return
            if not (self.filter_host == self.decoded_host() and self.filter_process == self.decoded_process()):
                self.say('try', 'Filter the log to the clue\'s computer AND program first, so you are looking at the right records.')
                return
            self.destination = ip
            if ip == '203.0.113.77':
                self.say('good', 'Correct: sync_agent sends to 203.0.113.77, the unknown address from Step 1.')
            else:
                self.say('try', f'None of the filtered records go to {ip}. Read the "Sending to" column.')
        self.finish_if_done('Filtered the network log to research-07 + sync_agent: 8 messages to 203.0.113.77, every minute from 09:15.')

    def decoded_host(self):
        return (self.decoded or {}).get('host', 'research-07')

    def decoded_process(self):
        return (self.decoded or {}).get('process', 'sync_agent')

    def _contain(self, action, command):
        if action == 'toggle':
            host = command.get('host')
            if host not in HOSTS:
                return
            if host in self.isolated:
                self.isolated.remove(host)
            else:
                self.isolated.append(host)
            self.verify_result = None
            others = [h for h in self.isolated if h != 'research-07']
            if 'research-07' in self.isolated and others:
                self.say('try', f'The lab is down to {self.availability()}%. {", ".join(HOSTS[h] for h in others)} had nothing to do with the threat. Click to reconnect.')
            elif others:
                self.say('try', f'Service dropped to {self.availability()}%, but sync_agent is on Research 07, which is still connected. That cost service without stopping the threat.')
            elif 'research-07' in self.isolated:
                self.say('info', f'Research 07 is isolated and {self.availability()}% of the lab is still running. Now test whether it worked.')
            else:
                self.say('info', 'Click a computer to isolate it. Click it again to reconnect.')
        elif action == 'verify':
            blocked = 'research-07' in self.isolated
            self.verify_result = dict(blocked=blocked, others_ok=[h for h in HOSTS if h not in self.isolated])
            if blocked and len(self.isolated) == 1:
                self.say('good', 'Test passed: sync_agent tried to reach 203.0.113.77 and was blocked. Everything else is still working.')
            elif blocked:
                self.say('try', 'sync_agent is blocked, but you also cut off computers the lab needs. Reconnect them and test again.')
            else:
                self.say('try', 'Test failed: sync_agent still reached 203.0.113.77. Isolate the computer it is running on.')
        self.finish_if_done('Isolated only Research 07 (75% of the lab still running) and verified sync_agent is blocked.')

    def _repair(self, action, command):
        if action == 'mode':
            mode = command.get('mode')
            if mode in ('unsafe', 'bound'):
                self.portal_mode = mode
                self.last_query = None
        elif action == 'login':
            value = str(command.get('value', ''))[:80]
            if not value.strip():
                self.say('try', 'Type something into the username box first.')
                return
            rows, error = self.run_query(self.portal_mode, value)
            injected = "'" in value and (' or ' in value.lower() or '--' in value)
            self.last_query = dict(mode=self.portal_mode, input=value, rows=rows, error=error)
            f = self.repair_flags
            if self.portal_mode == 'unsafe':
                if len(rows) > 1:
                    f['attack'] = True
                    self.say('good', f'Attack reproduced: {len(rows)} accounts matched. Your text changed the command itself.')
                elif error and value == "o'neil":
                    self.say('info', 'The original portal breaks on a real name with a quote mark in it! The quote ended the name early. Keep that in mind for the fixed portal.')
                elif error:
                    self.attack_misses += 1
                    self.say('info', 'Your quote mark broke the command. The attacker added more after the quote to make the command always true. Check the login log.')
                elif len(rows) == 1 and "'" not in value:
                    f['normal'] = True
                    self.say('info', 'A normal name finds exactly one account. That is what the portal is supposed to do. Now try what the attacker typed.')
                else:
                    self.attack_misses += 1
                    self.say('info', 'No accounts matched. Look at the login log to see exactly what the attacker typed.')
            else:
                if injected and not rows:
                    f['fixed_attack'] = True
                    self.say('good', 'Same attack, zero matches. The fixed portal treated it as a strange name, not a command.')
                elif value == "o'neil":
                    f['apostrophe'] = True
                    self.say('good', 'o\'neil logs in fine. The fix protects the portal without breaking names that contain a quote mark.')
                elif rows:
                    self.say('info', 'A normal name still works with the fix. Now try the attack text, and the name o\'neil.')
                else:
                    self.say('info', 'No match. Try the attack text, and the name o\'neil (which broke the original portal).')
        elif action == 'hint':
            self.attack_misses = max(self.attack_misses, 2)
            self.say('info', 'Hint: copy the text after username= in the log: riley\' OR \'1\'=\'1')
        elif action == 'patch':
            f = self.repair_flags
            if not (f['fixed_attack'] and f['apostrophe']):
                self.say('try', 'Test the fixed portal first: it should block the attack AND still let o\'neil log in. Apply a fix only after you know it works.')
            else:
                self.patched = True
        self.finish_if_done('Reproduced the SQL injection, verified the parameterized fix (blocks the attack, o\'neil still works), and applied it.')

    def _recover(self, action, command):
        if action == 'kill':
            name = command.get('process')
            if name not in [p['name'] for p in PROCESSES]:
                return
            if name == 'sync_agent':
                self.killed = True
                self.say('info', 'sync_agent is gone. But it was loading its settings from a changed file. Deal with collector_config.txt next.')
            else:
                what = next(p['what'] for p in PROCESSES if p['name'] == name)
                self.say('try', f'{name} is a normal program ({what.lower()}). Ending it would disrupt the researcher without removing the threat.')
        elif action == 'config':
            choice = command.get('choice')
            if choice not in dict(CONFIG_OPTIONS):
                return
            if not self.killed:
                self.say('try', 'End sync_agent first. It is still running and could rewrite the file.')
            elif choice == 'restore':
                self.config = 'restore'
                self.say('info', 'Trusted copy restored. Its fingerprint matches the trusted list again. Research 07 is clean, so reconnect it.')
            elif choice == 'delete':
                self.say('try', 'The lab\'s real data collector needs that file, so deleting it would break normal research. Is there a known-good version you can use?')
            else:
                self.say('try', 'The file still holds the attacker\'s settings. Anything that reads it could restart the attack.')
        elif action == 'reconnect':
            if not (self.killed and self.config == 'restore'):
                self.say('try', 'Not yet. Research 07 is not fully clean. Reconnecting now could let the attack pick up where it left off.')
                return
            self.reconnected = True
            if 'research-07' in self.isolated:
                self.isolated.remove('research-07')
            self.say('info', f'Research 07 is back online and the lab is at {self.availability()}%. Run a final check to confirm the threat is gone.')
        elif action == 'confirm':
            if not self.reconnected:
                self.say('try', 'Reconnect Research 07 first, then check that its traffic is normal.')
                return
            self.confirmed = True
        self.finish_if_done('Ended sync_agent, restored the trusted collector_config.txt, reconnected Research 07 and confirmed no traffic to 203.0.113.77.')

    # ---- state for the browser ------------------------------------------
    def tasks(self):
        sid = self.current()['id']
        f = self.repair_flags
        return {
            'observe': [('Click “Show network traffic.”', self.observed),
                        (f'Click each computer on the map to inspect it ({len(self.inspected)}/4).', len(self.inspected) == 4),
                        (f'Label every computer “Normal” or “Needs investigation” ({sum((v == "suspicious") == (h in SUSPICIOUS) for h, v in self.labels.items())}/4 correct).',
                         len(self.labels) == 4 and all((v == 'suspicious') == (h in SUSPICIOUS) for h, v in self.labels.items()))],
            'integrity': [('Click “Compute today’s fingerprints.”', bool(self.integrity)),
                          (f'Compare each file’s two fingerprints and mark it Matches or Changed ({len(self.verdicts)}/3).', len(self.verdicts) == 3),
                          ('In the fingerprint tester, change one character.', self.hash_changed),
                          ('Then make the two fingerprints match again.', self.hash_restored)],
            'decode': [('Open the file that changed in Step 2.', bool(self.opened)),
                       ('Decide what kind of text it is.', self.format_ok),
                       (f'Click the decoded values to fill in the clue card ({len(self.clues)}/3).', len(self.clues) == 3)],
            'correlate': [('Filter the log to the clue’s computer.', self.filter_host == self.decoded_host()),
                          ('Also filter to the clue’s program.', self.filter_host == self.decoded_host() and self.filter_process == self.decoded_process()),
                          ('Pick where that program is sending data.', self.destination == '203.0.113.77')],
            'contain': [('Isolate the computer running sync_agent.', 'research-07' in self.isolated),
                        ('Keep every other computer online.', 'research-07' in self.isolated and len(self.isolated) == 1),
                        ('Click “Test the connection” to prove it worked.', bool(self.verify_result and self.verify_result['blocked'] and len(self.isolated) == 1))],
            'repair': [('ORIGINAL portal: log in with a normal name (try riley).', f['normal']),
                       ('ORIGINAL portal: type what the attacker typed (see the login log) so that more than one account matches.', f['attack']),
                       ('FIXED portal: try the same attack. It should match no one.', f['fixed_attack']),
                       ('FIXED portal: make sure the real user o\'neil can still log in.', f['apostrophe']),
                       ('Click “Apply the fix to the portal.”', self.patched)],
            'recover': [('End the program that does not belong on Research 07.', self.killed),
                        ('Decide what to do with the changed collector_config.txt.', self.config == 'restore'),
                        ('Reconnect Research 07.', self.reconnected),
                        ('Run a final traffic check.', self.confirmed)],
        }.get(sid, [])

    def snapshot(self):
        step = dict(self.current())
        sid = step['id']
        step['tasks'] = [dict(text=t, done=d) for t, d in self.tasks()]
        network = self.network_rows() if sid == 'correlate' else []
        all_rows = load_network() if sid == 'correlate' else []
        return dict(
            step_index=self.step, step=step,
            steps=[dict(id=s['id'], short=s['short'], done=self.done[s['id']] and self.checked[s['id']]) for s in STEPS],
            task_done=self.done[sid], check_passed=self.checked[sid], picked_answer=self.picked_answer,
            feedback=self.feedback, history=self.history,
            # observe
            observed=self.observed, inspecting=self.inspecting, inspected=self.inspected, labels=self.labels, host_info=HOST_INFO,
            # integrity
            integrity=self.integrity, verdicts=self.verdicts, files=FILES,
            hash_input=self.hash_input, hash_sample=HASH_SAMPLE,
            hash_digest=hashlib.sha256(self.hash_input.encode()).hexdigest(),
            sample_digest=hashlib.sha256(HASH_SAMPLE.encode()).hexdigest(),
            # decode
            opened=self.opened, format_ok=self.format_ok, format_options=FORMAT_OPTIONS,
            encoded=(ROOT / 'data' / CHANGED_FILE).read_text().strip(), decoded=self.decoded,
            clues=self.clues, clue_slots=CLUE_SLOTS,
            # correlate
            filter_host=self.filter_host, filter_process=self.filter_process, network=network, network_total=len(all_rows),
            hosts=list(HOSTS), processes=sorted({r['process'] for r in all_rows}), destinations=DESTINATIONS, destination=self.destination,
            # contain
            isolated=self.isolated, availability=self.availability(), service=SERVICE, verify_result=self.verify_result,
            # repair
            portal_mode=self.portal_mode, last_query=self.last_query, attack_misses=self.attack_misses, patched=self.patched,
            # recover
            process_list=PROCESSES, killed=self.killed, config=self.config, config_options=CONFIG_OPTIONS,
            reconnected=self.reconnected, confirmed=self.confirmed,
            threat_active=not self.killed and 'research-07' not in self.isolated,
            recap=[dict(title=s['title'].split(' · ')[-1], learned=s['learned'], why=s['learned_why']) for s in STEPS if s['learned']],
        )
