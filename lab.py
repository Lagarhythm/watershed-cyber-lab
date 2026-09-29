"""Small reusable teaching components. Local assessment is formative, not tamper-proof."""
import base64
import hashlib
import html
import json
import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as W
from IPython.display import display, clear_output, HTML

ROOT = Path(__file__).resolve().parent
STAGES = ['Validate evidence', 'Decode artifact', 'Investigate logs', 'Follow network activity', 'Identify initial access', 'Reconstruct timeline']
HINTS = [
 ['A hash compares bytes, not intent.', 'Compare each file with the trusted manifest.', 'Read each file as bytes, calculate SHA-256, and locate the unequal digest.'],
 ['Encoding is reversible without a secret key.', 'Inspect the file whose digest differs.', 'Use base64.b64decode, then json.loads; locate the username field.'],
 ['Correlate a clue across independent sources.', 'Filter system events by decoded host, username, and process.', 'Find the process_start row and submit its event_id.'],
 ['Regular intervals alone do not prove malicious behavior.', 'Use the process_start time, host, and process from your previous evidence.', 'Filter network rows after the process start; group by destination and compare time gaps.'],
 ['Untrusted input can change the meaning of a query.', 'Compare the portal login message with application_example.py.', 'Name the query-construction vulnerability; repair the lookup with bound parameters.'],
 ['Order events by UTC timestamps, not by when you discovered them.', 'Use AUTH-041, system events for the recovered account, and the first matching network row.', 'Assign a unique rank 1–6 to access, job, file write, process start, communication, and file read.']]
TIMELINE = ['Portal access', 'Research job invoked', 'Collector file replaced', 'Sync process started', 'Outbound communication', 'Sensitive file read']

def normalize(value): return str(value).strip().casefold()

def code_checks(fn):
    """Behavior plus database-boundary checks, using only in-memory SQLite."""
    results=[]
    with sqlite3.connect(':memory:') as conn:
        conn.execute('CREATE TABLE users (username TEXT)')
        conn.executemany('INSERT INTO users VALUES (?)', [('riley',), ('jordan',), ("o\'neil",)])
        for value, expected, label in [('riley',[('riley',)],'Existing user works'), ('missing',[],'Unknown user stays unknown'), ("o'neil",[("o'neil",)],'Apostrophe is treated as data'), ("' OR '1'='1",[],'Injection does not expand results')]:
            try: results.append((label, fn(conn,value)==expected))
            except Exception: results.append((label,False))
    class Probe:
        def __init__(self): self.calls=[]
        def execute(self, sql, params=None): self.calls.append((sql,params)); return self
        def fetchall(self): return []
    probe=Probe(); marker='BOUND_VALUE_729'
    try:
        fn(probe,marker)
        passed=bool(probe.calls) and all(marker not in sql and params is not None and marker in (list(params.values()) if isinstance(params,dict) else params) for sql,params in probe.calls)
    except Exception: passed=False
    results.append(('User input is passed separately as a bound parameter', passed))
    return results

