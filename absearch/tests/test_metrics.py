import time
from collections import defaultdict
from contextlib import contextmanager
from absearch.tests.support import runServers, stopServers, get_app
from absearch import server


class FakeStatsd(object):
    def __init__(self, config):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)

    @contextmanager
    def timer(self, name):
        start = time.time()
        yield
        self.timers[name].append(time.time()-start)

    def incr(self, name, value=1, **kw):
        self.counters[name] += value


def setUp():
    server._old_Statsd = server._Statsd
    server._Statsd = FakeStatsd
    runServers()


def tearDown():
    stopServers()
    server._Statsd = server._old_Statsd


def test_metrics():
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/en-US/US/default/default'
    res = app.get(path)

    assert 'cohort' not in res.json
    assert res.json['settings'] == {'searchDefault': 'Yahoo'}
    assert res.json['interval'] == 31536000

    # lets verify our metrics
    stats = app.app._statsd

    # we got one cohort counter
    assert stats.counters['enrolled'] == 0

    # we called add_user_to_cohort once
    assert len(stats.timers['add_user_to_cohort']), 1


def test_enrolled():
    app = get_app()
    stats = app.app._statsd

    # get a cohort
    cohort = 'default'
    while cohort == 'default':
        path = '/1/firefox/39/beta/cs-CZ/cz/default/default'
        res = app.get(path)
        cohort = res.json.get('cohort', 'default')

    # we got one cohort counter
    assert stats.counters['enrolled'] == 1

    # we called add_user_to_cohort once
    assert len(stats.timers['add_user_to_cohort']), 1

    # now that we have a cohort let's check back the settings
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default/' + cohort
    res = app.get(path)

    assert stats.counters['refreshed'] == 1

    # also, an unexistant cohort should be counted as a discard
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default/meh'
    app.get(path)
    assert stats.counters['discarded'] == 1
