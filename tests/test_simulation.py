"""Behavior checks for the interactive student's decision loop."""
import json
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from simulator.engine import Simulation
from simulator.widget import WatershedSimulation

def act(sim,kind,**kw): sim.dispatch({'type':kind,**kw})
def observe(sim):
    act(sim,'play')
    for _ in range(6): act(sim,'tick')
    act(sim,'pause')

def evidence(sim):
    act(sim,'scan'); act(sim,'decode',filename='collector_config.txt')
    act(sim,'correlate',host='research-07',process='sync_agent',destination='203.0.113.77')

def test_containment_and_recovery_change_traffic():
    s=Simulation(); observe(s); evidence(s)
    assert s.beacons==1 and s.correlated
    assert sum(not f['matches'] for f in s.integrity)==1
    act(s,'isolate',host='research-07'); assert s.snapshot()['availability']==75
    observe(s); assert s.beacons==1
    act(s,'restore_host',host='research-07'); observe(s); assert s.beacons==2
    act(s,'isolate',host='research-07'); act(s,'remediate')
    act(s,'restore_host',host='research-07'); observe(s)
    assert s.beacons==2 and s.snapshot()['availability']==100
    act(s,'query',mode='bound',value="' OR '1'='1"); act(s,'patch'); act(s,'finish')
    assert s.snapshot()['score']==100 and s.finished
    act(s,'play'); assert not s.running

def test_repair_does_not_stop_existing_process():
    s=Simulation();act(s,'patch'); assert not s.patched
    act(s,'query',mode='unsafe',value="' OR '1'='1")
    assert len(s.query_result['rows'])==3
    act(s,'query',mode='bound',value="' OR '1'='1")
    assert s.query_result['rows']==[]
    act(s,'query',mode='bound',value="o'neil")
    assert s.query_result['rows']==["o'neil"]
    act(s,'patch');observe(s)
    assert s.patched and s.beacons==1

def test_bad_decisions_and_late_containment():
    s=Simulation();act(s,'decode',filename='readme.txt');assert not s.decoded
    act(s,'remediate');assert not s.remediated
    act(s,'isolate',host='research-08');observe(s)
    assert s.beacons==1 and s.snapshot()['availability']==80
    act(s,'play');act(s,'speed',value=4)
    for _ in range(18):act(s,'tick')
    assert s.tick==72 and not s.running and s.file_access
    act(s,'isolate',host='research-07');assert s.file_access
    assert not s.snapshot()['availability']==100

def test_replay_reset_and_widget_messages():
    s=Simulation();observe(s);evidence(s);act(s,'isolate',host='research-07')
    other=Simulation();act(other,'restore',journal=json.loads(json.dumps(s.journal)))
    assert other.beacons==s.beacons and other.isolated==s.isolated and other.correlated
    assert not other.running
    act(other,'reset');assert other.tick==0 and not other.journal and not other.integrity
    w=WatershedSimulation();w._action(w,{'type':'scan'},None)
    assert len(w.state['integrity'])==3
    w.close()

def test_hash_experiment_and_wrong_correlation():
    s=Simulation();act(s,'hash',original='same',changed='same');assert s.hash_result['bits']==0
    act(s,'hash',original='same',changed='Same');assert s.hash_result['bits']>0
    observe(s);act(s,'decode',filename='collector_config.txt')
    act(s,'correlate',host='research-08',process='backup_agent',destination='192.0.2.200')
    assert not s.correlated

def test_student_app_executes():
    root=Path(__file__).resolve().parents[1]
    nb=nbformat.read(root/'Watershed_Simulation.ipynb',as_version=4)
    nbformat.validate(nb)
    NotebookClient(nb,timeout=60,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
    assert any('application/vnd.jupyter.widget-view+json' in o.get('data',{}) for o in nb.cells[0].outputs)
