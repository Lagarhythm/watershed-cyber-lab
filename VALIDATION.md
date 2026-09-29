# Validation record — 2026-09-27

**Result: 9 automated tests passed in 7.63 seconds**, plus a live JupyterLab/Chromium smoke test.

Validated in a newly created local virtual environment on Python 3.14 with ipywidgets 8.1.9, pandas 2.3.3, matplotlib 3.11.2, JupyterLab 4.6.4, nbformat 5.11.1 and nbclient 0.11.0. Dependency ranges permit Python 3.10+ compatible releases; other Python versions were not separately exercised.

## Automated coverage

- Notebook schema and fresh-kernel execution twice from an isolated package copy; no cell exceptions. Initial secure-code failures are intentional displayed feedback.
- Notebook execution with `socket.create_connection` blocked, plus review of runtime code for external network use. This is a smoke check, not an OS-level network sandbox.
- Evidence-derived solution: exactly one hash mismatch, valid Base64 JSON, matching process-start event, eight correlated connections at 60-second intervals, and chronological six-event reconstruction.
- Stage locks, wrong-answer feedback, code-assessment prerequisite, hint-level capping, generated completion token, save/reload, and reset.
- Secure and vulnerable query behavior, apostrophes, unknown users, predicate-changing input and bound-parameter checks.
- Python-side widget callbacks for hash updates, decoding, concept checks, searches, sorting, stage unlock and instructor view.
- Malformed saved progress recovery (three cases).
- Student archive exclusions and cleared notebook outputs.

## Browser review

Opened the actual notebook in JupyterLab using headless Chromium, ran all cells, confirmed six investigation controls, changed a hash input and observed the live changed-bit count become zero. Screenshots of the hashing lesson and investigation controls were visually inspected for legibility and enabled/locked stage distinctions. The temporary validation server was shut down afterward.

## Deployment boundaries

No live JupyterHub was available or modified. User-image installation, per-user file permissions and browser/widget support still require an ordinary Hub deployment smoke check. Classic Notebook, mobile layouts, screen readers and multi-user capacity were not tested. Python-side callbacks and local state are formative teaching tools, not tamper-resistant assessment. Simulated aggregate analytics are labeled and are not real student records.

The distributed notebook is rebuilt in its original unsolved state with no saved outputs. The student ZIP excludes instructor guides, tests, generators and local progress. It includes the diagram and all evidence required for offline use after dependencies are installed.

# Student simulation revision — 2026-09-27

The primary student experience is now `Watershed_Simulation.ipynb` via `python launch.py` (Voilà), with source hidden and a custom anywidget dashboard. The original notebook remains the optional coding companion.

**Result: 15 automated tests passed in 9.72 seconds**, plus a complete live Chromium/Voilà interaction test. Additional packages: anywidget 0.11.0 and Voilà 0.5.13.

New engine tests cover traffic stopping and resuming under containment, safe restoration after removal, availability costs, evidence correlation, wrong-host containment, late file access, end-of-window stopping, query injection versus parameter binding, replay/reset, widget messages, and fresh execution of the simulation notebook.

`tests/browser_smoke.py` exercises actual widget communication and the full student path to 100 objective points. It additionally reloads and resumes a completed browser-saved attempt, resets it, observes three live connections, downloads a report, checks a 390-pixel layout for app overflow, and selects a host by keyboard. It blocks external HTTP requests and asserts none are attempted with the bundled template. No JavaScript page errors occurred. Desktop operations/evidence/debrief and narrow-screen screenshots were visually reviewed. Reduced-motion mode was exercised; a full screen-reader audit was not performed.

Run the browser check separately when needed:

```bash
python -m pip install playwright
python -m playwright install chromium
python launch.py --port 8898
# In another terminal using the same environment:
python tests/browser_smoke.py
```

Screenshots are in `docs/previews/`. Browser tooling is a development dependency only; students do not install it. The student ZIP now includes both notebooks, the simulator, offline template, launcher and evidence, while excluding instructor guides, screenshots, tests and saved progress.

This validates local application behavior, not a deployed Jetstream2/JupyterHub instance or cohort capacity. The simulation is deterministic, has no external AI, and does not operate on real systems. Availability weights, traffic background and the containment/file-access relationship are explicitly simplified in the debrief and simulation guide. Browser storage is profile/origin scoped and is not a central student database. Objective scores are formative and inspectable.
