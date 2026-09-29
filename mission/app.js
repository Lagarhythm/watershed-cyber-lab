const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Map positions are percentages of the map box; the SVG uses a 1000×420 viewBox.
const HOSTS = {
  'portal-01':   {name:'Research portal', job:'Logins for researchers', x:15, y:31, icon:'▣'},
  'research-07': {name:'Research 07', job:'Research workstation', x:47, y:44, icon:'▤'},
  'research-08': {name:'Research 08', job:'Nightly backups', x:15, y:78, icon:'▤'},
  'archive-01':  {name:'Data archive', job:'Stores research data', x:47, y:80, icon:'▥'},
};
const OUT = {library:{x:87, y:24}, unknown:{x:87, y:68}};
const pt = h => `${HOSTS[h].x*10} ${HOSTS[h].y*4.2}`;
const ROUTES = [
  {id:'portal', d:`M${pt('portal-01')} L${pt('research-07')}`, hosts:['portal-01','research-07'], kind:'routine'},
  {id:'backup', d:`M${pt('research-08')} L${pt('archive-01')}`, hosts:['research-08','archive-01'], kind:'routine'},
  {id:'library', d:`M${pt('research-07')} L790 ${OUT.library.y*4.2}`, hosts:['research-07'], kind:'routine'},
  {id:'threat', d:`M${pt('research-07')} L790 ${OUT.unknown.y*4.2}`, hosts:['research-07'], kind:'threat'},
];
const LOGIN_LOG = [
  ['09:03', 'jordan', 'username=\'jordan\'', 'success', false],
  ['09:06', 'jordan', 'username=\'jordan\'', 'success', false],
  ['09:09', 'jordan', 'username=\'jordan\'', 'success', false],
  ['09:11', '???', 'username=\'riley\' OR \'1\'=\'1\'', 'success · session DEMO-7', true],
  ['09:12', 'jordan', 'username=\'jordan\'', 'success', false],
];

