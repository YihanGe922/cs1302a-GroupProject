# Deadline Conflict Solver — Combined Prototype

An educational Python package combining an advanced scheduling engine with a JSON CLI and a beginner-friendly interactive CLI. **This is a new integration prototype, not a verified merge of the teammate's private GitHub source.** Verify course AI-use rules and originality, and adapt together before submission.

## Features

- Earliest-deadline-first scheduling, with priority for deadline ties
- Task dependencies and cycle checks
- Weekday/weekend availability and specific date overrides
- Adjustable buffer time
- Conflict reports for unfinished assignments
- What-if simulations that add daily study hours
- JSON input / JSON output; optional no-JSON interactive input
- Importable functions and automated tests

## Install locally (macOS, Python 3.9+)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run — no JSON editing needed

```bash
python -m deadline_conflict_solver.cli --interactive
```

Answer the prompts, then the tool prints the generated schedule, conflicts and a what-if suggestion. Or, after installation:

```bash
deadline-solver --interactive
```

## Run — teammate-style JSON mode

```bash
python -m deadline_conflict_solver.cli examples/homework.json
python -m deadline_conflict_solver.cli --json examples/homework.json
```

JSON fields: `start_date`, `daily_free_time` (number or weekday dictionary), `assignments` (`name`, `deadline`, `estimated_hours`); optional `id`, `priority` (1–5), `depends_on` (list of IDs), `buffer_ratio`, `date_overrides`, `max_extra_hours`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Important limitations

- This is a **heuristic schedule**, not an optimizer and not guaranteed to find all feasible plans.
- Time units are hours, dates are calendar-day boundaries, and it assumes tasks can be split into short work blocks.
- In interactive mode, capacities are the same every day and dependencies are not entered. Use JSON mode for advanced options.
- What-if mode increases each day's available time by the same increment and finds the first feasible tested increment. It is not an optimal recommendation.
- Package name is a local example, not a claim that it has been published to PyPI.

## For the group

The known source for the scheduling modules was the earlier Advanced Demo; the teammate's actual GitHub private-source files were not available for code-level merge. The JSON schema and CLI behavior were recreated based on screenshots. Before merging into the group repository, compare with their real `cli.py`, `models.py`, `solver.py`, and agree on a single public API. Use a feature branch and a pull request, not a replacement of `main`.
