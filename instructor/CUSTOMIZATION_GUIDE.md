# Customization guide

> This guide covers the optional code-oriented companion. For the current visual student app, use [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md).

Edit `build_notebook.py` for changes to the published starter, then rebuild. Editing only the `.ipynb` is suitable for a personal lesson copy but will be overwritten by regeneration.

## Replace a dataset

Log explorers expect `timestamp`, `host`, `username`, and `event_type`. Network explorers expect `timestamp`, `host`, `protocol`, and `process`; retain other columns used in questions. Use ISO UTC timestamps. Change `make_data.py`, regenerate, and verify every narrative link. For another discipline, change selector columns in `explorer` to your domain's categories.

Do not calculate the trusted manifest from the already-modified evidence: that erases the integrity lesson. The generator hashes baseline files before replacing the collector file.

## Change a question or add an activity

```python
display(practice(case, 'Sensor analysis',
                 'Which sensor needs recalibration?', 'sensor-03',
                 'Compare calibration offsets with the baseline.'))
```

Use a stable module name. If adding a sixth assessed module, update the `/5` count in `progress`, documentation and tests. Questions should require a useful inference.

## Modify a widget

Add `destination_ip` to the network selector list in `explorer` when comparing known endpoints matters more than text search. Keep an All option so learners can recover from empty results. A numeric slider can observe `value` and refilter a measurement range using the same Output/observe pattern.

## Add a visualization

```python
import matplotlib.pyplot as plt
counts = network.groupby('process').size()
ax = counts.plot.barh(title='Connection records by process')
ax.set_xlabel('Record count')
plt.show()
display(counts.rename('records').to_frame())
```

Add an interpretive question and exact values. Move this into an explorer callback if it should respond to filters. A chart should support a comparison students need to make.

## Add validation and hints

Extend `code_checks` with a meaningful behavior, such as Unicode usernames. Add a database row and expected result, then verify both a correct and incorrect function. Avoid requiring one exact source-code spelling when several repairs are valid.

Edit a stage's three `HINTS` entries: concept → evidence location → operation. Do not insert the final answer. The stored count is unique levels revealed, not repeated clicks.

## Change a CTF stage

Update the answer in `submit`, its notebook prompt, evidence in `make_data.py`, the solution guide, and tests together. For timeline changes, update `TIMELINE`, timestamps and rank order. The implementation intentionally has six stages. Adding a seventh requires extending state arrays, completion bounds, progress totals, challenge construction and dashboard logic.

If changing state structure, increment its schema version and reset old progress. Solve the revised case from evidence alone after running tests.

## Transfer to another discipline

| Discipline | Evidence | Interaction | Assessment |
|---|---|---|---|
| Biology | Measurements and sample metadata | Select conditions, inspect outliers | Identify anomalous sample and justify follow-up |
| Engineering | Sensor and maintenance logs | Filter machine/time, compare baseline | Reconstruct fault sequence |
| Data science | Observational dataset | Filter, summarize, chart | Test a claim and discuss confounding |

Keep concise instruction, learner-controlled experiments, evidence-based tasks, useful feedback, and a larger application. Change the story and assessment together so the final investigation remains coherent.
