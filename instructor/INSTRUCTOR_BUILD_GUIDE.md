# Build guide

> This guide covers the optional code-oriented companion. For the current visual student app, use [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md).

The notebook is the instructional surface; `lab.py` contains reusable controls so learners encounter short, purposeful cells. `data/` contains all evidence. `make_data.py` documents its fictional provenance and rebuilds it deterministically. `build_notebook.py` is the source of the starter notebook; regenerating replaces edits in the `.ipynb`.

## Follow one interaction

`hash_lab(case)` creates two text controls, observes changes, calculates SHA-256, and updates an HTML output. A separate concept check marks the lesson complete. This separates free exploration from assessed reasoning. `artifact_lab` uses the same pattern with a file selector and decoding checkbox, displaying content as text rather than running it.

`explorer(df)` applies dropdown filters and literal search to a pandas DataFrame, sorts by the selected column, then redraws a one-minute count chart. The table is the exact evidence, and a written summary describes the chart. Tables are sorted through the “Sort by” and “Descending” controls, not by clicking headers. The same pattern works for lab measurements or sensor records.

## Assessment and hints

`practice` provides a reusable concept question. `code_checks` uses an isolated in-memory SQLite database, verifies ordinary and apostrophe-containing names, tests a predicate-changing input, and probes the database boundary to see whether input is bound separately. This is a teaching test, not a general-purpose SQL security auditor or sandbox for arbitrary student code.

`Investigation.submit` checks stage order, increments attempts, validates the finding, records failures, and unlocks the next stage. Stage 5 also checks for a successful code-repair assessment. Stage 6 compares the order of all six labels. Answers accept surrounding whitespace and differences in case; they otherwise require the stated format. Failed feedback directs attention to evidence rather than giving a bare “wrong.”

`HINTS` has three method-focused hints per stage. `hint` reveals levels in order, caps the count at three, and avoids unlocking future stages. The count means unique hint levels revealed, not repeated button presses.

## State and instructor view

`Investigation` loads `.progress/session.json` on construction. A save writes a temporary file then replaces the session file; read-only storage falls back to in-memory operation with a message. This is one anonymous session per writable package copy, not concurrent multi-user storage. Do not open multiple actively used copies sharing the same progress path. Restarting the kernel reloads progress; resetting restores a blank session. Progress listeners update all visible progress bars and stage locks.

`instructor_panel` hides notes and analytics until selected. `dashboard` displays local per-stage attempts, failures, hint levels, completion and lesson checks, then a distinctly labeled fixed simulated cohort. Click Refresh analytics after activity. There is no Hub roster integration, identity collection, or outbound telemetry.

The toggle, Python validators, and local JSON are not access controls. Students can inspect or change local code. The completion token is generated after completion, but the generation method is also inspectable. For secure grading, the trust boundary must move outside the learner's kernel.

## Publication workflow

1. Edit the generator or runtime and update data only when deliberately changing the scenario.
2. Rebuild the notebook; run `python -m pytest -q`.
3. Review the lesson in JupyterLab, including filtering, decoding, repair, hints and reset.
4. Generate the student ZIP. It excludes instructor solutions, tests, progress and output.
5. Install dependencies into the chosen Hub user image; test a real user session before a class.

The project intentionally uses CPU Python with a small dependency set because the learning objective is interactive evidence analysis, not model inference. It uses the common pandas/matplotlib stack without heavyweight model libraries.
