# Product Requirements Document, v2 (as built)
## Interactive Cybersecurity Teaching Demonstration: Watershed Incident

| | |
|---|---|
| **Status** | As built, 2026-09-28 |
| **Supersedes** | v1 PRD "Interactive Cybersecurity Teaching Demonstration Notebook" (2026-09-27). v1's vision, principles, safety and data rules still apply; this version records what changed and why. |
| **Repository** | `github.com/Lagarhythm/watershed-cyber-lab` |
| **Use as a template** | Section 9 is the build playbook and Section 10 is the checklist for a new lab. |

---

## 1. What changed from v1, and why

v1 described one code-based Jupyter notebook. Building and trying it produced three layers, and the student entry point moved to the simplest one.

| v1 said | As built | Why |
|---|---|---|
| A notebook students run cell by cell | Students open a **web page** (Voilà renders the notebook as an app, code hidden). The code notebook is an optional companion. | Running cells, kernels and code was a barrier for students and for faculty evaluating the demo. |
| Teach → Practice → Apply → Investigate across notebook sections | **Guided Mission**: 7 steps, each Learn → Why → Do (3–5 tasks) → Learned → Check. | The free-play simulator was "really cool but WAY too complicated". Students need to be walked through what they're doing and why. |
| Final multi-stage CTF with a flag | The mission itself is the investigation, with no flag. The flag-based CTF stays in the companion notebook. | One continuous story beats a lesson series plus a separate exam. |
| Progressive 3-level hints | 3-level hints in the companion notebook. The mission teaches before each task, explains every wrong choice, and offers a "Stuck? Show me" hint where students type free text (SQL injection). | Guidance up front made most hints unnecessary. |
| Instructor view with progress analytics | Companion notebook: local progress plus a *simulated* cohort view. Mission: none yet. | A real cohort view needs a server (JupyterHub/LMS). See Section 11. |
| Jupyter Notebook or JupyterLab | Voilà 0.5 + anywidget, **ipykernel pinned below 7**, bundled offline Voilà template, `start.sh` one-command launcher. | Voilà hangs on ipykernel 7. The stock template loads fonts from a CDN, which breaks the offline requirement. |
| Runs within JupyterHub | Runs standalone on a laptop or Jetstream2 VM. LMS launch through JupyterHub + LTI 1.3 proven in a local testbed. | Faculty will want to launch labs from Canvas. |

---

## 2. Product overview (as built)

Three surfaces share one fictional incident and one evidence set:

1. **Guided Mission** (default, `./start.sh`): the student product. Graphical, no code, no clock, about 30 minutes.
2. **Free-play dashboard** (`./start.sh --full`): the same incident as an open simulation with a clock, scoring and exportable debrief. Good for live faculty demos and students who finished the mission.
3. **Code companion** (`Cybersecurity_Interactive_Lab.ipynb`): the v1 notebook. pandas explorers, editable secure-code exercise, 6-stage CTF, hints, progress, instructor mode. For courses where students should read and write Python.

The v1 product principle is unchanged: *the cybersecurity lesson demonstrates what students can learn; the notebook demonstrates what instructors can build.*

---

## 3. Users and the simplest path for each

| User | Path | Steps |
|---|---|---|
| Student (own machine or Jetstream2 VM) | `git clone` → `./start.sh` → open `http://127.0.0.1:8866` | 3 |
| Student (via LMS, future) | Click the assignment in Canvas | 1 |
| Instructor editing the lesson | Edit wording in `STEPS` in `mission/engine.py`, re-run `./start.sh` | 2 |
| Instructor distributing offline | `python package_student.py` → hand out the ZIP (contains `start.sh`) | 2 |
| Faculty evaluator | Watch the free-play dashboard demo (`instructor/DEMO_SCRIPT.md`, `SIMULATION_GUIDE.md`) | 0 setup |

**Simplicity requirement:** a student must never need to create a virtual environment, choose a kernel, run a cell, or see code to do the mission. `start.sh` creates `.venv` on first run and reinstalls only when `requirements.txt` changes. Windows uses the documented manual steps.

---

## 4. Guided lesson design rules

These came out of review of the first guided version. Apply them to every future lab.

1. **Order on screen:** *What you're learning* → *Why it matters* → *What to do* checklist. Explanation comes before the task, not after.
2. **Tasks have 3–5 parts.** No step is "click one button". Examples: inspect all four computers *then* label each; compare hashes by hand *then* break and restore the tester; open the file → identify the encoding → pull clues into a card.
3. **After the task:** *What you learned* + *Why*, then one multiple-choice **quick check** that unlocks **Next**.
4. **Wrong choices explain instead of block.** Feedback says why the choice is wrong (e.g. "leaves the lab" alone is not suspicious; the browser does that too).
5. **Never move the page on its own.** No auto-scroll when a task completes. Only a user-clicked "↓ Show me", and on **Next** only when the top is off-screen. The browser test asserts `scrollY` is unchanged.
6. **No clock in the guided version.** Time pressure lives in the free-play dashboard.
7. **Stage locks:** once a step's task is complete its controls lock, so students can't undo their way into an inconsistent state.
8. **All wording in one data structure** (`STEPS`, `HOST_INFO`, `PROCESSES`) so instructors edit text, not UI code.
9. **Graphics are driven by state**, never decorative (the map, packets and service meter all reflect the engine).
10. **Accessibility:** status in text as well as color, keyboard-reachable controls, `aria-` labels, `prefers-reduced-motion` support, readable on a 390-pixel phone. A full screen-reader audit has not been done.