function render({model, el}) {
  el.classList.add('gm-app');
  let state = model.get('state');
  let typed = '';                 // repair step: what the student has typed so far
  const send = command => model.send(command);
  const tag = (label, cls='') => `<span class="gm-tag ${cls}">${label}</span>`;
  const btn = (label, attrs, cls='') => `<button class="${cls}" ${attrs}>${label}</button>`;

  function stepper() {
    return `<ol class="gm-stepper" aria-label="Mission progress">${state.steps.map((s, i) => {
      const cls = i === state.step_index ? 'current' : s.done || i < state.step_index ? 'done' : '';
      return `<li class="${cls}" ${i === state.step_index ? 'aria-current="step"' : ''}><span>${cls === 'done' ? '✓' : i === 0 ? '★' : i === state.steps.length - 1 ? '⚑' : i}</span><small>${s.short}</small></li>`;
    }).join('')}</ol>`;
  }

  function guide() {
    const s = state.step;
    const learnWhy = (learnLabel) => `<div class="gm-block learn"><h3>${learnLabel}</h3><p>${esc(s.learning)}</p></div>
      <div class="gm-block why"><h3>WHY IT MATTERS</h3><p>${esc(s.why)}</p></div>`;
    if (s.id === 'briefing') return `
      <p class="gm-story">${esc(s.story)}</p>${learnWhy("WHAT YOU'LL LEARN")}
      <div class="gm-block do"><h3>HOW THIS WORKS</h3><ol class="gm-how">
        <li>Each step tells you <b>what you're learning</b>, <b>why it matters</b>, and exactly <b>what to do</b>.</li>
        <li>Work through the tasks using the panels on the right. You can't break anything, and wrong choices explain what happened.</li>
        <li>When all tasks are done, read <b>What you learned</b> and answer one quick question.</li>
        <li>Click <b>Next step</b>. There is no timer, so go at your own pace.</li></ol></div>
      <button class="gm-primary gm-big" data-action="next">Start the mission →</button>`;
    if (s.id === 'debrief') return `<p class="gm-story">${esc(s.story)}</p>
      <div class="gm-block learn"><h3>THE RESPONSE ORDER YOU FOLLOWED</h3><ol class="gm-how">
        <li><b>Observe</b>: know what normal looks like.</li><li><b>Verify</b>: make sure the evidence is trustworthy.</li>
        <li><b>Decode</b>: read what was left behind.</li><li><b>Connect</b>: confirm with a second source.</li>
        <li><b>Contain</b>: stop the threat with the least disruption, and test it.</li><li><b>Repair</b>: close the way in.</li>
        <li><b>Recover</b>: clean, restore, confirm.</li></ol></div>
      <button data-action="reset">Start over</button>`;
    return `<p class="gm-story">${esc(s.story)}</p>${learnWhy("WHAT YOU'RE LEARNING")}
      <div class="gm-block do"><h3>WHAT TO DO</h3><ol class="gm-tasks">${s.tasks.map(t => `<li class="${t.done ? 'done' : ''}"><span>${t.done ? '✓' : ''}</span>${esc(t.text)}</li>`).join('')}</ol></div>`;
  }

  function feedback() {
    const f = state.feedback;
    if (!f) return '';
    const jump = state.task_done && state.step.check && !state.check_passed ? '<button class="gm-link" data-action="show-learned">↓ Show me</button>' : '';
    return `<div class="gm-feedback ${f.tone}"><b>${f.tone === 'good' ? '✓' : f.tone === 'try' ? '↺' : '→'}</b><p>${esc(f.text)} ${jump}</p></div>`;
  }

  function learned() {
    const s = state.step;
    if (!state.task_done || !s.check) return '';
    return `<section class="gm-learned" id="gm-learned">
      <div class="gm-learned-text"><div><h3>✓ WHAT YOU LEARNED</h3><p>${esc(s.learned)}</p></div><div><h3>WHY IT MATTERS</h3><p>${esc(s.learned_why)}</p></div></div>
      <div class="gm-check"><h3>QUICK CHECK</h3><p class="gm-q">${esc(s.check.question)}</p>
        <div class="gm-options">${s.check.options.map((o, i) => {
          const cls = state.picked_answer === i ? (state.check_passed ? 'right' : 'wrong') : '';
          return `<button data-answer="${i}" class="${cls}" ${state.check_passed ? 'disabled' : ''}>${esc(o)}</button>`;
        }).join('')}</div>
        <button class="gm-primary gm-big" data-action="next" ${state.check_passed ? '' : 'disabled'}>${state.step_index === state.steps.length - 2 ? 'See your mission report →' : 'Next step →'}</button>
      </div></section>`;
  }

  // ---------- network map ----------
  function networkMap({mode, showTraffic, showService}) {
    const iso = state.isolated, locked = state.task_done;
    const live = r => showTraffic && !r.hosts.some(h => iso.includes(h)) && !(r.kind === 'threat' && state.killed);
    const svgRoutes = ROUTES.map(r => `<path class="gm-route ${r.kind} ${live(r) ? 'live' : 'off'}" d="${r.d}"/>` +
      (live(r) ? [0, 0.66, 1.33].map(b => `<circle class="gm-packet ${r.kind}" r="7"><animateMotion dur="2s" begin="-${b}s" repeatCount="indefinite" path="${r.d}"/></circle>`).join('') : '')).join('');
    const clickable = (mode === 'inspect' && state.observed && !locked) || (mode === 'toggle' && !locked);
    const nodes = Object.entries(HOSTS).map(([id, h]) => {
      const isolated = iso.includes(id);
      const label = state.labels[id];
      const suspect = mode === 'inspect' ? label === 'suspicious' : id === 'research-07' && state.step_index > 1 && !state.killed;
      const status = isolated ? 'ISOLATED' : id === 'research-07' && state.killed ? 'CLEANED'
        : mode === 'inspect' ? (label === 'suspicious' ? 'Needs investigation' : label === 'normal' ? 'Normal' : state.inspected.includes(id) ? 'Inspected · not labeled' : 'Not inspected')
        : suspect ? 'sync_agent running' : 'Online';
      const picked = mode === 'inspect' && state.inspecting === id;
      return `<button class="gm-node ${isolated ? 'isolated' : ''} ${suspect ? 'suspect' : ''} ${label === 'normal' && mode === 'inspect' ? 'ok' : ''} ${picked ? 'picked' : ''} ${clickable ? 'clickable' : ''}" data-host="${id}" style="left:${h.x}%;top:${h.y}%" ${clickable ? '' : 'tabindex="-1" aria-disabled="true"'} aria-label="${h.name}, ${status}">
        <span class="gm-node-icon">${isolated ? '⊘' : h.icon}</span><strong>${h.name}</strong><small>${h.job}</small><em>${status}</em></button>`;
    }).join('');
    const threatOn = live(ROUTES[3]);
    const service = showService ? `<div class="gm-meter"><div class="gm-meter-head"><span>LAB SERVICES RUNNING</span><strong>${state.availability}%</strong></div>
      <div class="gm-meter-bar"><div style="width:${state.availability}%"></div></div>
      <small>Each isolated computer stops its normal job. Research 07 = 25% · Research 08 = 20% · Portal = 45% · Archive = 10%</small></div>` : '';
    return `<div class="gm-map">
      <svg viewBox="0 0 1000 420" preserveAspectRatio="none" aria-hidden="true">
        <rect class="gm-boundary" x="20" y="20" width="620" height="380" rx="18"/>
        <text class="gm-boundary-label" x="40" y="48">INSIDE THE LAB NETWORK</text>
        <text class="gm-boundary-label out" x="700" y="48">OUTSIDE (INTERNET)</text>
        ${svgRoutes}</svg>
      ${nodes}
      <div class="gm-ext known" style="left:${OUT.library.x}%;top:${OUT.library.y}%"><span>◉</span><strong>University library</strong><small>203.0.113.80</small><em>Known website</em></div>
      <div class="gm-ext ${threatOn ? 'hot' : ''}" style="left:${OUT.unknown.x}%;top:${OUT.unknown.y}%"><span>◎</span><strong>Unknown address</strong><small>203.0.113.77</small><em>Nobody recognizes it</em></div>
    </div>
    <div class="gm-legend"><span><i class="routine"></i> Normal traffic</span><span><i class="threat"></i> Unexplained traffic</span>${showTraffic ? '' : '<span>Traffic is hidden until you click the button.</span>'}</div>
    ${service}`;
  }

  function inspector() {
    const id = state.inspecting;
    const chips = Object.entries(HOSTS).map(([h, v]) => {
      const l = state.labels[h];
      return `<span class="gm-chip ${l || ''}">${v.name}: ${l === 'suspicious' ? 'Needs investigation' : l === 'normal' ? 'Normal' : '—'}</span>`;
    }).join('');
    if (!id) return `<div class="gm-card gm-inspector"><h3>COMPUTER INSPECTOR</h3><p class="gm-hint">${state.observed ? 'Click a computer on the map to see what it is doing.' : 'Click “Show network traffic” first.'}</p><div class="gm-chips">${chips}</div></div>`;
    const info = state.host_info[id], label = state.labels[id];
    return `<div class="gm-card gm-inspector"><div class="gm-stage-head"><div><h3>COMPUTER INSPECTOR</h3><h2>${HOSTS[id].name} <small>${id}</small></h2></div></div>
      <p class="gm-hint"><b>Job:</b> ${esc(info.job)} · ${esc(info.since)}</p>
      <div class="gm-table-wrap"><table class="gm-table"><thead><tr><th>Program</th><th>Talks to</th><th>Where</th><th>What we know</th></tr></thead><tbody>
      ${info.connections.map(c => `<tr><td><code>${esc(c.program)}</code></td><td>${esc(c.to)}</td><td>${tag(c.where === 'outside' ? 'OUTSIDE' : 'INSIDE', c.where === 'outside' ? 'warn' : '')}</td><td>${esc(c.note)}</td></tr>`).join('')}</tbody></table></div>
      <div class="gm-label-row"><span>Your label for ${HOSTS[id].name}:</span>
        ${btn('Normal', `data-label="normal" ${state.task_done ? 'disabled' : ''}`, label === 'normal' ? 'on' : '')}
        ${btn('Needs investigation', `data-label="suspicious" ${state.task_done ? 'disabled' : ''}`, label === 'suspicious' ? 'on warn' : '')}</div>
      <div class="gm-chips">${chips}</div></div>`;
  }

  // ---------- step stages ----------
  function stage() {
    const id = state.step.id;
    if (id === 'briefing') return `<div class="gm-card">${networkMap({mode:'none', showTraffic:false})}</div>`;
    if (id === 'observe') return `<div class="gm-card">
      <div class="gm-stage-head"><h2>Lab network map</h2>${state.observed ? tag('LIVE TRAFFIC', 'live') : btn('▶ Show network traffic', 'data-action="observe"', 'gm-primary')}</div>
      ${networkMap({mode:'inspect', showTraffic: state.observed})}</div>${inspector()}`;
    if (id === 'integrity') return integrity();
    if (id === 'decode') return decode();
    if (id === 'correlate') return correlate();
    if (id === 'contain') return `<div class="gm-card"><div class="gm-stage-head"><h2>Containment</h2><span class="gm-hint">Click a computer to isolate it. Click again to reconnect.</span></div>
      ${networkMap({mode:'toggle', showTraffic:true, showService:true})}</div>
      <div class="gm-card"><div class="gm-stage-head"><h2>Connection test</h2>${btn('Test the connection', `data-action="verify" ${state.task_done ? 'disabled' : ''}`, 'gm-primary')}</div>
      <p class="gm-hint">Sends a harmless test from each program to where it normally connects, and reports what got through.</p>${verifyResult()}</div>`;
    if (id === 'repair') return portal();
    if (id === 'recover') return recover();
    if (id === 'debrief') return `<div class="gm-card"><div class="gm-stage-head"><h2>Mission report</h2>${tag('COMPLETE', 'live')}</div>
      <div class="gm-recap">${state.recap.map((r, i) => `<article><span>${i + 1}</span><div><h3>${esc(r.title)}</h3><p><b>Learned:</b> ${esc(r.learned)}</p><p><b>Why:</b> ${esc(r.why)}</p></div></article>`).join('')}</div></div>
      <div class="gm-card"><h2>What the evidence proves and what it doesn't</h2>
      <ul class="gm-proves"><li class="yes">A file on Research 07 was changed, and the change named sync_agent.</li><li class="yes">sync_agent sent a small message to an unknown outside address every minute.</li><li class="yes">The portal accepted an injection attack that matched every account.</li>
      <li class="no">We do <b>not</b> know what data was sent. Seeing a connection is not the same as seeing its contents.</li><li class="no">We do <b>not</b> know who the attacker is.</li></ul>
      <p class="gm-hint"><b>Discuss:</b> What evidence would you ask for next? What would you tell the lab director?</p></div>
      <div class="gm-card"><h2>Your actions</h2>${state.history.map(h => `<div class="gm-log"><span>${esc(h.step)}</span><p>${esc(h.text)}</p></div>`).join('')}</div>`;
    return '';
  }

  const groups = hex => hex.match(/.{1,8}/g).join(' ');
  function integrity() {
    const locked = state.task_done;
    const files = state.integrity.length ? state.integrity.map(f => {
      const v = state.verdicts[f.filename];
      return `<div class="gm-fprow ${v ? (v === 'match' ? 'match' : 'changed') : ''}"><div class="gm-fprow-head"><strong>${f.filename}</strong>
        <span>${btn('Matches', `data-verdict="match" data-file="${f.filename}" ${locked ? 'disabled' : ''}`, v === 'match' ? 'on' : '')}${btn('Changed', `data-verdict="changed" data-file="${f.filename}" ${locked ? 'disabled' : ''}`, v === 'changed' ? 'on warn' : '')}</span></div>
        <div class="gm-fp"><span>Trusted</span><code>${groups(f.expected)}</code><span>Today</span><code>${groups(f.actual)}</code></div></div>`;
    }).join('') : `<div class="gm-files">${state.files.map(f => `<div class="gm-file"><strong>${f}</strong><em>Trusted fingerprint on file · today's not computed</em></div>`).join('')}</div>`;
    const diff = [...state.hash_digest].filter((c, i) => c !== state.sample_digest[i]).length;
    return `<div class="gm-card"><div class="gm-stage-head"><h2>Evidence check</h2>${btn(state.integrity.length ? 'Fingerprints computed ✓' : 'Compute today’s fingerprints', `data-action="scan" ${state.integrity.length ? 'disabled' : ''}`, 'gm-primary')}</div>
      <p class="gm-hint">Files collected from Research 07. The lab saved a trusted fingerprint of each one <b>before</b> the incident.${state.integrity.length ? ' Compare the two fingerprints for each file, then mark it.' : ''}</p>${files}</div>
      <div class="gm-card gm-tester"><div class="gm-stage-head"><h2>Fingerprint tester</h2>${tag('TRY IT')}</div>
      <p class="gm-hint">Edit the text. Orange marks every character of the fingerprint that no longer matches the original.</p>
      <label class="gm-field">Text<input id="gm-hash" value="${esc(state.hash_input)}" maxlength="200" autocomplete="off" spellcheck="false" ${locked ? 'disabled' : ''}></label>
      ${digestRow('Fingerprint of the original text "' + esc(state.hash_sample) + '"', state.sample_digest, state.sample_digest)}
      ${digestRow('Fingerprint of your text', state.hash_digest, state.sample_digest)}
      <p class="gm-hint"><b>${diff} of 64</b> characters differ.${diff === 0 ? ' The fingerprints match.' : ''}</p></div>`;
  }
  function digestRow(label, digest, base) {
    return `<div class="gm-digest"><span>${label}</span><div>${[...digest].map((c, i) => `<i class="${c !== base[i] ? 'diff' : ''}">${c}</i>`).join('')}</div></div>`;
  }

  function decode() {
    const verdict = f => { const r = state.integrity.find(x => x.filename === f); return r ? (r.matches ? 'match' : 'changed') : ''; };
    const files = `<div class="gm-files">${state.files.map(f => `<button class="gm-file ${verdict(f)} ${state.opened === f ? 'picked' : ''}" data-open="${f}" ${state.opened ? 'disabled' : ''}><strong>${f}</strong><em>${verdict(f) === 'changed' ? '! Changed in Step 2' : '✓ Matched in Step 2'}</em></button>`).join('')}</div>`;
    let body = '';
    if (state.opened) {
      body += `<h3 class="gm-sub">CONTENTS OF ${state.opened.toUpperCase()}</h3><code class="gm-encoded">${esc(state.encoded)}</code>`;
      body += `<h3 class="gm-sub">WHAT KIND OF TEXT IS THIS?</h3><div class="gm-options">${state.format_options.map(([k, l]) => btn(esc(l), `data-format="${k}" ${state.format_ok ? 'disabled' : ''}`, state.format_ok && k === 'base64' ? 'right' : '')).join('')}</div>`;
    }
    if (state.decoded) {
      const next = state.clue_slots.find(([k]) => !(k in state.clues));
      body += `<div class="gm-arrow">↓ Base64 decoded, no key needed ↓</div>
        <div class="gm-decode-grid"><div><h3 class="gm-sub">DECODED TEXT (click the values)</h3><div class="gm-json">{${Object.entries(state.decoded).map(([k, v]) => `<div>&nbsp;&nbsp;"${k}": ${k === 'note' ? `"${esc(v)}"` : `<button class="gm-token ${state.clues[k] ? 'used' : ''}" data-clue="${k}" ${state.task_done ? 'disabled' : ''}>"${esc(v)}"</button>`},</div>`).join('')}}</div></div>
        <div class="gm-clue-card"><h3>CLUE CARD</h3>${state.clue_slots.map(([k, l]) => `<div class="gm-slot ${state.clues[k] ? 'filled' : next && next[0] === k ? 'next' : ''}"><span>${l}</span><strong>${state.clues[k] ? esc(state.clues[k]) : next && next[0] === k ? `← click the ${l.toLowerCase()}` : '…'}</strong></div>`).join('')}</div></div>`;
    }
    return `<div class="gm-card"><div class="gm-stage-head"><h2>Artifact decoder</h2></div>
      <p class="gm-hint">${state.opened ? '' : 'Open a file. Your Step 2 results are shown on each one.'}</p>${files}${body}</div>`;
  }

  function correlate() {
    const d = state.decoded || {};
    const opt = (v, cur, label) => `<option value="${v}" ${v === cur ? 'selected' : ''}>${label}</option>`;
    const rows = state.network.slice(0, 60).map(r => `<tr><td>${r.time}</td><td>${r.host}</td><td><code>${r.process}</code></td><td><code>${r.destination}</code></td><td>${r.bytes.toLocaleString()}</td></tr>`).join('');
    return `<div class="gm-card"><div class="gm-correlate">
      <div class="gm-clue-card"><h3>YOUR CLUE (FROM STEP 3)</h3><div class="gm-slot filled"><span>Computer</span><strong>${esc(d.host)}</strong></div><div class="gm-slot filled"><span>Program</span><strong>${esc(d.process)}</strong></div></div>
      <div><h2>Network log</h2><p class="gm-hint">Every connection the lab network recorded this morning. Use the filters.</p>
        <div class="gm-filters"><label>Computer<select id="gm-f-host" ${state.task_done ? 'disabled' : ''}>${opt('', state.filter_host, 'All computers')}${state.hosts.map(h => opt(h, state.filter_host, h)).join('')}</select></label>
        <label>Program<select id="gm-f-proc" ${state.task_done ? 'disabled' : ''}>${opt('', state.filter_process, 'All programs')}${state.processes.map(p => opt(p, state.filter_process, p)).join('')}</select></label>
        <span class="gm-count">Showing <b>${state.network.length}</b> of ${state.network_total} records</span></div></div></div>
      <div class="gm-table-wrap tall"><table class="gm-table"><thead><tr><th>Time</th><th>Computer</th><th>Program</th><th>Sending to</th><th>Bytes</th></tr></thead><tbody>${rows}</tbody></table></div>
      <h3 class="gm-sub">WHERE IS THE CLUE'S PROGRAM SENDING DATA?</h3>
      <div class="gm-button-row">${state.destinations.map(ip => btn(`<code>${ip}</code>`, `data-dest="${ip}" ${state.task_done ? 'disabled' : ''}`, state.destination === ip ? (ip === '203.0.113.77' ? 'right' : 'wrong') : '')).join('')}</div></div>`;
  }

  function verifyResult() {
    const v = state.verify_result;
    if (!v) return '<p class="gm-hint">No test run yet.</p>';
    const line = (prog, dest, reached, shouldReach) => `<div class="gm-test ${reached === shouldReach ? 'good' : 'bad'}"><code>${prog}</code><span>→ ${dest}</span><b>${reached ? 'REACHED' : 'BLOCKED'}</b></div>`;
    return `<div class="gm-tests">${line('sync_agent (Research 07)', '203.0.113.77', !v.blocked, false)}
      ${line('backup_agent (Research 08)', 'Data archive', v.others_ok.includes('research-08') && v.others_ok.includes('archive-01'), true)}
      ${line('web_portal (Portal)', 'Researchers', v.others_ok.includes('portal-01'), true)}</div>`;
  }

  function sqlPreview(value, mode) {
    if (!value) return '<p class="gm-hint">Start typing to see the command the portal builds.</p>';
    if (mode === 'bound') return `<div class="gm-sql"><span class="kw">SELECT</span> username <span class="kw">FROM</span> users <span class="kw">WHERE</span> username = <mark class="slot">?</mark></div>
      <div class="gm-sealed"><span>SENT SEPARATELY AS DATA</span><code>${esc(value)}</code></div>
      <p class="gm-hint"><b>The command and your typing travel separately.</b> The database fills the <b>?</b> slot with your text as a plain name.</p>`;
    const q = value.indexOf("'");
    const html = q < 0 ? `<mark class="data">${esc(value)}</mark>` : `${q ? `<mark class="data">${esc(value.slice(0, q))}</mark>` : ''}<mark class="cmd">${esc(value.slice(q))}</mark>`;
    return `<div class="gm-sql"><span class="kw">SELECT</span> username <span class="kw">FROM</span> users <span class="kw">WHERE</span> username = '${html}'</div>
      <p class="gm-hint">${q < 0 ? '<b class="ok">Teal = your typing, used as a name.</b> It is pasted straight into the command.' : '<b class="warn">Red = your typing is now part of the command.</b> Your quote mark closed the name early, so everything after it is read as instructions.'}</p>`;
  }

  function portal() {
    const q = state.last_query, mode = state.portal_mode, locked = state.task_done;
    const users = ['riley', 'jordan', "o'neil"];
    return `<div class="gm-card"><div class="gm-stage-head"><h2>Portal login log</h2>${tag('EVIDENCE')}</div>
      <div class="gm-table-wrap"><table class="gm-table"><thead><tr><th>Time</th><th>Account</th><th>What the portal checked</th><th>Result</th></tr></thead><tbody>
      ${LOGIN_LOG.map(([t, a, c, r, hot]) => `<tr class="${hot ? 'hot' : ''}"><td>${t}</td><td>${a}</td><td><code>${esc(c)}</code></td><td>${r}</td></tr>`).join('')}</tbody></table></div>
      <p class="gm-hint">Normal logins look like <code>username='jordan'</code>. The one at 09:11 does not.</p></div>
      <div class="gm-card"><div class="gm-stage-head"><h2>Portal login test</h2>${state.patched ? tag('FIX APPLIED', 'live') : ''}</div>
      <div class="gm-mode" role="radiogroup" aria-label="Portal version">
        <button role="radio" aria-checked="${mode === 'unsafe'}" class="${mode === 'unsafe' ? 'on' : ''}" data-mode="unsafe" ${locked ? 'disabled' : ''}><strong>ORIGINAL portal</strong><small>Pastes your typing into the command</small></button>
        <button role="radio" aria-checked="${mode === 'bound'}" class="${mode === 'bound' ? 'on' : ''}" data-mode="bound" ${locked ? 'disabled' : ''}><strong>FIXED portal</strong><small>Parameterized query: typing stays separate</small></button></div>
      <form class="gm-loginbox" data-form="login"><label class="gm-field">Username<input id="gm-user" value="${esc(typed)}" maxlength="80" autocomplete="off" spellcheck="false" placeholder="Type a username" ${locked ? 'disabled' : ''}></label>
        <button type="submit" class="gm-primary" ${locked ? 'disabled' : ''}>Log in</button></form>
      <div class="gm-db"><h3>WHAT THE DATABASE WILL RUN</h3><div id="gm-sql-live">${sqlPreview(typed, mode)}</div>
        ${q ? `<h3>RESULT FOR <code>${esc(q.input)}</code> · ${q.mode === 'bound' ? 'FIXED' : 'ORIGINAL'} PORTAL</h3>
        ${q.error ? `<p class="gm-alarm">${esc(q.error)}</p>` : `<div class="gm-users">${users.map(u => `<span class="${q.rows.includes(u) ? 'hit' : ''}">👤 ${esc(u)}</span>`).join('')}<b>${q.rows.length} account${q.rows.length === 1 ? '' : 's'} matched</b></div>`}
        ${q.mode === 'unsafe' && q.rows.length > 1 ? '<p class="gm-alarm">In this simplified portal, a match means you are logged in. The attacker got in as riley without knowing riley’s password.</p>' : ''}` : ''}</div>
      <div class="gm-button-row">${state.attack_misses ? btn('Stuck? Show me what the attacker typed', 'data-action="hint"') : ''}
        ${btn(state.patched ? 'Fix applied to the portal ✓' : 'Apply the fix to the portal', `data-action="patch" ${state.patched ? 'disabled' : ''}`, 'gm-primary')}</div></div>`;
  }

  function recover() {
    const locked = state.task_done;
    const procs = state.process_list.map(p => `<tr><td><code>${p.name}</code></td><td>${esc(p.what)}</td><td>${esc(p.since)}</td>
      <td>${p.name === 'sync_agent' && state.killed ? tag('ENDED', 'live') : btn('End program', `data-kill="${p.name}" ${state.killed || locked ? 'disabled' : ''}`)}</td></tr>`).join('');
    const final = state.confirmed ? `<div class="gm-tests"><div class="gm-test good"><code>browser</code><span>→ 203.0.113.80 library</span><b>NORMAL</b></div>
      <div class="gm-test good"><code>resolver</code><span>→ 192.0.2.53 name server</span><b>NORMAL</b></div>
      <div class="gm-test good"><code>sync_agent</code><span>→ 203.0.113.77</span><b>NO TRAFFIC</b></div></div>` : '';
    return `<div class="gm-card"><div class="gm-stage-head"><h2>Research 07</h2>${tag(state.reconnected ? 'ONLINE' : 'ISOLATED', state.reconnected ? 'live' : 'warn')}</div>
      <h3 class="gm-sub">A · PROGRAMS RUNNING NOW</h3>
      <div class="gm-table-wrap"><table class="gm-table"><thead><tr><th>Program</th><th>What it is</th><th>Started</th><th></th></tr></thead><tbody>${procs}</tbody></table></div>
      <h3 class="gm-sub">B · THE CHANGED FILE: collector_config.txt</h3>
      <div class="gm-options">${state.config_options.map(([k, l]) => btn(esc(l), `data-config="${k}" ${state.config === 'restore' || locked ? 'disabled' : ''}`, state.config === k ? 'right' : '')).join('')}</div>
      <h3 class="gm-sub">C · BRING IT BACK</h3>
      <div class="gm-button-row">${btn(state.reconnected ? 'Reconnected ✓' : 'Reconnect Research 07', `data-action="reconnect" ${state.reconnected ? 'disabled' : ''}`, state.reconnected ? '' : 'gm-primary')}
        ${btn(state.confirmed ? 'Check complete ✓' : 'Run final traffic check', `data-action="confirm" ${state.confirmed ? 'disabled' : ''}`, state.reconnected && !state.confirmed ? 'gm-primary' : '')}</div>${final}</div>
      <div class="gm-card">${networkMap({mode:'none', showTraffic:true, showService:true})}</div>`;
  }

  // ---------- page ----------
  function draw() {
    const a = document.activeElement;
    const focus = a && el.contains(a) && a.id ? [a.id, a.selectionStart, a.selectionEnd] : null;
    const s = state.step;
    el.innerHTML = `<div class="gm-shell">
      <header class="gm-header"><div class="gm-brand"><span class="gm-logo">◈</span><div><span class="gm-eyebrow">GUIDED MISSION</span><h1>The Watershed Incident</h1></div></div>${tag('FICTIONAL TRAINING ENVIRONMENT')}</header>
      ${stepper()}
      <div class="gm-grid">
        <aside class="gm-guide"><span class="gm-eyebrow">${state.step_index === 0 ? 'MISSION BRIEFING' : state.step_index === state.steps.length - 1 ? 'DEBRIEF' : `STEP ${state.step_index} OF ${state.steps.length - 2}`}</span>
          <h2>${esc(s.title.split(' · ').pop())}</h2>${guide()}<div aria-live="polite">${feedback()}</div></aside>
        <main class="gm-stage">${stage()}</main>
      </div>
      ${learned()}
      <footer><span>All computers, addresses and people are fictional. Nothing here touches a real network.</span>${state.step_index > 0 ? '<button class="gm-link" data-action="reset">Restart mission</button>' : ''}</footer>
    </div>`;
    if (focus) {
      const i = el.querySelector('#' + focus[0]);
      if (i && !i.disabled) { i.focus({preventScroll:true}); if (focus[1] != null && i.setSelectionRange) i.setSelectionRange(focus[1], focus[2]); }
    }
  }

  let hashTimer, lastStep = state.step_index;
  const click = event => {
    const b = event.target.closest('button');
    if (!b || !el.contains(b) || b.disabled || b.closest('form')) return;   // the login form handles its own submit
    const d = b.dataset;
    if (d.host) return send({type: state.step.id === 'contain' ? 'toggle' : 'inspect', host: d.host});
    if (d.label) return send({type:'label', host:state.inspecting, verdict:d.label});
    if (d.answer) return send({type:'answer', choice:Number(d.answer)});
    if (d.verdict) return send({type:'verdict', filename:d.file, verdict:d.verdict});
    if (d.open) return send({type:'open', filename:d.open});
    if (d.format) return send({type:'format', choice:d.format});
    if (d.clue) return send({type:'clue', key:d.clue});
    if (d.dest) return send({type:'destination', ip:d.dest});
    if (d.mode) return send({type:'mode', mode:d.mode});
    if (d.kill) return send({type:'kill', process:d.kill});
    if (d.config) return send({type:'config', choice:d.config});
    const a = d.action;
    // The only scroll the student ever gets is one they asked for.
    if (a === 'show-learned') return el.querySelector('#gm-learned')?.scrollIntoView({behavior:'smooth', block:'start'});
    if (a === 'hint') { typed = "riley' OR '1'='1"; }
    if (a === 'reset' && !confirm('Restart the mission from the beginning?')) return;
    if (a) send({type:a});
  };
  const input = event => {
    const t = event.target;
    if (t.id === 'gm-hash') { clearTimeout(hashTimer); hashTimer = setTimeout(() => send({type:'hash', text:t.value}), 150); }
    if (t.id === 'gm-user') { typed = t.value; el.querySelector('#gm-sql-live').innerHTML = sqlPreview(typed, state.portal_mode); }
  };
  const change = event => {
    if (event.target.id === 'gm-f-host' || event.target.id === 'gm-f-proc')
      send({type:'filter', host:el.querySelector('#gm-f-host').value, process:el.querySelector('#gm-f-proc').value});
  };
  const submit = event => {
    if (event.target.dataset.form !== 'login') return;
    event.preventDefault();
    send({type:'login', value:typed});
  };
  const listeners = {click, input, change, submit};
  Object.entries(listeners).forEach(([n, f]) => el.addEventListener(n, f));
  const update = () => {
    state = model.get('state');
    const stepChanged = state.step_index !== lastStep;
    if (stepChanged) typed = '';
    draw();
    // A new step starts at its top, but only if that top is scrolled out of view. Task results never move the page.
    if (stepChanged && el.getBoundingClientRect().top < 0) el.scrollIntoView({block:'start'});
    lastStep = state.step_index;
  };
  model.on('change:state', update);
  draw();
  return () => { clearTimeout(hashTimer); model.off('change:state', update); Object.entries(listeners).forEach(([n, f]) => el.removeEventListener(n, f)); };
}
export default {render};
