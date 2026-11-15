# Deadline Conflict Solver — Combined Prototype

A reusable Python package that helps students schedule assignments, identify unfinished work, and compare plans with additional daily study time.

## Motivation and features

Students often have several deadlines competing for limited study time. This tool combines deadline-first scheduling, conflict reports, and extra-time scenario comparisons in one workflow.

- Earliest deadline first; priority (1 highest to 5 lowest) breaks deadline ties.
- Task prerequisites, unknown-dependency validation, and cycle checks.
- A different capacity for each weekday and specific-date overrides.
- Adjustable buffer time (default 10%).
- Reports showing assignments and hours unfinished by the deadline.
- Extra-time scenarios in 0.5-hour increments (default maximum 3 hours per day).
- Interactive questions for basic and advanced settings.
- Reusable Python functions, CSV helpers, and automated tests.

## Install locally (macOS, Python 3.9+)

From the folder containing `pyproject.toml`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run

```bash
python -m deadline_conflict_solver.cli
```

After installation, you can also use:

```bash
deadline-solver
```

Answer the prompts. At `Configure advanced settings? [y/N]`, press Enter for defaults or enter `y` to configure weekday hours, date overrides, dependencies, buffer percentage, and the extra-hours search limit. Dependency IDs such as `T1` refer to the task numbers printed by the interface. Start dates and deadlines include the whole calendar day.

## Basic example

Enter start date `2026-11-15`, 2 available hours each day, one assignment named `Python Project`, deadline `2026-11-15`, estimated hours 3, priority 1, and `n` for advanced settings.

Expected result: 1.8 hours initially scheduled, 1.2 hours unfinished, and a feasible scenario adding 1.5 available hours per day. The buffer also applies to additional available time.

See `examples/interactive_example.md` for another walkthrough.

## Python API and helper modules

The import name remains `deadline_conflict_solver`. `Task`, `WorkBlock`, `PlanResult`, `make_plan`, `analyze_conflicts`, `suggest_extra_hours`, and `parse_payload` remain available from the package. `parse_payload` accepts a Python dictionary with `start_date`, `daily_free_time`, and `assignments`; assignment fields are `id`, `name`, `deadline`, `estimated_hours`, `priority`, and `depends_on`. Optional settings are `date_overrides`, `buffer_ratio`, and `max_extra_hours` (used by report generation).

`deadlines.py` retains date and weekday/weekend capacity helpers. `io_utils.py` retains `load_tasks_csv`, `export_schedule_csv`, and `format_plan`; these are Python helpers, not interactive file-import/export menu options.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Limitations

This is a heuristic, not an optimal solver; it can miss feasible arrangements. Tasks may be split into work blocks and capacities describe total daily hours, not appointment times. Prerequisites must finish before dependent work starts. The extra-time comparison adds the same amount to every day and returns the first feasible tested increment. Interactive entries are not automatically saved between runs.

## Development status

This remains an integration prototype based on the earlier scheduling demo. It has not been verified against the teammate's private source repository. Compare with the team's current files before merging. The existing distribution name and version are preserved; this archive does not establish publication to PyPI or verification on the course JupyterHub. Adapt the work together and follow the course's attribution requirements.
