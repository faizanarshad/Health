from datetime import date, timedelta
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.healthagent import nlp_utils as nlu


def test_parse_today_tomorrow():
    today = date.today().isoformat()
    assert nlu.parse_natural_date('today') == today
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert nlu.parse_natural_date('tomorrow') == tomorrow


def test_parse_iso_and_in_days():
    assert nlu.parse_natural_date('2026-08-01') == '2026-08-01'
    assert nlu.parse_natural_date('in 3 days') == (date.today() + timedelta(days=3)).isoformat()


def test_parse_next_weekday():
    # pick a weekday name
    res = nlu.parse_natural_date('next monday')
    assert res is not None
    # result is a valid YYYY-MM-DD
    assert len(res) == 10
