import statsd
import time
from collections import defaultdict
from contextlib import contextmanager


class FakeStatsd(object):
    def __init__(self, host, port, prefix):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)

    @contextmanager
    def timer(self, name):
        start = time.time()
        yield
        self.timers[name].append(time.time()-start)

    def incr(self, name, value=1):
        self.counters[name] += value


statsd.StatsClient = FakeStatsd

from absearch.tests.support import runServers, stopServers, get_app


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_metrics():
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/en-US/US/default/default'
    res = app.get(path)

    assert res.json['cohort'] == 'default'
    assert res.json['settings'] == {'searchDefault': 'Yahoo'}
    assert res.json['interval'] == 31536000

    # lets verify our metrics
    stats = app.app._statsd

    # we got one cohort counter
    assert stats.counters['cohorts.en-US.US.default'] == 1

    # we called add_user_to_cohort once
    assert len(stats.timers['add_user_to_cohort']), 1

    # we read two files in AWS
    assert len(stats.timers['get_s3_file']), 2

    # we incremented on redis the counter for the default cohort
    assert len(stats.timers['redis.incr']) == 1
