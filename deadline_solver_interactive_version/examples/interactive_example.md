# Interactive walkthrough

Run `python -m deadline_conflict_solver.cli`.

1. Enter start date `2026-11-15` and 3 available hours per day.
2. Enter two assignments: Project (T1), due `2026-11-16`, 2 hours, priority 1; Report (T2), due `2026-11-16`, 1 hour, priority 2.
3. Enter `y` for advanced settings.
4. Press Enter to keep the same weekday hours and to skip date overrides.
5. Enter `y` for dependencies. Leave T1 prerequisites blank; enter `T1` for T2.
6. Enter `0` for buffer percentage, and press Enter for the default extra-hours limit.

The report should schedule T1 before T2 and show no conflicts. Setting different weekday hours and date-specific overrides is also available in advanced settings.