class Investigation:
    def __init__(self, state_path=None):
        self.state_path=Path(state_path) if state_path else ROOT/'.progress'/'session.json'
        self.listeners=[]
        self.state=self.blank()
        self.storage_message=''
        if self.state_path.exists():
            try:
                loaded=json.loads(self.state_path.read_text())
                if loaded.get('version')!=1 or type(loaded['completed']) is not int or not 0<=loaded['completed']<=6: raise ValueError()
                for key in ('attempts', 'failures', 'hints'):
                    if not isinstance(loaded[key], list) or len(loaded[key])!=6 or any(type(v) is not int or v<0 for v in loaded[key]): raise ValueError()
                if not isinstance(loaded['modules'], list) or any(not isinstance(v,str) for v in loaded['modules']): raise ValueError()
                if loaded['flag'] is not None and not isinstance(loaded['flag'],str): raise ValueError()
                self.state=loaded
            except (OSError,ValueError,KeyError,TypeError,AttributeError): self.storage_message='Saved progress was unreadable; using a fresh in-memory session. Reset to replace it.'
    @staticmethod
    def blank(): return dict(version=1,completed=0,attempts=[0]*6,failures=[0]*6,hints=[0]*6,modules=[],flag=None)
    def save(self):
        try:
            self.state_path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.state_path.with_suffix('.tmp'); temporary.write_text(json.dumps(self.state,indent=2)); temporary.replace(self.state_path)
        except OSError: self.storage_message='Progress is in memory only: this folder is not writable.'
        for callback in self.listeners: callback()
    def reset(self): self.state=self.blank(); self.save()
    def module(self,name):
        if name not in self.state['modules']: self.state['modules'].append(name)
        self.save()
    def hint(self,stage):
        if stage>self.state['completed']: return 'Complete the previous stage to unlock these hints.'
        level=min(self.state['hints'][stage],2)
        self.state['hints'][stage]=min(3,self.state['hints'][stage]+1); self.save()
        return HINTS[stage][level]
    def submit(self,stage,answer):
        if stage>self.state['completed']: return False,'Complete the previous stage first; its evidence guides this step.'
        if stage<self.state['completed']: return True,'Evidence already accepted. Continue to the next stage.'
        self.state['attempts'][stage]+=1
        expected=['collector_config.txt','riley','sys-042','203.0.113.77','sql injection']
        ok=(answer==list(range(1,7))) if stage==5 else normalize(answer)==expected[stage]
        if stage==4 and 'Secure coding' not in self.state['modules']:
            ok=False; message='Run and pass the secure-code checks as well as naming the vulnerability.'
        else:
            message=[ 'Compare file bytes with the trusted manifest; a mismatch is an integrity clue, not proof of malware.', 'Submit the username from the decoded JSON, not its host or process.', 'Find the process_start event matching all three decoded fields; submit its event ID.', 'That destination does not match the correlated host/process stream. Compare the rows beginning after its start time.', 'Inspect how untrusted text changes the SQL predicate; name the vulnerability.', 'Use each rank exactly once. Compare the UTC timestamps across authentication, system, and network evidence.'][stage]
        if ok:
            self.state['completed']+=1
            if self.state['completed']==6:
                # Generate the completion token at completion, rather than embedding a final flag.
                material='|'.join(expected+TIMELINE).encode()
                self.state['flag']='CYBER{'+hashlib.sha256(material).hexdigest()[:16].upper()+'}'
            message='Accepted — evidence added to the case.'
        else: self.state['failures'][stage]+=1
        self.save(); return ok,message
    def progress(self):
        bar=W.IntProgress(min=0,max=6,description='Case stages')
        label=W.HTML()
        def update():
            bar.value=self.state['completed']
            label.value=f"<b>Investigation: {bar.value}/6 stages</b> · Lessons checked: {len(self.state['modules'])}/5 · Hints revealed: {sum(self.state['hints'])}" + (f"<p><b>Completion token: {self.state['flag']}</b></p>" if self.state['flag'] else '')
        self.listeners.append(update); update(); return W.VBox([bar,label])
    def challenge(self,stage):
        field=W.Text(description='Answer:',layout=W.Layout(width='95%')) if stage<5 else None
        ranks=[W.Dropdown(options=[('Choose rank',0)]+[(str(i),i) for i in range(1,7)],description=label,style={'description_width':'180px'}) for label in TIMELINE]
        inputs=[field] if field else [ranks[i] for i in [3,0,5,2,1,4]]
        submit=W.Button(description='Check evidence',button_style='primary'); hint=W.Button(description='Next hint'); feedback=W.HTML(); hintout=W.HTML()
        def check(_):
            answer=field.value if field else [r.value for r in ranks]
            ok,msg=self.submit(stage,answer); feedback.value=f"<b>{'Accepted' if ok else 'Try again'}:</b> {html.escape(msg)}"
        submit.on_click(check)
        hint.on_click(lambda _: setattr(hintout,'value', '<b>Hint:</b> '+html.escape(self.hint(stage))))
        def update():
            locked=stage>self.state['completed']; submit.disabled=locked; hint.disabled=locked
            for item in inputs: item.disabled=locked
        self.listeners.append(update); update()
        return W.VBox([W.HTML(f'<h3>Stage {stage+1} · {STAGES[stage]}</h3>'),*inputs,W.HBox([submit,hint]),feedback,hintout])

def load_table(name):
    df=pd.read_csv(ROOT/'data'/name)
    if 'timestamp' in df: df['timestamp']=pd.to_datetime(df['timestamp'],utc=True)
    return df

