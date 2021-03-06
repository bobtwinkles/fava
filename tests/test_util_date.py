from datetime import date, datetime
from unittest import mock

import pytest

from fava.util.date import (Interval, parse_date, get_next_interval,
                            interval_ends, substitute,
                            number_of_days_in_period)


def test_interval():
    assert Interval.get('month') is Interval.MONTH
    assert Interval.get('year') is Interval.YEAR
    assert Interval.get('YEAR') is Interval.YEAR
    assert Interval.get('asdfasdf') is Interval.MONTH


def _to_date(string):
    """Convert a string in ISO 8601 format into a datetime.date object."""
    return datetime.strptime(string, '%Y-%m-%d').date() if string else None


@pytest.mark.parametrize('input_date_string,interval,expect', [
    ('2016-01-01', Interval.DAY, '2016-01-02'),
    ('2016-01-01', Interval.WEEK, '2016-01-04'),
    ('2016-01-01', Interval.MONTH, '2016-02-01'),
    ('2016-01-01', Interval.QUARTER, '2016-04-01'),
    ('2016-01-01', Interval.YEAR, '2017-01-01'),
    ('2016-12-31', Interval.DAY, '2017-01-01'),
    ('2016-12-31', Interval.WEEK, '2017-01-02'),
    ('2016-12-31', Interval.MONTH, '2017-01-01'),
    ('2016-12-31', Interval.QUARTER, '2017-01-01'),
    ('2016-12-31', Interval.YEAR, '2017-01-01'),
])
def test_get_next_interval(input_date_string, interval, expect):
    get = get_next_interval(_to_date(input_date_string), interval)
    assert get == _to_date(expect)


def test_get_next_intervalfail2():
    with pytest.raises(NotImplementedError):
        get_next_interval(date(2016, 4, 18), 'decade')


def test_interval_tuples():
    assert list(
        interval_ends(date(2014, 3, 5), date(2014, 5, 5), Interval.MONTH)) == [
            date(2014, 3, 5),
            date(2014, 4, 1),
            date(2014, 5, 1),
            date(2014, 5, 5),
        ]
    assert list(
        interval_ends(date(2014, 1, 1), date(2014, 5, 1), Interval.MONTH)) == [
            date(2014, 1, 1),
            date(2014, 2, 1),
            date(2014, 3, 1),
            date(2014, 4, 1),
            date(2014, 5, 1),
        ]
    assert list(
        interval_ends(date(2014, 3, 5), date(2014, 5, 5), Interval.YEAR)) == [
            date(2014, 3, 5),
            date(2014, 5, 5),
        ]
    assert list(
        interval_ends(date(2014, 1, 1), date(2015, 1, 1), Interval.YEAR)) == [
            date(2014, 1, 1),
            date(2015, 1, 1),
        ]


@pytest.mark.parametrize("string,output", [
    ('year', '2016'),
    ('(year-1)', '2015'),
    ('year-1-2', '2015-2'),
    ('(year)-1-2', '2016-1-2'),
    ('(year+3)', '2019'),
    ('(year+3)month', '20192016-06'),
    ('(year-1000)', '1016'),
    ('quarter', '2016-Q2'),
    ('quarter+2', '2016-Q4'),
    ('quarter+20', '2021-Q2'),
    ('(month)', '2016-06'),
    ('month+6', '2016-12'),
    ('(month+24)', '2018-06'),
    ('week', '2016-W25'),
    ('week+20', '2016-W45'),
    ('week+2000', '2054-W42'),
    ('day', '2016-06-24'),
    ('day+20', '2016-07-14'),
])
def test_substitute(string, output):
    # Mock the imported datetime.date in fava.util.date module
    # Ref:
    # http://www.voidspace.org.uk/python/mock/examples.html#partial-mocking
    with mock.patch('fava.util.date.datetime.date') as mock_date:
        mock_date.today.return_value = _to_date('2016-06-24')
        mock_date.side_effect = date
        assert substitute(string) == output


@pytest.mark.parametrize("expect_start,expect_end,text", [
    (None, None, '    '),
    ('2000-01-01', '2001-01-01', '   2000   '),
    ('2010-10-01', '2010-11-01', '2010-10'),
    ('2000-01-03', '2000-01-04', '2000-01-03'),
    ('2015-01-05', '2015-01-12', '2015-W01'),
    ('2015-04-01', '2015-07-01', '2015-Q2'),
    ('2014-01-01', '2016-01-01', '2014 to 2015'),
    ('2014-01-01', '2016-01-01', '2014-2015'),
    ('2011-10-01', '2016-01-01', '2011-10 - 2015'),
])
def test_parse_date(expect_start, expect_end, text):
    start, end = _to_date(expect_start), _to_date(expect_end)
    assert parse_date(text) == (start, end)


@pytest.mark.parametrize("expect_start,expect_end,text", [
    ('2014-01-01', '2016-06-27', 'year-2-day+2'),
    ('2016-01-01', '2016-06-25', 'year-day'),
    ('2015-01-01', '2017-01-01', '2015-year'),
])
def test_parse_date_relative(expect_start, expect_end, text):
    start, end = _to_date(expect_start), _to_date(expect_end)
    with mock.patch('fava.util.date.datetime.date') as mock_date:
        mock_date.today.return_value = _to_date('2016-06-24')
        mock_date.side_effect = date
        assert parse_date(text) == (start, end)


@pytest.mark.parametrize("interval,date_str,expect", [
    (Interval.DAY, '2016-05-01', 1),
    (Interval.DAY, '2016-05-31', 1),
    (Interval.WEEK, '2016-05-01', 7),
    (Interval.WEEK, '2016-05-31', 7),
    (Interval.MONTH, '2016-05-02', 31),
    (Interval.MONTH, '2016-05-31', 31),
    (Interval.MONTH, '2016-06-11', 30),
    (Interval.MONTH, '2016-07-31', 31),
    (Interval.MONTH, '2016-02-01', 29),
    (Interval.MONTH, '2015-02-01', 28),
    (Interval.MONTH, '2016-01-01', 31),
    (Interval.QUARTER, '2015-02-01', 90),
    (Interval.QUARTER, '2015-05-01', 91),
    (Interval.QUARTER, '2016-02-01', 91),
    (Interval.QUARTER, '2016-12-01', 92),
    (Interval.YEAR, '2015-02-01', 365),
    (Interval.YEAR, '2016-01-01', 366),
])
def test_number_of_days_in_period(interval, date_str, expect):
    assert number_of_days_in_period(interval, _to_date(date_str)) == expect


def test_number_of_days_in_period2():
    with pytest.raises(NotImplementedError):
        number_of_days_in_period('test', date(2011, 2, 1))
