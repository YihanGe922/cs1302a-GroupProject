import unittest
from datetime import date
from deadline_conflict_solver.cli import make_report, main, interactive_payload
from deadline_conflict_solver.data import parse_payload
from deadline_conflict_solver.models import Task
from deadline_conflict_solver.planner import make_plan
from deadline_conflict_solver.reschedule import suggest_extra_hours
from unittest.mock import patch
import io
import json
from contextlib import redirect_stdout

class TestMerged(unittest.TestCase):
    def setUp(self):
        self.payload = {'start_date':'2026-11-14','daily_free_time':2,'buffer_ratio':0,
                        'assignments':[{'id':'A','name':'Test','deadline':'2026-11-14','estimated_hours':3}]}

    def test_conflict(self):
        report = make_report(self.payload)
        self.assertEqual(report['remaining_hours']['A'],1)
        self.assertEqual(len(report['conflicts']),1)

    def test_suggestion(self):
        report = make_report(self.payload)
        self.assertEqual(report['suggestion']['extra_hours_per_day'], 1)

    def test_json_compat(self):
        payload = {'start_date':'2026-11-14','daily_free_time':{'saturday':2},
                   'assignments':[{'name':'Reading','deadline':'2026-11-14','estimated_hours':1}]}
        self.assertEqual(make_report(payload)['conflicts'], [])

    def test_dependency(self):
        p = {'start_date':'2026-11-14','daily_free_time':3,'buffer_ratio':0,
             'assignments':[{'id':'A','name':'A','estimated_hours':2,'deadline':'2026-11-14'},
                           {'id':'B','name':'B','estimated_hours':1,'deadline':'2026-11-14','depends_on':['A']}]}
        report = make_report(p)
        self.assertEqual([x['task_id'] for x in report['schedule']],['A','B'])

    def test_cycle_rejected(self):
        p = {'start_date':'2026-11-14','daily_free_time':3,
             'assignments':[{'id':'A','name':'A','estimated_hours':1,'deadline':'2026-11-14','depends_on':['B']},
                           {'id':'B','name':'B','estimated_hours':1,'deadline':'2026-11-14','depends_on':['A']}]}
        with self.assertRaises(ValueError):
            make_report(p)

    def test_interactive(self):
        answers = iter(['2026-11-14','2','1','Reading','2026-11-14','1','2'])
        p = interactive_payload(input_fn=lambda _:next(answers),output_fn=lambda _:None)
        self.assertEqual(make_report(p)['conflicts'], [])

    def test_json_command(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'sample.json'
            path.write_text(json.dumps(self.payload))
            out=io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(['--json',str(path)]),0)
            self.assertEqual(json.loads(out.getvalue())['remaining_hours']['A'],1)

    def test_invalid_dates(self):
        p = dict(self.payload)
        p['start_date']='not-date'
        with self.assertRaises(ValueError):
            make_report(p)

    def test_invalid_negative_capacity(self):
        p = dict(self.payload)
        p['daily_free_time']=-3
        with self.assertRaises(ValueError):
            make_report(p)

if __name__ == '__main__': unittest.main()