---

## 5. Scenario and mission steps (as built)

**Story:** Monday morning at the Watershed Research Lab. Four computers: `portal-01`, `research-07`, `research-08`, `archive-01`. An attacker used SQL injection on the research portal (`riley' OR '1'='1`), which led to a new program, `sync_agent`, starting on `research-07` at 09:14. It loaded a modified `collector_config.txt` (Base64 JSON clue) and beacons to `203.0.113.77` every minute.

| Step | Student does (3–5 parts) | Concept | v1 phase |
|---|---|---|---|
| Briefing | Read the role and objective | Incident-response order | 1 Mission briefing |
| 1 Observe | Show traffic, inspect all 4 computers, label each Normal / Needs investigation | Baseline vs. anomaly | 5 Network |
| 2 Verify | Compare trusted vs. current SHA-256 by hand; change and restore the tester text | Hashing, integrity | 2 Hashing |
| 3 Decode | Open the changed file, identify Base64 (not encryption), click values into a clue card | Encoding vs. encryption | 3 Encoding |
| 4 Connect | Filter the real 54-row `network_traffic.csv` by computer (24) → program (8) → pick destination | Correlation across sources | 4 Logs + 5 Network |
| 5 Contain | Isolate only Research 07 (75% service kept), run a connection test | Containment tradeoff, verify actions | new |
| 6 Repair | Type usernames with live SQL preview; reproduce the attack from the login log; test the fixed portal (attack blocked, `o'neil` works); apply | SQL injection, parameterized queries | 6 Secure coding |
| 7 Recover | End only `sync_agent` → restore the trusted config → reconnect → final check | Recovery order | new |
| Debrief | Review what was learned; discussion prompts | | 7 CTF reconstruction |

All evidence is synthetic, generated deterministically by `make_data.py`. Addresses use documentation ranges (192.0.2.0/24, 203.0.113.0/24). The engine never opens sockets, starts processes or touches real hosts.

---

## 6. Architecture (reusable pattern)

```text
start.sh                one command: create .venv, install when requirements change, launch
launch.py               starts Voilà on 127.0.0.1 with the bundled template; --full picks the dashboard
jupyter/voila/templates/watershed/   offline Voilà template (no CDN fonts)
Guided_Mission.ipynb    ONE hidden cell: `from mission import GuidedMission; GuidedMission()`
build_mission.py        regenerates that notebook (never hand-edit)
mission/
  engine.py             pure-Python state machine + ALL lesson text (STEPS); dispatch(action) -> snapshot()
  widget.py             anywidget: syncs `state` to the browser, forwards actions to the engine
  app.js, style.css     the UI: renders snapshot(), sends actions; no logic that matters for grading
simulator/              the same pattern for the free-play dashboard
lab.py + Cybersecurity_Interactive_Lab.ipynb + build_notebook.py   the code companion
data/                   synthetic evidence (make_data.py)
tests/                  pytest (engine + notebook execution + packaging) and Playwright browser walks
package_student.py      student ZIP: runtime + data + start.sh, no instructor answers or outputs
instructor/             facilitation, build, capability, customization, demo script, simulation guide
```

**Rules of the pattern:**
- The engine is testable without a browser. Every student action is a `dispatch` command, and every screen is a `snapshot()`.
- The notebook is a thin generated wrapper. Voilà hides code and runs it on launch.
- Serve on **loopback only** (127.0.0.1). Remote access goes through an SSH tunnel or an authenticated JupyterHub, never a public port.

---

## 7. Technical requirements (as built)

- Python 3.10+ (validated on 3.12 and 3.14).
- `ipywidgets`, `pandas`, `matplotlib`, `jupyterlab`, `anywidget>=0.9,<1`, `voila>=0.5,<0.6`, **`ipykernel>=6.29,<7`** (Voilà 0.5 hangs on the first code cell with ipykernel 7).
- No GPU, API keys, AI calls, accounts or Internet after install. No external JavaScript or CSS.
- Dev only: `requirements-dev.txt` (pytest, nbclient, nbformat), plus Playwright + Chromium for browser tests.
- Jetstream2: one person fits on an m3.quad (m3.small likely fine, not benchmarked). The repo is **public** so `git clone` on a VM doesn't prompt for GitHub credentials.

---

## 8. Acceptance criteria: v1 status