def hash_lab(case):
    a=W.Text(value='Research sample',description='Original:'); b=W.Text(value='research sample',description='Changed:'); out=W.HTML()
    def update(_=None):
        ha,hb=[hashlib.sha256(t.value.encode()).hexdigest() for t in (a,b)]
        bits=sum((x^y).bit_count() for x,y in zip(bytes.fromhex(ha),bytes.fromhex(hb)))
        out.value=f'<p>SHA-256 original: <code>{ha}</code><br>SHA-256 changed: <code>{hb}</code></p><b>{bits}/256 bits differ.</b> Same bytes always give the same digest. A mismatch alone does not identify the cause.'
    a.observe(update,names='value'); b.observe(update,names='value'); update()
    check=W.Button(description='Check prediction'); feedback=W.HTML()
    prediction=W.Dropdown(options=['Choose a prediction','Identical input gives the same digest','A hash can be decoded to recover text'],description='Prediction:',style={'description_width':'initial'})
    def assess(_):
        ok=prediction.value=='Identical input gives the same digest'
        if ok: case.module('Hashing')
        feedback.value='Correct: try making both inputs identical.' if ok else 'Try again: a hash is a fingerprint; encoding is the reversible operation.'
    check.on_click(assess)
    return W.VBox([a,b,out,prediction,check,feedback])

def artifact_lab(case):
    filename=W.Dropdown(options=load_table('evidence_manifest.csv').filename.tolist(),description='Artifact:')
    decode=W.Checkbox(value=False,description='Try Base64 decoding'); out=W.Output()
    def show(_=None):
        with out:
            clear_output(wait=True)
            data=(ROOT/'data'/filename.value).read_bytes()
            print(f'{len(data)} bytes | SHA-256 {hashlib.sha256(data).hexdigest()}')
            print(data.decode())
            if decode.value:
                try: print('Decoded text:\n'+base64.b64decode(data.strip(),validate=True).decode())
                except (ValueError,UnicodeError): print('This file is not valid Base64 text. Try another artifact; encoding is not encryption.')
    filename.observe(show,names='value'); decode.observe(show,names='value'); show()
    q=W.Dropdown(options=['Choose a classification','Encoding','Encryption','Hashing'],description='Base64 is:'); feedback=W.HTML(); button=W.Button(description='Check concept')
    def check(_):
        ok=q.value=='Encoding'
        if ok: case.module('Artifact analysis')
        feedback.value='Correct: reversible representation, with no secret key.' if ok else 'Try again: decoding Base64 needs no secret. Compare this with encryption and hashing.'
    button.on_click(check)
    return W.VBox([filename,decode,out,q,button,feedback])

def explorer(df,network=False):
    selectors={col:W.Dropdown(options=['All']+sorted(df[col].unique().tolist()),description=col.replace('_',' ').title()+':',style={'description_width':'initial'}) for col in (['host','protocol','process'] if network else ['host','username','event_type'])}
    search=W.Text(description='Search:',placeholder='IP, message, event ID…'); sort=W.Dropdown(options=list(df.columns),value='timestamp',description='Sort by:'); descending=W.Checkbox(description='Descending')
    out=W.Output()
    def update(_=None):
        selected=df.copy()
        for col,widget in selectors.items():
            if widget.value!='All': selected=selected[selected[col]==widget.value]
        if search.value.strip(): selected=selected[selected.astype(str).apply(lambda col: col.str.contains(search.value.strip(),case=False,regex=False)).any(axis=1)]
        selected=selected.sort_values(sort.value,ascending=not descending.value)
        with out:
            clear_output(wait=True); print(f'{len(selected)} of {len(df)} records match. All timestamps UTC.'); display(selected)
            if selected.empty: print('No matches. Clear a filter or change the search text.'); return
            counts=selected.set_index('timestamp').resample('1min').size()
            fig,ax=plt.subplots(figsize=(9,2.6)); ax.plot(counts.index,counts.values,marker='o',color='#245a81'); ax.set(title='Connections per minute' if network else 'Events per minute',xlabel='Time (UTC)',ylabel='Record count'); ax.grid(alpha=.25); fig.autofmt_xdate(); display(fig); plt.close(fig)
            print(f'Chart description: {len(selected)} records; peak {counts.max()} per minute. The table above provides the exact evidence.')
    for widget in [*selectors.values(),search,sort,descending]: widget.observe(update,names='value')
    update(); return W.VBox([W.HBox(list(selectors.values())),search,W.HBox([sort,descending]),out])

