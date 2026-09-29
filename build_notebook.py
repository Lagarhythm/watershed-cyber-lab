from pathlib import Path
import nbformat as n
ROOT=Path(__file__).parent
cells=[]
def md(s): cells.append(n.v4.new_markdown_cell(s))
def code(s): cells.append(n.v4.new_code_cell(s))
def lesson(anchor,title,text,value):
    md(f'<a id="{anchor}"></a>\n## {title}\n\n{text}\n\n<details><summary>Why teach this in Jupyter?</summary>\n\n{value}\n\n</details>')
md('''# The Watershed Incident
### An interactive cybersecurity teaching laboratory
**Teach → Practice → Apply → Investigate** · 60–75 minutes · CPU only · Offline after setup

A fictional research workstation is making unfamiliar outbound connections. You are the junior analyst assigned to reconstruct the incident from collected evidence. Your goal is an evidence-supported explanation, not a guess at a hidden string.

**You will:** verify file integrity, decode an artifact, filter logs, correlate network telemetry, repair a SQL query, and reconstruct a timeline.

[Briefing](#briefing) · [Integrity](#integrity) · [Artifacts](#artifacts) · [Logs](#logs) · [Network](#network) · [Secure code](#code) · [Investigation](#investigation) · [Instructor view](#instructor)

**Start here:** select the Python kernel installed using `README.md`, then **Run → Run All Cells**. A failed secure-code check is an intentional exercise, not a notebook error. Work through the controls from top to bottom. To edit code, change the cell and press **Shift+Enter**. Save the notebook with **Ctrl+S**. Progress is saved separately in `.progress/session.json`.

All evidence is synthetic. Addresses describe fictional observations and are never contacted. All times are UTC. This notebook performs no scanning or external exploitation.''')
code('''from pathlib import Path
import sys
# Works when launched from this folder or its parent.
ROOT = Path.cwd()
if not (ROOT / "lab.py").exists():
    ROOT = ROOT / "cybersecurity_showcase"
if not (ROOT / "lab.py").exists():
    raise FileNotFoundError("Open the notebook from the cybersecurity_showcase folder; see README.md.")
sys.path.insert(0, str(ROOT))
import hashlib, base64, json, sqlite3
import pandas as pd
from IPython.display import display, HTML
from lab import (Investigation, load_table, hash_lab, artifact_lab, explorer,
                 practice, assess_code, instructor_panel)
case = Investigation()
display(HTML("<div style='padding:18px;border-left:6px solid #245a81;background:#eef5fa;color:#172b3a'><b>CASE 07 · WATERSHED</b><br>Observe → test → connect evidence → explain</div>"))
display(case.progress())
if case.storage_message: print(case.storage_message)
print("Ready. Interact with the controls below; no Internet connection is required.")''')
lesson('briefing','01 · Mission briefing','''The evidence packet contains a trusted pre-incident hash manifest, three collected files, authentication logs, system events, network telemetry, and a toy portal query. The manifest is supplied by the fictional response team; it is not recomputed from the collected files.

![Evidence moves from the trusted manifest through artifact, logs, network and code to a reconstructed timeline.](assets/evidence_flow.svg)

**Evidence flow:** trusted manifest → collected artifact → account/process clue → system event → network correlation → application review → incident timeline.

**Practice:** inspect the inventory below. **Apply:** distinguish an observation (“the bytes changed”) from a conclusion (“this was malicious”). During the final investigation you will submit one finding per stage. Three progressive hints are available at each stage.

**Success:** support your timeline with event IDs and timestamps. The final token is generated only after all six stages are accepted.''','Markdown, a persistent progress indicator, and the evidence inventory give learners one navigable environment. The instructor can connect explanation, action, and feedback without moving between tools.')
code('''manifest = load_table("evidence_manifest.csv")
auth = load_table("authentication_logs.csv")
system = load_table("system_events.csv")
network = load_table("network_traffic.csv")
display(pd.DataFrame({"Evidence": ["Trusted manifest", "Authentication", "System events", "Network telemetry"],
                      "Records": [len(manifest), len(auth), len(system), len(network)]}))''')