| v1 criterion | Status |
|---|---|
| Runs from a clean environment | **Met.** Fresh-copy `./start.sh` + browser walk verified 2026-09-28. |
| Each module has meaningful interaction | **Met.** 3–5 part tasks per step. |
| Each module demonstrates a distinct capability | **Met** (see `JUPYTER_CAPABILITY_REFERENCE.md`, `SIMULATION_GUIDE.md`). |
| Every module contributes to the investigation | **Met.** One continuous incident. |
| Useful feedback | **Met.** Every wrong choice explains itself. |
| No hidden prerequisite knowledge | **Met.** Each step teaches before asking. |
| Security activity safely contained | **Met.** Synthetic data, no sockets or processes. Tests block network access (notebook) and external requests (browser). |
| Progress represented clearly | **Met.** Stepper + checklists. The mission does not persist across reloads. |
| Instructor-facing view | **Partial.** Companion has one (simulated cohort). Mission has none. |
| Instructor documentation complete | **Partial.** Guides cover the companion and dashboard. The mission is covered by the README and `STEPS`, but has no dedicated facilitation guide yet. |
| Documentation explains pedagogy | **Met.** |
| Another instructor could adapt a pattern | **Met.** Section 6 pattern + `CUSTOMIZATION_GUIDE.md`. |

---

## 9. Build playbook: the steps we actually took

The order that got the product here, including the steps v1 didn't plan for.

1. **Write the PRD and design the incident first** (v1 Phases A–B): narrative, evidence, correct timeline, what each step must teach.
2. **Generate synthetic evidence** with a deterministic script (`make_data.py`) so it can be rebuilt and tested.
3. **Build the code notebook from a generator** (`build_notebook.py` + `lab.py`), never by hand, so the published starter is always clean. Write instructor guides alongside.
4. **Test from a fresh environment:** execute the notebook twice with nbclient, block network access, test every widget callback, package a student ZIP and check that it excludes answers.
5. **Publish to GitHub as a public repo.** Private repos prompt for credentials on `git clone` from a VM.
6. **Try it where it will run** (Jetstream2 m3.quad, Web Desktop). This is where the real problems showed up.
7. **Remove the code barrier:** build a no-code app with **anywidget** (Python engine + JS UI) served by **Voilà**. Add a **bundled Voilà template** so nothing loads from a CDN.
8. **Fix environment breakage:** Voilà 0.5 + ipykernel 7 hang. Reproduce locally and pin `ipykernel<7`.
9. **Review with the intended user and simplify:** the free-play dashboard was too complicated → build the **Guided Mission** on the same engine pattern and evidence, no clock.
10. **Second review round:** explanation before tasks; 3–5 part tasks instead of single clicks; no auto-scroll (Section 4 rules come from this).
11. **Automate a real browser walkthrough** (Playwright): every step including wrong turns, desktop + phone widths, no page movement, no external requests, screenshots for review. Run it after every UI change.
12. **Make launch one command:** `start.sh`, a quick start at the top of the README, then re-test from a fresh copy exactly as a new user would.
13. **Plan LMS delivery:** LTI 1.3 from Canvas → JupyterHub (`jupyterhub-ltiauthenticator`) → per-student server → the lab URL. Proven locally with Moodle standing in for Canvas (separate local testbed). Per-assignment links work because the activity's tool URL becomes the post-login redirect.
14. **Record validation** in `VALIDATION.md` (what was tested, versions, what was not).

---

## 10. Template checklist for a new lab

- [ ] Copy the repo layout from Section 6. Rename `mission/` if useful and keep `engine.py` / `widget.py` / `app.js` / `style.css`.
- [ ] Write the incident (or domain scenario) and its correct end state before any UI.
- [ ] Generate synthetic data with a deterministic script. Use documentation IP ranges and fictional names only.
- [ ] Put all student-facing text in `STEPS` with `learning`, `why`, `learned`, `learned_why`, `check`.
- [ ] Give each step 3–5 tasks. Write an explanation for every wrong answer.
- [ ] Engine first: `dispatch()` + `snapshot()`, with pytest covering the full path *and* wrong turns.
- [ ] UI renders the snapshot only. No auto-scroll. Status shown in text as well as color. Reduced-motion support.
- [ ] `build_<lab>.py` generates the one-cell notebook. Add it to `launch.py` and `package_student.py`.
- [ ] Keep the `ipykernel<7` pin until Voilà supports 7. Keep the offline template.
- [ ] Playwright walk: full path, wrong turns, phone width, `scrollY` unchanged, no external requests.
- [ ] Fresh-copy test: `./start.sh` from a clean folder, then the browser walk.
- [ ] README quick start stays at 3 commands. Update `VALIDATION.md`.
- [ ] Review with a real student or instructor, then iterate (expect at least two rounds).

---

## 11. Open items

- **Instructor view for the mission:** needs per-student records on a server (JupyterHub) or LMS grade passback (LTI AGS, not provided by ltiauthenticator).
- **Mission progress persistence** across page reloads.
- **Production hosting:** JupyterHub on Jetstream2 with per-student isolation (KubeSpawner or DockerSpawner) and HTTPS. Then validate on a school's Canvas test instance.
- **Mission facilitation guide** in `instructor/`.
- **Windows one-command launcher** (currently manual steps).
- The code companion's Voilà hang on Jetstream still needs diagnosis there (it works locally with `ipykernel<7`).
