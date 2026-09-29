import base64, hashlib, json, shutil, sys, zipfile
from pathlib import Path
import nbformat
from nbclient import NotebookClient
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab import Investigation, code_checks, load_table, hash_lab, artifact_lab, explorer, instructor_panel
from package_student import package

def secure(conn,name): return conn.execute('SELECT username FROM users WHERE username = ?', (name,)).fetchall()
def unsafe(conn,name): return conn.execute("SELECT username FROM users WHERE username = '"+name+"'").fetchall()
@pytest.fixture
def case(tmp_path): return Investigation(tmp_path/'session.json')

def test_evidence_chain_and_completion(case):
    manifest=load_table('evidence_manifest.csv')
    changed=[r.filename for r in manifest.itertuples() if hashlib.sha256((ROOT/'data'/r.filename).read_bytes()).hexdigest()!=r.expected_sha256]
    assert len(changed)==1
    clue=json.loads(base64.b64decode((ROOT/'data'/changed[0]).read_bytes()))
    logs=load_table('system_events.csv')
    event=logs[(logs.host==clue['host'])&(logs.username==clue['username'])&(logs.process==clue['process'])&(logs.event_type=='process_start')]
    assert len(event)==1
    net=load_table('network_traffic.csv')
    selected=net[(net.host==clue['host'])&(net.process==clue['process'])&(net.timestamp>event.iloc[0].timestamp)]
    assert selected.destination_ip.nunique()==1 and len(selected)==8
    assert selected.timestamp.sort_values().diff().dropna().dt.total_seconds().eq(60).all()
    answers=[changed[0],clue['username'],event.iloc[0].event_id,selected.iloc[0].destination_ip,'SQL injection']
    for i,a in enumerate(answers):
        if i==4:
            assert not case.submit(i,a)[0]
            assert all(ok for _,ok in code_checks(secure)); case.module('Secure coding')
        assert case.submit(i,' '+a.upper()+' ')[0]
    auth=load_table('authentication_logs.csv').set_index('event_id'); syslog=logs.set_index('event_id')
    times=[auth.loc['AUTH-041','timestamp'],syslog.loc['SYS-040','timestamp'],syslog.loc['SYS-041','timestamp'],syslog.loc['SYS-042','timestamp'],selected.timestamp.min(),syslog.loc['SYS-043','timestamp']]
    assert times==sorted(times)
    assert not case.submit(5,[1,1,1,1,1,1])[0]
    assert case.submit(5,[1,2,3,4,5,6])[0]
    assert case.state['flag'].startswith('CYBER{')
    assert case.state['flag'] not in (ROOT/'lab.py').read_text()

def test_order_hints_persistence_reset(case):
    assert not case.submit(2,'SYS-042')[0]
    assert case.state['attempts']==[0]*6
    assert 'previous' in case.hint(2)
    assert not case.submit(0,'readme.txt')[0]
    assert case.state['failures'][0]==1
    hints=[case.hint(0) for _ in range(4)]
    assert len(set(hints))==3 and case.state['hints'][0]==3
    assert case.submit(0,'collector_config.txt')[0]
    restored=Investigation(case.state_path); assert restored.state==case.state
    restored.reset(); assert restored.state==restored.blank()
    assert Investigation(case.state_path).state==restored.blank()

def test_secure_code_assessment():
    assert all(ok for _,ok in code_checks(secure))
    assert not all(ok for _,ok in code_checks(unsafe))
    assert not all(ok for _,ok in code_checks(lambda conn,name: []))

def test_widget_callbacks(case):
    panel=case.challenge(0); next_panel=case.challenge(1)
    assert next_panel.children[2].children[0].disabled
    panel.children[1].value='readme.txt'; panel.children[2].children[0].click()
    assert 'Try again' in panel.children[3].value
    panel.children[2].children[1].click(); assert 'Hint' in panel.children[4].value
    panel.children[1].value='collector_config.txt'; panel.children[2].children[0].click()
    assert not next_panel.children[2].children[0].disabled
    h=hash_lab(case); h.children[1].value=h.children[0].value
    assert '0/256' in h.children[2].value
    h.children[3].value='Identical input gives the same digest'; h.children[4].click()
    assert 'Hashing' in case.state['modules']
    a=artifact_lab(case); a.children[0].value='collector_config.txt'; a.children[1].value=True
    a.children[3].value='Encoding'; a.children[4].click()
    assert 'Artifact analysis' in case.state['modules']
    e=explorer(load_table('network_traffic.csv'),network=True)
    e.children[0].children[0].value='research-07'; e.children[1].value='no matches expected'; e.children[1].value='203.0.113.77'
    e.children[2].children[1].value=True
    p=instructor_panel(case); p.children[0].value=True
    assert p.children[1].layout.display=='block'
    case.reset(); assert next_panel.children[2].children[0].disabled

def test_fresh_notebook_twice(tmp_path):
    workspace=tmp_path/'cybersecurity_showcase'
    shutil.copytree(ROOT,workspace,ignore=shutil.ignore_patterns('.progress','__pycache__','.pytest_cache','.git'))
    for _ in range(2):
        nb=nbformat.read(workspace/'Cybersecurity_Interactive_Lab.ipynb',as_version=4)
        nbformat.validate(nb)
        nb.cells.insert(0,nbformat.v4.new_code_cell("import socket\ndef offline(*args, **kwargs):\n    raise AssertionError('Network access is not permitted in this lab')\nsocket.create_connection = offline"))
        NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(workspace)}}).execute()
        assert not [o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
        assert 'Expected learning checkpoint' in ' '.join(str(c.get('outputs',[])) for c in nb.cells)

def test_student_package(tmp_path):
    with zipfile.ZipFile(package(tmp_path/'student.zip')) as z:
        names=z.namelist()
        assert not any('/instructor/' in n or '/tests/' in n or '/.progress/' in n for n in names)
        nb=json.loads(z.read('cybersecurity_showcase/Cybersecurity_Interactive_Lab.ipynb'))
        assert all(not c.get('outputs') for c in nb['cells'])
        assert 'cybersecurity_showcase/lab.py' in names
        assert 'cybersecurity_showcase/Watershed_Simulation.ipynb' in names
        assert 'cybersecurity_showcase/simulator/app.js' in names
        assert 'cybersecurity_showcase/simulator/engine.py' in names
        assert 'cybersecurity_showcase/mission/app.js' in names and 'cybersecurity_showcase/Guided_Mission.ipynb' in names
        assert not any('__pycache__' in n for n in names)
        assert z.getinfo('cybersecurity_showcase/start.sh').external_attr>>16 & 0o111  # stays executable after unzip

@pytest.mark.parametrize('content', ['not json', '[]', '{"version":1,"completed":0,"attempts":[0,0,0,0,0,0]}'])
def test_bad_saved_state_recovers(tmp_path,content):
    path=tmp_path/'session.json'; path.write_text(content)
    session=Investigation(path)
    assert session.state==session.blank() and 'unreadable' in session.storage_message