lesson('integrity','02 · Hashing and file integrity','''SHA-256 produces a 256-bit fingerprint of bytes. Identical bytes produce an identical digest; changing the input usually changes many output bits. A hash does not encrypt the content or explain why a file changed.

**Practice:** change one character, then make both text inputs identical. Check your prediction.

**Apply:** execute the comparison below. Which collected file differs from the trusted manifest? Record its filename for CTF stage 1.''','A text widget makes a mathematical property observable. Learners test a prediction, then apply the same operation to real file bytes. The code cell exposes the method so they can adapt it.')
code('display(hash_lab(case))')
code('''integrity = manifest.copy()
integrity["actual_sha256"] = integrity.filename.map(lambda name: hashlib.sha256((ROOT / "data" / name).read_bytes()).hexdigest())
integrity["matches"] = integrity.expected_sha256 == integrity.actual_sha256
display(integrity)''')
lesson('artifacts','03 · Encoding and artifact analysis','''**Encoding** changes representation and is reversible without a secret (Base64). **Encryption** protects content using a key. **Hashing** produces a fingerprint and is not a reversible representation.

**Practice:** select a collected file and inspect its bytes as text. Try Base64 decoding; a clear message handles files that are not Base64.

**Apply:** decode the file identified by the integrity comparison. Record its `username`, `host`, `process`, and `event_id`. These are leads to verify against independent logs in CTF stages 2–3.''','File reading and decoding happen next to the explanation. A checkbox reveals the next layer of evidence, while feedback distinguishes a bad format assumption from a broken notebook.')
code('display(artifact_lab(case))')
md('''Optional executable method: replace the filename below with the artifact you selected, then run. Decoding a file does not execute its contents.''')
code('''artifact_name = "readme.txt"  # Change to the file you want to inspect.
raw = (ROOT / "data" / artifact_name).read_bytes()
print(raw.decode())
# For a Base64 artifact: print(base64.b64decode(raw.strip(), validate=True).decode())''')
lesson('logs','04 · Security log analysis','''Logs describe observations, not necessarily intent. Combine **host + username + process + time** to avoid confusing unrelated events. Filter each table and choose a sort column; search matches literal text across columns.

**Practice:** find a routine `backup_agent` event in system logs. **Apply:** use the decoded clues to locate a `process_start` event. Record its event ID and UTC timestamp. Also inspect the unusual portal login and its linked session. CTF stage 3 asks for the process-start event ID.''','Dropdowns let students begin with analytical reasoning, then the pandas example reveals how the same filter becomes code. Sort controls and a changing chart show the effect of each selection.')
code('display(explorer(auth))\ndisplay(explorer(system))')
code('''# Equivalent filtering in pandas: change the host to investigate another system.
display(system.loc[system["host"].eq("research-08")].sort_values("timestamp"))
display(practice(case, "Log analysis", "Which host runs the routine backup_agent? Submit the host name.",
                 "research-08", "Filter the system log by process or search backup_agent; compare the host column."))''')