def practice(case,name,prompt,expected,explanation):
    answer=W.Text(description='Answer:',layout=W.Layout(width='90%')); button=W.Button(description='Check reasoning'); feedback=W.HTML()
    def check(_):
        ok=normalize(answer.value)==normalize(expected)
        if ok: case.module(name)
        feedback.value=('<b>Correct.</b> ' if ok else '<b>Try again.</b> ')+html.escape(explanation)
    button.on_click(check)
    return W.VBox([W.HTML(html.escape(prompt)),answer,button,feedback])

def assess_code(case,fn):
    results=code_checks(fn)
    display(pd.DataFrame(results,columns=['Check','Passed']))
    if all(ok for _,ok in results): case.module('Secure coding'); print('All checks passed. Bound parameters preserve input as data.')
    else: print('Expected learning checkpoint: repair the function, rerun its cell, then rerun these checks. Use execute(sql, (username,)) with a ? placeholder.')
    return results

def dashboard(case):
    """Live local record plus clearly separate, deterministic simulated cohort."""
    out=W.Output(); refresh=W.Button(description='Refresh analytics')
    def show(_=None):
        with out:
            clear_output(wait=True)
            print('LIVE LOCAL SESSION — anonymous; no data sent to a server')
            display(pd.DataFrame({'Stage':STAGES,'Attempts':case.state['attempts'],'Failed attempts':case.state['failures'],'Hint levels revealed':case.state['hints'],'Complete':[i<case.state['completed'] for i in range(6)]}))
            print('Modules checked: '+(', '.join(case.state['modules']) or 'None')); print('CTF complete:',case.state['completed']==6)
            print('\nSIMULATED COHORT — 8 invented records, not JupyterHub telemetry')
            reached=[6,6,5,4,3,6,2,4]
            cohort=pd.DataFrame({'Learner':[f'Demo {i+1}' for i in range(8)],'Stages complete':reached})
            display(cohort)
            attempts=[1.2,1.5,2.1,2.8,1.7,2.0]; hints=[2,5,9,15,7,6]; failures=[1,4,7,13,5,6]
            display(pd.DataFrame({'Stage':STAGES,'Mean attempts (simulated)':attempts,'Hints (simulated)':hints,'Failures (simulated)':failures}))
            print(f'Simulated CTF completion rate: {sum(x==6 for x in reached)/len(reached):.0%}. Mean stage completion: {sum(reached)/(6*len(reached)):.0%}. Most hints and failures: network correlation.')
            print('Teaching response: pause to model host + process + time correlation, then let learners retry.')
            fig,ax=plt.subplots(figsize=(8,2.5)); ax.bar(cohort.Learner,cohort['Stages complete'],color='#245a81'); ax.set(ylim=(0,6),ylabel='Stages complete',title='Simulated progress distribution'); display(fig); plt.close(fig)
    refresh.on_click(show); show(); return W.VBox([refresh,out])

def instructor_panel(case):
    toggle=W.Checkbox(description='Show instructor view',value=False)
    box=W.Output(layout=W.Layout(display='none')); confirmation=W.Checkbox(description='Confirm reset of this local session'); reset=W.Button(description='Reset progress',button_style='warning'); message=W.HTML()
    def reveal(change):
        box.layout.display='block' if change['new'] else 'none'
        if change['new']:
            with box:
                clear_output(wait=True)
                display(HTML('<p><b>Teaching notes:</b> Ask for evidence before accepting conclusions. A hash mismatch is not a malware verdict; periodic traffic is not proof of command and control. See instructor/ for the solution and facilitation guide. This display toggle is not access control.</p>'))
                display(dashboard(case)); display(confirmation,reset,message)
    def clear(_):
        if confirmation.value:
            case.reset(); confirmation.value=False; message.value='Progress reset. Restart the kernel and run all cells to clear old widget text and restore the exercise function.'
        else: message.value='Select the confirmation checkbox to reset your local progress.'
    reset.on_click(clear); toggle.observe(reveal,names='value'); return W.VBox([toggle,box])
