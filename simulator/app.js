const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hosts = {
  'portal-01': {name:'Research portal', role:'Identity & job access', x:19,y:25,icon:'▣'},
  'research-07': {name:'Research 07',role:'Research workstation',x:49,y:48,icon:'▤'},
  'research-08': {name:'Research 08',role:'Scheduled backups',x:19,y:76,icon:'▤'},
  'archive-01': {name:'Data archive',role:'Watershed datasets',x:79,y:76,icon:'▥'},
};
const key = 'watershed-simulation-v2';
function render({model,el}) {
  el.classList.add('ws-app');
  let state = model.get('state'), tab = 'operations', lastEvidence = '', lastInspector = '', awaitingTick = false;
  let saved = null, storageWarning = '';
  try { saved = JSON.parse(localStorage.getItem(key)); } catch (_) { storageWarning='Browser saving is unavailable. Export your report before closing.'; }
  const send = command => model.send(command);
  el.innerHTML = `
    <div class="ws-shell">
      <header class="ws-header"><div class="ws-brand"><span class="ws-logo">◈</span><div><span class="ws-eyebrow">INTERACTIVE LAB</span><h1>Watershed <span>Incident Command</span></h1></div></div><div class="ws-header-right"><span class="ws-pill">FICTIONAL ENVIRONMENT</span><button data-action="brief" class="ws-icon-button" aria-label="Mission briefing">?</button></div></header>
      <section class="ws-mission"><div><span class="ws-eyebrow">YOUR MISSION · JUNIOR INCIDENT RESPONDER</span><p>Find the signal. Contain the incident. Keep the research running.</p></div><div class="ws-mission-status"><span class="ws-dot"></span><span id="ws-status">Ready to investigate</span></div></section>
      <div class="ws-toolbar"><nav aria-label="Simulation views"><button data-tab="operations" class="active">01 <span>Operations</span></button><button data-tab="evidence">02 <span>Evidence lab</span></button><button data-tab="response">03 <span>Portal workbench</span></button><button data-tab="debrief">04 <span>Debrief</span></button></nav><div class="ws-clock-controls"><span id="ws-clock" class="ws-clock">09:14:00</span><span class="ws-utc">UTC</span><button data-action="play" id="ws-play" class="ws-primary">Start simulation</button><label class="ws-speed"><span class="ws-sr">Simulation speed</span><select id="ws-speed"><option value="1">1× speed</option><option value="4">4× speed</option></select></label></div></div>
      <div class="ws-notice" role="status" aria-live="polite" id="ws-notice"></div>
      <div id="ws-saved" class="ws-saved" hidden><span>A saved attempt is available in this browser.</span><button data-action="resume">Resume saved attempt</button><button data-action="discard">Dismiss</button></div>
      <section class="ws-metrics" aria-label="Live simulation metrics"><article><span>INVESTIGATION</span><strong id="ws-progress">0<span>/5</span></strong><small>Evidence & response objectives</small></article><article><span>SUSPICIOUS OUTBOUND</span><strong id="ws-beacons">0 <span>connections</span></strong><small id="ws-bytes">0 bytes observed</small></article><article><span>SERVICE AVAILABILITY</span><strong id="ws-availability">100<span>%</span></strong><small>Illustrative weighted service model</small></article><article><span>RESPONSE POSTURE</span><strong id="ws-posture" class="ws-posture">Investigating</strong><small id="ws-posture-note">Evidence before assumptions</small></article></section>
      <main>
        <section data-panel="operations">
          <div class="ws-ops-grid"><section class="ws-card ws-network"><div class="ws-card-heading"><div><span class="ws-eyebrow">LIVE TOPOLOGY</span><h2>Follow the connections</h2></div><span class="ws-subtle">Select a host to inspect</span></div>
            <div class="ws-map"><svg viewBox="0 0 800 340" preserveAspectRatio="none" aria-hidden="true"><defs><pattern id="ws-grid" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="#24354b"/></pattern></defs><rect width="800" height="340" fill="url(#ws-grid)"/><path class="ws-link" data-edge="portal-01" d="M152 85 L392 163"/><path class="ws-link" data-edge="research-08" d="M152 258 L632 258"/><path class="ws-link" data-edge="archive-01" d="M392 163 L632 258"/><path class="ws-link ws-threat-link" data-edge="research-07" d="M392 163 L632 68"/></svg>
              ${Object.entries(hosts).map(([id,h])=>`<button class="ws-node" data-host="${id}" style="left:${h.x}%;top:${h.y}%" aria-label="Inspect ${id}"><span class="ws-node-icon">${h.icon}</span><strong>${h.name}</strong><small>${id}</small><span class="ws-node-status">Online</span></button>`).join('')}
              <div class="ws-external"><span>↗</span><strong>External endpoint</strong><small>203.0.113.77</small><em>Unverified destination</em></div>
            </div><div class="ws-map-legend"><span><i class="ws-legend-line"></i> Routine / internal route</span><span><i class="ws-legend-line alert"></i> Investigate outbound route</span><span>Motion shows route activity, not individual packets.</span></div>
            <div class="ws-chart-head"><h3>Traffic pulse</h3><span>Records per 30 simulated seconds</span></div><div id="ws-chart" class="ws-chart"></div><p id="ws-chart-text" class="ws-chart-text"></p>
          </section>
          <aside class="ws-card ws-inspector"><span class="ws-eyebrow">HOST INSPECTOR</span><div id="ws-inspector"></div></aside></div>
          <div class="ws-bottom-grid"><section class="ws-card"><div class="ws-card-heading"><h2>Event stream</h2><label class="ws-inline-filter">Show <select id="ws-event-filter"><option value="all">All events</option><option value="alert">Alerts</option><option value="network">Network</option><option value="action">My actions</option><option value="blocked">Blocked</option></select></label></div><div class="ws-events" id="ws-events" role="log" aria-label="Simulation event stream" aria-live="off"></div></section><section class="ws-card"><div class="ws-card-heading"><h2>Case objectives</h2><button data-action="hint" class="ws-text-button">Get a hint ↗</button></div><div id="ws-goals"></div><div class="ws-callout">Pause freely. A good response balances evidence, containment, and service continuity.</div></section></div>
        </section>
        <section data-panel="evidence" hidden>
          <div class="ws-section-intro"><span class="ws-eyebrow">OBSERVE → TEST → CONNECT</span><h2>Make the evidence tell a story.</h2><p>Verify bytes, decode a lead, then match it to traffic you have actually observed.</p></div>
          <div class="ws-evidence-grid"><section class="ws-card"><div class="ws-card-heading"><h2>01 / Integrity scanner</h2><button data-action="scan" class="ws-primary">Verify files</button></div><p>A trusted pre-incident manifest gives you a baseline. Changed bytes are a clue, not a verdict.</p><div id="ws-integrity" class="ws-placeholder">Three collected files are ready to compare.</div></section><section class="ws-card"><div class="ws-card-heading"><h2>02 / Artifact decoder</h2><span class="ws-tag">BASE64</span></div><p>Encoding changes representation. It does not protect a secret.</p><label class="ws-field">Collected file<select id="ws-artifact"><option>readme.txt</option><option>research_notes.txt</option><option>collector_config.txt</option></select></label><button data-action="decode">Decode selected file</button><div id="ws-decoded" class="ws-placeholder">Choose an artifact based on the integrity finding.</div></section></div>
          <section class="ws-card ws-correlation"><div class="ws-card-heading"><div><h2>03 / Connect the evidence</h2><p>Match all three fields. A periodic backup is the benign counterexample.</p></div><span id="ws-correlated" class="ws-tag">NOT YET VERIFIED</span></div><div class="ws-form-row"><label class="ws-field">Host<select id="ws-c-host"><option>research-08</option><option>research-07</option></select></label><label class="ws-field">Process<select id="ws-c-process"><option>backup_agent</option><option>sync_agent</option><option>browser</option></select></label><label class="ws-field">Destination<select id="ws-c-destination"><option>192.0.2.200</option><option>203.0.113.77</option><option>203.0.113.80</option></select></label><button data-action="correlate" class="ws-primary">Check correlation</button></div><details><summary>Open collected system events · available at 09:14</summary><div id="ws-system" class="ws-table-wrap"></div></details></section>
          <section class="ws-card ws-hash"><div><span class="ws-eyebrow">TRY IT YOURSELF</span><h2>One character. A different fingerprint.</h2><p>Change either input to recalculate SHA-256. Then make them identical.</p></div><div class="ws-form-row"><label class="ws-field">Original text<input id="ws-hash-a" value="Research sample" maxlength="2000"></label><label class="ws-field">Changed text<input id="ws-hash-b" value="research sample" maxlength="2000"></label></div><div id="ws-hash-result"></div></section>
        </section>
        <section data-panel="response" hidden>
          <div class="ws-section-intro"><span class="ws-eyebrow">EXPERIMENT WITHOUT WRITING CODE</span><h2>Close the entry point.</h2><p>The portal treated login input as part of its database instructions. Test a safer design, then apply it.</p></div>
          <div class="ws-evidence-grid"><section class="ws-card"><h2>Portal request workbench</h2><p>This isolated database contains three fictional users. A lookup grants a session in this simplified application.</p><div class="ws-designs"><label><input type="radio" name="ws-query-mode" value="unsafe" checked><span><strong>Mix input into the query</strong><small>Original design · input can change instructions</small></span></label><label><input type="radio" name="ws-query-mode" value="bound"><span><strong>Use bound parameters</strong><small>Repair · input remains data</small></span></label></div><label class="ws-field">Username input<input id="ws-query-input" value="riley" maxlength="200"></label><div class="ws-button-row"><button data-action="payload">Insert test payload</button><button data-action="normal">Use ordinary name</button><button data-action="query" class="ws-primary">Run lookup</button></div><div id="ws-query-result" class="ws-placeholder">Run a normal lookup, then compare the test payload under both designs.</div></section><section class="ws-card"><span class="ws-eyebrow">RESPONSE PLAN</span><h2>Repair is only one part of recovery.</h2><div class="ws-sequence"><div><b>1</b><p><strong>Preserve the evidence</strong>Verify, decode and correlate before removing the process.</p></div><div><b>2</b><p><strong>Contain the workstation</strong>Isolate the affected host. Watch traffic stop and service availability fall.</p></div><div><b>3</b><p><strong>Repair the portal</strong>Bound parameters block new malformed logins, but do not remove the existing process.</p></div><div><b>4</b><p><strong>Recover deliberately</strong>Remove the simulated process while contained, then restore the host.</p></div></div><button data-action="patch" class="ws-primary" id="ws-patch">Apply portal repair</button><div id="ws-repair-status" class="ws-placeholder"></div><div class="ws-callout">All actions affect this fictional model only. Real containment and recovery require additional checks.</div></section></div>
        </section>
        <section data-panel="debrief" hidden><div class="ws-section-intro"><span class="ws-eyebrow">AFTER-ACTION REVIEW</span><h2>What changed because of your decisions?</h2><p>Review the evidence you collected, the service tradeoffs, and what the observations cannot prove.</p></div><div class="ws-button-row ws-debrief-actions"><button data-action="finish" id="ws-finish" class="ws-primary">Finish attempt & review</button><button data-action="export">Download report</button><button data-action="reset" class="ws-danger">Start a new attempt</button></div><div id="ws-debrief"></div></section>
      </main>
      <footer><span>THE WATERSHED INCIDENT</span><span id="ws-storage">Session saves in this browser · no account or external AI required</span><button data-action="reset" class="ws-text-button">Reset scenario</button></footer>
      <dialog class="ws-dialog" id="ws-brief"><span class="ws-eyebrow">CASE 07 / MISSION BRIEF</span><h2>You’re on call.</h2><p>A research workstation just launched an unfamiliar process. You have a trusted file manifest, collected artifacts, system events, and a live simulated network.</p><ol><li>Start the clock and select hosts on the map.</li><li>Use the Evidence lab to establish what changed.</li><li>Observe a connection, then contain the right host.</li><li>Test a portal repair, remove the process and restore service.</li><li>Review your decisions in the debrief.</li></ol><p><strong>Pause whenever you need.</strong> At 1×, one second advances ten simulated seconds. The scenario ends at 09:26. All addresses and actions are fictional. No Python is required.</p><button data-action="close-brief" class="ws-primary">Enter the operations room →</button></dialog>
      <dialog class="ws-dialog" id="ws-reset"><h2>Start a new attempt?</h2><p>This clears the current attempt and its browser save. Download your report first if you want to keep it.</p><div class="ws-button-row"><button data-action="cancel-reset">Keep investigating</button><button data-action="confirm-reset" class="ws-danger">Reset this attempt</button></div></dialog>
    </div>`;
  const $ = selector => el.querySelector(selector);
  const setTab = value => {
    tab=value;
    el.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p.dataset.panel!==value);
    el.querySelectorAll('[data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===value);b.setAttribute('aria-current',b.dataset.tab===value?'page':'false');});
    update();
  };
  const hash = () => send({type:'hash',original:$('#ws-hash-a').value,changed:$('#ws-hash-b').value});
  let hashTimer;
  ['#ws-hash-a','#ws-hash-b'].forEach(id=>$(id).addEventListener('input',()=>{clearTimeout(hashTimer);hashTimer=setTimeout(hash,180);}));
  $('#ws-speed').addEventListener('change',e=>send({type:'speed',value:Number(e.target.value)}));
  $('#ws-event-filter').addEventListener('change',()=>drawEvents());
  const click = event => {
    const button=event.target.closest('button');
    if(!button || !el.contains(button)) return;
    if(button.dataset.tab) return setTab(button.dataset.tab);
    if(button.dataset.host) return send({type:'select',host:button.dataset.host});
    const action=button.dataset.action;
    if(action==='brief') return $('#ws-brief').showModal();
    if(action==='close-brief') return $('#ws-brief').close();
    if(action==='reset') return $('#ws-reset').showModal();
    if(action==='cancel-reset') return $('#ws-reset').close();
    if(action==='confirm-reset') {$('#ws-reset').close();saved=null;$('#ws-saved').hidden=true;try{localStorage.removeItem(key);}catch(_){};send({type:'reset'});return;}
    if(action==='resume') {if(saved)send({type:'restore',journal:saved});$('#ws-saved').hidden=true;saved=null;return;}
    if(action==='discard') {saved=null;$('#ws-saved').hidden=true;return;}
    if(action==='play') return send({type:state.running?'pause':'play'});
    if(action==='isolate' || action==='restore_host') return send({type:action,host:state.selected});
    if(action==='evidence') return setTab('evidence');
    if(action==='decode') return send({type:'decode',filename:$('#ws-artifact').value});
    if(action==='correlate') return send({type:'correlate',host:$('#ws-c-host').value,process:$('#ws-c-process').value,destination:$('#ws-c-destination').value});
    if(action==='payload') {$('#ws-query-input').value="' OR '1'='1";return;}
    if(action==='normal') {$('#ws-query-input').value='riley';return;}
    if(action==='query') return send({type:'query',mode:$('input[name="ws-query-mode"]:checked').value,value:$('#ws-query-input').value});
    if(action==='export') {
      const report={scenario:'Watershed / simulated incident',version:2,...state};delete report.journal;
      const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download='watershed-incident-report.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return;
    }
    if(['scan','patch','remediate','hint','finish'].includes(action)) send({type:action});
  };
  el.addEventListener('click',click);
  function drawEvents(){
    const filter=$('#ws-event-filter').value;
    const events=state.events.filter(e=>filter==='all'||e.kind===filter||(filter==='alert'&&e.kind==='critical')).slice().reverse();
    $('#ws-events').innerHTML=events.length?events.map(e=>`<div class="ws-event"><time>${e.time}</time><span class="ws-event-kind ${e.kind}">${e.kind}</span><p><b>${escape(e.host)}</b> ${escape(e.text)}</p></div>`).join(''):'<p class="ws-placeholder">No events in this category yet.</p>';
  }
  function update(){
    state=model.get('state');awaitingTick=false;
    const done=state.goals.filter(g=>g.done).length;
    $('#ws-clock').textContent=state.time;
    $('#ws-play').textContent=state.running?'Pause':state.tick?'Resume':'Start simulation';
    $('#ws-play').disabled=state.finished||state.tick>=72;
    $('#ws-speed').value=String(state.speed);
    $('#ws-status').textContent=state.finished?'Attempt complete':state.running?'Simulation running':state.tick>=72?'Scenario window ended':'Simulation paused';
    if($('#ws-notice').textContent!==state.message) $('#ws-notice').textContent=state.message;
    $('#ws-progress').innerHTML=`${done}<span>/5</span>`;
    $('#ws-beacons').innerHTML=`${state.beacons} <span>connections</span>`;
    $('#ws-bytes').textContent=`${state.bytes_sent.toLocaleString()} bytes observed · not proof of exfiltration`;
    $('#ws-availability').innerHTML=`${state.availability}<span>%</span>`;
    $('#ws-posture').textContent=state.remediated?'Recovering':state.contained?'Contained':state.file_access?'File accessed':'Investigating';
    $('#ws-posture-note').textContent=state.patched?'Portal repair applied':'Portal repair pending';
    el.classList.toggle('ws-running',state.running);
    el.classList.toggle('ws-contained',state.contained);
    el.querySelectorAll('[data-host]').forEach(b=>{
      b.classList.toggle('selected',b.dataset.host===state.selected);
      b.classList.toggle('isolated',state.isolated.includes(b.dataset.host));
      b.classList.toggle('suspect',b.dataset.host==='research-07'&&!state.remediated);
      b.querySelector('.ws-node-status').textContent=state.isolated.includes(b.dataset.host)?'Isolated':b.dataset.host==='research-07'?(state.remediated?'Recovered':'Investigate'):'Online';
      b.setAttribute('aria-pressed',String(b.dataset.host===state.selected));
    });
    el.querySelectorAll('[data-edge]').forEach(p=>{
      const endpoints={'portal-01':['portal-01','research-07'],'research-08':['research-08','archive-01'],'archive-01':['research-07','archive-01'],'research-07':['research-07']}[p.dataset.edge];
      p.classList.toggle('offline',endpoints.some(h=>state.isolated.includes(h))||(p.dataset.edge==='research-07'&&state.remediated));
    });
    const h=hosts[state.selected], isolated=state.isolated.includes(state.selected);
    const explanation=state.selected==='research-07'?(state.remediated?'Evidence preserved and sync_agent removed. Restore service when ready.':'sync_agent started at 09:14. Its purpose is unverified. Correlate the collected artifact with its destination before drawing a conclusion.'):state.selected==='research-08'?'backup_agent runs a scheduled transfer to 192.0.2.200. Regular traffic can be benign; compare this stream with the research workstation.':state.selected==='portal-01'?'The portal accepted a malformed login at 09:11. It grants sessions that can invoke research jobs. Repairing new logins does not terminate the existing process.':'Stores fictional watershed research data. Isolating the archive has a service cost and does not stop the workstation’s external route.';
    const inspectorSignature=JSON.stringify([state.selected,state.isolated,state.remediated,state.finished]);
    if(inspectorSignature!==lastInspector){lastInspector=inspectorSignature;$('#ws-inspector').innerHTML=`<div class="ws-inspector-title"><span>${h.icon}</span><div><h2>${h.name}</h2><small>${state.selected}</small></div></div><div class="ws-inspector-facts"><span>ROLE<b>${h.role}</b></span><span>STATUS<b>${isolated?'Isolated':'Online'}</b></span></div><p>${explanation}</p><div class="ws-inspector-actions"><button data-action="evidence">Open evidence lab ↗</button><button data-action="${isolated?'restore_host':'isolate'}" class="${isolated?'':'ws-danger'}" ${state.finished?'disabled':''}>${isolated?'Restore host':'Isolate host'}</button>${state.selected==='research-07'?`<button data-action="remediate" ${state.finished||state.remediated?'disabled':''}>${state.remediated?'Process removed ✓':'Remove simulated process'}</button>`:''}</div><div class="ws-callout">Containment has a cost. Watch service availability when you isolate a host.</div>`;
    }
    const plot=state.trace;
    const points=k=>plot.map(p=>`${30+p.tick/72*690},${105-p[k]*25}`).join(' ');
    $('#ws-chart').innerHTML=`<svg viewBox="0 0 750 145" role="img" aria-label="Routine and suspicious connection counts over simulated time"><g class="ws-chart-grid"><path d="M30 30H720 M30 55H720 M30 80H720 M30 105H720"/></g><polyline points="${points('routine')}" class="ws-series-routine"/><polyline points="${points('suspicious')}" class="ws-series-suspect"/><g class="ws-chart-labels"><text x="8" y="34">3</text><text x="8" y="109">0</text><text x="30" y="130">09:14</text><text x="347" y="130">09:20</text><text x="682" y="130">09:26</text></g></svg>`;
    $('#ws-chart-text').textContent=`Solid teal: routine backup records. Dashed amber: sync_agent records. ${state.beacons} suspicious connections observed; ${state.contained?'outbound route currently stopped.':'route currently available.'}`;
    $('#ws-goals').innerHTML=state.goals.map((g,i)=>`<div class="ws-goal ${g.done?'done':''}"><span>${g.done?'✓':String(i+1).padStart(2,'0')}</span><p>${g.label}</p><small>${g.done?'Complete':'Pending'}</small></div>`).join('');
    drawEvents();
    const signature=JSON.stringify([state.integrity,state.decoded,state.correlated,state.hash_result,state.query_result,state.patched]);
    if(signature!==lastEvidence){
      lastEvidence=signature;
      if(state.integrity.length) $('#ws-integrity').innerHTML=state.integrity.map(f=>`<details class="ws-file ${f.matches?'match':'changed'}"><summary><span>${f.matches?'✓':'!'}</span><b>${f.filename}</b><em>${f.matches?'Verified':'Changed'}</em></summary><p>Expected SHA-256</p><code>${f.expected}</code><p>Collected SHA-256</p><code>${f.actual}</code></details>`).join('');
      else $('#ws-integrity').textContent='Three collected files are ready to compare.';
      $('#ws-decoded').innerHTML=state.decoded?`<div class="ws-clues">${['host','username','process','event_id'].map(k=>`<div><span>${k.replace('_',' ')}</span><strong>${escape(state.decoded[k])}</strong></div>`).join('')}</div>`:'Choose an artifact based on the integrity finding.';
      $('#ws-correlated').textContent=state.correlated?'CORRELATION VERIFIED':'NOT YET VERIFIED';
      if(state.hash_result){const a=state.hash_result.original,b=state.hash_result.changed;$('#ws-hash-result').innerHTML=`<div class="ws-digest">${a.split('').map((c,i)=>`<span class="${c!==b[i]?'different':''}">${c}</span>`).join('')}</div><div class="ws-digest">${b.split('').map((c,i)=>`<span class="${c!==a[i]?'different':''}">${c}</span>`).join('')}</div><p><strong>${state.hash_result.bits}/256 bits differ.</strong> Highlighted hex digits changed. Equal inputs give equal fingerprints.</p>`;} else $('#ws-hash-result').textContent='Edit a text field to compare fingerprints.';
      const result=state.query_result;
      $('#ws-query-result').innerHTML=result?`<div class="ws-result"><span>${result.mode==='bound'?'BOUND PARAMETERS':'INPUT CONCATENATION'}</span><strong>${result.rows.length} matching users</strong><p>${result.error?escape(result.error):result.rows.length?result.rows.map(escape).join(' · '):'No matching user. This input does not identify an account.'}</p></div>`:'Run a normal lookup, then compare the test payload under both designs.';
    }
    $('#ws-system').innerHTML=`<table><thead><tr><th>UTC</th><th>Event</th><th>Process</th><th>Observation</th></tr></thead><tbody>${state.system.map(r=>`<tr><td>${r.timestamp.slice(11,19)}</td><td>${r.event_id}</td><td>${r.process}</td><td>${escape(r.message)}</td></tr>`).join('')}</tbody></table>`;
    $('#ws-patch').disabled=state.patched||state.finished;
    $('#ws-patch').textContent=state.patched?'Portal repaired ✓':'Apply portal repair';
    $('#ws-repair-status').textContent=state.patched?'New malformed logins will be rejected. Check whether the workstation still needs containment.':'Test the safer design, then deploy the repair.';
    $('#ws-finish').disabled=state.finished;
    if(tab==='debrief') $('#ws-debrief').innerHTML=`<div class="ws-review-grid"><section class="ws-card ws-score"><span class="ws-eyebrow">${state.finished?'FINAL':'LIVE'} OBJECTIVE SCORE</span><strong>${state.score}<small>/100</small></strong><p>60 evidence · 15 containment · 15 repair · 10 safe restoration</p></section><section class="ws-card"><h2>${state.finished?'Your response, explained':'Your response so far'}</h2><ul><li>${state.correlated?'You connected the artifact to an observed stream.':'An evidence link is still missing: correlate the decoded lead with traffic.'}</li><li>${state.contained?'The suspicious process is contained or removed.':'The suspicious process can still communicate.'}</li><li>${state.patched?'The portal now separates input from instructions.':'New malformed logins can still be accepted.'}</li><li>${state.file_access?'Sensitive-file access occurred during this attempt; later containment does not erase it.':'No sensitive-file access has been observed in this attempt.'}</li><li>Current service availability: ${state.availability}%. ${state.isolated.length?'Some services remain isolated.':'All services are online.'}</li></ul></section></div><section class="ws-card"><h2>Decision timeline</h2>${state.history.length?state.history.map(e=>`<div class="ws-decision"><time>${e.time}</time><div><strong>${escape(e.action)}</strong><p>${escape(e.detail)}</p></div></div>`).join(''):'<p>Your actions will appear here. Start by investigating the alert.</p>'}</section><section class="ws-card ws-limitations"><h2>What can you defend with evidence?</h2><p>A file changed; its decoded contents identify a process; that process made outbound connections. These observations do not prove what was inside the traffic. A file read is not proof of exfiltration.</p><p><strong>Discuss:</strong> What did you isolate, and why? What evidence would you request next? Did you restore service before removing the process?</p><details><summary>Understand the simulation model</summary><p>This is a deterministic classroom simulation, not a network emulator. Isolation stops the scheduled file read as a teaching simplification; actual network isolation does not prevent local file access. Availability weights and traffic counts are illustrative. One real second is ten simulated seconds at 1×. The score measures completed objectives, not overall professional competence. No AI judges your decisions.</p></details></section>`;
    if(!saved){try{localStorage.setItem(key,JSON.stringify(state.journal));}catch(_){storageWarning='Browser saving unavailable. Download your report before closing.';}}
    if(storageWarning) $('#ws-storage').textContent=storageWarning;
  }
  model.on('change:state',update);
  const interval=setInterval(()=>{if(state.running&&!awaitingTick&&!document.hidden){awaitingTick=true;send({type:'tick'});}},1000);
  // Backgrounding pauses virtual time rather than silently punishing the learner.
  const visibility=()=>{if(document.hidden&&state.running)send({type:'pause'});};
  document.addEventListener('visibilitychange',visibility);
  if(Array.isArray(saved)&&saved.length) $('#ws-saved').hidden=false; else saved=null;
  update();hash();
  return ()=>{clearInterval(interval);clearTimeout(hashTimer);model.off('change:state',update);el.removeEventListener('click',click);document.removeEventListener('visibilitychange',visibility);};
}
export default {render};
