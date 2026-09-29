"""Deterministic, fictional evidence; run only when intentionally rebuilding the lesson."""
import base64, csv, hashlib, json
from pathlib import Path
D = Path(__file__).parent / 'data'
def csvwrite(name, rows):
    with (D/name).open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def stamp(minute): return f'2026-09-14T09:{minute:02d}:00Z'
clean = {'research_notes.txt': b'Fictional research: watershed simulation v1.\n', 'collector_config.txt': b'collector=local; mode=inventory\n', 'readme.txt': b'Training evidence only. All timestamps UTC.\n'}
for name, data in clean.items(): (D/name).write_bytes(data)
csvwrite('evidence_manifest.csv', [{'filename':n,'expected_sha256':hashlib.sha256(b).hexdigest()} for n,b in clean.items()])
clue={'host':'research-07','username':'riley','process':'sync_agent','event_id':'SYS-042','note':'Compare process start with outbound connections; all times UTC.'}
(D/'collector_config.txt').write_text(base64.b64encode(json.dumps(clue).encode()).decode()+'\n')
auth=[dict(event_id=f'AUTH-{i:03}',timestamp=stamp(i),host='portal-01',username='jordan',event_type='login',source_ip='192.0.2.10',result='success',message='Routine training portal login') for i in range(0,30,3)]
auth += [dict(event_id='AUTH-041',timestamp=stamp(11),host='portal-01',username='riley',event_type='login',source_ip='198.51.100.23',result='success',message="query predicate accepted: username='riley' OR '1'='1'; linked session DEMO-7" )]
csvwrite('authentication_logs.csv',auth)
sys=[dict(event_id=f'SYS-{i:03}',timestamp=stamp(i),host='research-08',username='jordan',event_type='process_start',process='backup_agent',message='Scheduled backup') for i in range(0,30,5)]
sys += [dict(event_id=e,timestamp=stamp(t),host='research-07',username='riley',event_type=k,process=p,message=m) for e,t,k,p,m in [('SYS-040',12,'job_started','portal_worker','Session DEMO-7 invoked research job runner on research-07'),('SYS-041',13,'file_write','portal_worker','Replaced collector_config.txt; session DEMO-7'),('SYS-042',14,'process_start','sync_agent','Loaded collector_config.txt; session DEMO-7'),('SYS-043',23,'file_read','sync_agent','Read fictional sensitive dataset watershed_private.csv; session DEMO-7')]]
csvwrite('system_events.csv',sys)
net=[]
for i in range(30):
    net.append(dict(timestamp=stamp(i),host='research-08',process='backup_agent',source_ip='192.0.2.18',destination_ip='192.0.2.200',destination_port=443,protocol='TCP',bytes_sent=5000+i*31))
    if i%3==0: net.append(dict(timestamp=stamp(i),host='research-07',process='browser',source_ip='192.0.2.17',destination_ip='203.0.113.80',destination_port=443,protocol='TCP',bytes_sent=900+i))
    if i%5==0: net.append(dict(timestamp=stamp(i),host='research-07',process='resolver',source_ip='192.0.2.17',destination_ip='192.0.2.53',destination_port=53,protocol='UDP',bytes_sent=70))
for i in range(15,23): net.append(dict(timestamp=stamp(i),host='research-07',process='sync_agent',source_ip='192.0.2.17',destination_ip='203.0.113.77',destination_port=443,protocol='TCP',bytes_sent=128))
csvwrite('network_traffic.csv',net)
(D/'application_example.py').write_text('''# Fictional portal lookup: query output grants a session in this toy application.
# The dataset records a separate job-runner action after the session was granted.
def lookup_user(connection, username):
    query = "SELECT username FROM users WHERE username = '" + username + "'"
    return connection.execute(query).fetchall()
''')