lesson('network','05 · Follow the network evidence','''A connection record gives source, destination, port, protocol, process, time, and bytes sent. Frequent, regular connections may be a clue; backups and monitoring can also be periodic. Port 443 alone cannot establish that traffic is harmless or even prove the application protocol.

**Practice:** compare hosts and select TCP or UDP. **Apply:** filter by the host and process recovered from the artifact. Compare the first connection with the process-start event, then identify the repeating destination for CTF stage 4. The table provides exact values alongside the chart.

The observations support suspicious outbound communication. They do **not** establish the contents of the traffic or prove that the later file read resulted in exfiltration.''','Widget-controlled tables and charts keep the evidence visible while learners change hypotheses. A written chart description and the underlying table make the comparison usable without relying on color.')
code('display(explorer(network, network=True))')
code('''display(practice(case, "Network analysis", "Which protocol appears on destination port 53 in this evidence?",
                 "UDP", "Search 53 and inspect the protocol column. This conclusion applies to these records, not every service on that port."))
# Reusable analysis pattern: count observations for each destination.
display(network.groupby(["host", "process", "destination_ip"]).size().rename("connections").reset_index())''')
lesson('code','06 · Repair a vulnerable query','''The fictional portal grants a session when this lookup returns a user. Concatenating input into SQL lets input alter the query's meaning: **SQL injection**. In the incident, a granted session was then used to invoke an existing research job runner. SQL injection alone does not imply arbitrary code execution; the linked job event supplies that next step.

**Practice:** inspect the function, then run the checks. The initial failures are expected.

**Apply:** edit `lookup_user` so the SQL contains a `?` placeholder and pass `(username,)` separately to `connection.execute`. Keep `.fetchall()`. Rerun the function cell and check cell. All five checks should pass before CTF stage 5 can be completed.

The database is created in memory for each check and contains only three fictional names.''','Students modify executable code and see behavior-based assessment immediately. Checks cover ordinary functionality, apostrophes, hostile input, and separation of query from parameters. This tests a transferable repair, not memorization of a flag.')
code('''def lookup_user(connection, username):
    # TODO: replace this unsafe concatenation with a bound parameter.
    query = "SELECT username FROM users WHERE username = '" + username + "'"
    return connection.execute(query).fetchall()''')
code('code_results = assess_code(case, lookup_user)')
lesson('investigation','07 · Reconstruct the Watershed incident','''Use your findings to complete the connected investigation. Stages unlock in order. A wrong answer keeps the stage open and provides guidance; hints reveal a concept, direction, then method.

1. Submit the modified **filename**.
2. Submit the decoded **username**.
3. Submit the matching **process-start event ID**.
4. Submit the correlated outbound **destination IP**.
5. Name the **vulnerability**, and pass the secure-code checks above.
6. Assign **ranks 1–6**, earliest first, using each rank once.

Keep a short evidence-based case note in the Markdown cell below. Automated checks assess the findings and ordering; your instructor reviews the strength and limitations of your explanation.''','Persistent state links six skills into one investigation. Ordered checks discourage skipping the evidence chain, hints support recovery, and the completion token rewards the finished case. Local Python assessment is formative, not a secure exam boundary.')
code('''for stage in range(6):
    display(case.challenge(stage))
display(case.progress())''')
md('''### Analyst case note — double-click to edit
- Initial access and supporting event:
- Artifact integrity finding and decoded lead:
- Process event and first correlated connection:
- Sensitive-file observation:
- What the evidence does **not** prove:
- One next investigative question:

**Debrief:** Why is a mismatch not proof of malware? What benign explanation could fit periodic traffic? Which independent records make your conclusion stronger?''')
lesson('instructor','08 · Instructor view and reuse','''The optional view below shows the live anonymous session and a separately labeled simulated cohort. It is hidden by default. It can demonstrate where additional scaffolding may help; it is not a central learning-management system.

Open `instructor/DEMO_SCRIPT.md` for a short faculty presentation and `instructor/CUSTOMIZATION_GUIDE.md` to adapt a pattern to your discipline. Reset clears local progress; restart and run all cells afterward to clear old outputs. Save a student distribution with outputs cleared.''','Local attempts and hint counts make learning difficulties visible. A simulated cohort illustrates the next integration step without implying that real student records are being collected. The same observe → filter → explain → check pattern transfers to scientific and engineering datasets.')
code('display(instructor_panel(case))')
nb=n.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (Watershed lab)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'},'title':'The Watershed Incident'})
n.validate(nb); n.write(nb,ROOT/'Cybersecurity_Interactive_Lab.ipynb')
