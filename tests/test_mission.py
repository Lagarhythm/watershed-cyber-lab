import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mission.engine import Mission, STEPS

def advance(m):
    """Answer the current quick check correctly and move on."""
    m.dispatch({'type':'answer','choice':STEPS[m.step]['check']['answer']})
    m.dispatch({'type':'next'})

def test_every_step_states_task_learning_and_why():
    for step in STEPS[1:-1]:
        assert step['story'] and step['learning'] and step['why'] and step['learned'] and step['learned_why']
        assert step['check']['options'][step['check']['answer']]
    m=Mission()
    for i in range(1,len(STEPS)-1):
        m.step=i
        assert len(m.snapshot()['step']['tasks'])>=3, STEPS[i]['id']

def test_full_mission_with_wrong_turns():
    m=Mission(); m.dispatch({'type':'next'})
    # 1 Observe: inspect all four, label all four correctly.
    m.dispatch({'type':'inspect','host':'research-07'}); assert not m.inspected   # traffic not shown yet
    m.dispatch({'type':'observe'})
    for h in ['portal-01','research-07','research-08','archive-01']: m.dispatch({'type':'inspect','host':h})
    m.dispatch({'type':'label','host':'research-08','verdict':'suspicious'}); assert m.feedback['tone']=='try'
    m.dispatch({'type':'next'}); assert m.step==1
    for h,v in [('research-08','normal'),('portal-01','normal'),('archive-01','normal')]: m.dispatch({'type':'label','host':h,'verdict':v})
    assert not m.done['observe']
    m.dispatch({'type':'label','host':'research-07','verdict':'suspicious'}); assert m.done['observe']
    m.dispatch({'type':'answer','choice':0}); assert not m.checked['observe']
    advance(m); assert STEPS[m.step]['id']=='integrity'
    # 2 Verify: compare fingerprints by hand, then change and restore the tester text.
    m.dispatch({'type':'verdict','filename':'readme.txt','verdict':'match'}); assert not m.verdicts   # not computed yet
    m.dispatch({'type':'scan'})
    m.dispatch({'type':'verdict','filename':'collector_config.txt','verdict':'match'}); assert 'collector_config.txt' not in m.verdicts
    for f,v in [('collector_config.txt','changed'),('readme.txt','match'),('research_notes.txt','match')]: m.dispatch({'type':'verdict','filename':f,'verdict':v})
    assert not m.done['integrity']
    m.dispatch({'type':'hash','text':'research sample'}); assert not m.done['integrity']
    m.dispatch({'type':'hash','text':'Research sample'}); assert m.done['integrity']
    advance(m)
    # 3 Decode: open the changed file, recognize Base64, fill the clue card in order.
    m.dispatch({'type':'open','filename':'readme.txt'}); assert m.opened is None
    m.dispatch({'type':'open','filename':'collector_config.txt'})
    m.dispatch({'type':'format','choice':'encrypted'}); assert m.decoded is None
    m.dispatch({'type':'format','choice':'base64'}); assert m.decoded['process']=='sync_agent'
    m.dispatch({'type':'clue','key':'process'}); assert not m.clues   # the computer slot comes first
    for k in ['host','username','process']: m.dispatch({'type':'clue','key':k})
    assert m.done['decode']
    advance(m)
    # 4 Connect: filter the real log, then name the destination.
    m.dispatch({'type':'destination','ip':'203.0.113.77'}); assert m.destination is None   # must filter first
    m.dispatch({'type':'filter','host':'research-07','process':''}); assert len(m.network_rows())==24
    m.dispatch({'type':'filter','host':'research-07','process':'sync_agent'}); assert len(m.network_rows())==8
    assert {r['destination'] for r in m.network_rows()}=={'203.0.113.77'}
    m.dispatch({'type':'destination','ip':'203.0.113.80'}); assert not m.done['correlate']
    m.dispatch({'type':'destination','ip':'203.0.113.77'}); assert m.done['correlate']
    advance(m)
    # 5 Contain: over-isolating and untested containment are not accepted.
    m.dispatch({'type':'toggle','host':'portal-01'}); assert m.availability()==55
    m.dispatch({'type':'toggle','host':'research-07'}); m.dispatch({'type':'verify'}); assert not m.done['contain']
    m.dispatch({'type':'toggle','host':'portal-01'}); assert m.verify_result is None and not m.done['contain']
    m.dispatch({'type':'verify'}); assert m.done['contain'] and m.availability()==75
    m.dispatch({'type':'toggle','host':'research-07'}); assert m.isolated==['research-07']   # stage locks once done
    advance(m)
    # 6 Repair: free typing on both portal versions.
    m.dispatch({'type':'login','value':'riley'}); assert m.repair_flags['normal']
    m.dispatch({'type':'login','value':"o'neil"}); assert m.last_query['error']
    m.dispatch({'type':'login','value':"riley' OR '1'='1"}); assert m.repair_flags['attack'] and len(m.last_query['rows'])==3
    m.dispatch({'type':'mode','mode':'bound'}); m.dispatch({'type':'patch'}); assert not m.patched
    m.dispatch({'type':'login','value':"riley' OR '1'='1"}); assert m.repair_flags['fixed_attack'] and m.last_query['rows']==[]
    m.dispatch({'type':'login','value':"o'neil"}); assert m.repair_flags['apostrophe'] and m.last_query['rows']==["o'neil"]
    m.dispatch({'type':'patch'}); assert m.patched and m.done['repair']
    advance(m)
    # 7 Recover: order matters; only sync_agent is ended; the trusted file is restored.
    m.dispatch({'type':'reconnect'}); assert not m.reconnected
    m.dispatch({'type':'kill','process':'browser'}); assert not m.killed
    m.dispatch({'type':'config','choice':'restore'}); assert m.config is None   # kill first
    m.dispatch({'type':'kill','process':'sync_agent'})
    m.dispatch({'type':'config','choice':'delete'}); assert m.config is None
    m.dispatch({'type':'config','choice':'restore'})
    m.dispatch({'type':'confirm'}); assert not m.confirmed
    m.dispatch({'type':'reconnect'}); m.dispatch({'type':'confirm'})
    assert m.done['recover'] and m.availability()==100 and not m.snapshot()['threat_active']
    advance(m)
    s=m.snapshot()
    assert s['step']['id']=='debrief' and all(x['done'] for x in s['steps'][1:-1])
    assert len(s['recap'])==7 and len(s['history'])==7
    m.dispatch({'type':'reset'}); assert m.step==0 and not m.history

def test_hint_and_bad_input():
    m=Mission()
    for bad in [None,'x',{'type':'nope'},{'type':'answer','choice':'1'},{'type':'toggle','host':'evil'}]:
        m.dispatch(bad)
    assert m.step==0
    m.step=2; m.dispatch({'type':'hash','text':'a'*5000}); assert len(m.hash_input)==200
    m.step=6; m.dispatch({'type':'login','value':'nobody'}); assert m.attack_misses==1
    m.dispatch({'type':'hint'}); assert "OR '1'='1" in m.feedback['text']
    m.dispatch({'type':'login','value':'x'*500}); assert len(m.last_query['input'])==80
