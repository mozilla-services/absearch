import os
import subprocess
import sys
import time
from collections import defaultdict

import redis
from webtest import TestApp
from konfig import Config

from absearch import server, __version__
from absearch.aws import _get_connector, set_s3_file


def run_moto():
    args = [sys.executable, '-c',
            "from moto import server; server.main()",
            's3bucket_path']
    return subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


def run_redis():
    args = ['redis-server', '--port', '7777']
    return subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


_P = []
test_config = os.path.join(os.path.dirname(__file__), 'absearch.ini')


def setUp():
    # run Moto & Redis
    _P.append(run_moto())
    _P.append(run_redis())

    time.sleep(.1)

    # populate the bucket in Moto
    config = Config(test_config)
    conn = _get_connector(config)
    conn.create_bucket(config['aws']['bucketname'])

    datadir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

    for file_ in (config['absearch']['config'],
                  config['absearch']['schema']):
        filename = os.path.join(datadir, file_)
        set_s3_file(filename, config)

    _redis = redis.StrictRedis(**dict(config['redis']))
    _redis.flushdb()


def tearDown():
    for p in _P:
        p.kill()


def get_app():
    # create the web app
    server.app.debug = True
    server.initialize_app(test_config)
    server.app.catchall = False
    return TestApp(server.app)


def test_info():
    app = get_app()

    # test the APIs
    info = app.get('/__info__').json
    assert info['version'] == __version__


def test_set_cohort():
    app = get_app()

    # get a cohort
    path = '/firefox/39/beta/en-US/US/default/default'
    res = app.get(path)

    assert res.json['cohort'] == 'default'
    assert res.json['settings'] == {'searchDefault': 'Yahoo'}
    assert res.json['interval'] == 31536000


def test_set_cohort2():
    app = get_app()

    # get a cohort
    path = '/firefox/39/beta/cs-CZ/cz/default/default'
    res = app.get(path)

    assert res.json['cohort'] in ('default', 'foo23542', 'bar34234')
    settings = res.json['settings']

    # now that we have a cohort let's check back the settings
    path = '/firefox/39/beta/cs-CZ/cz/default/default/' + res.json['cohort']
    res = app.get(path)
    assert res.json['settings'] == settings


def test_max_cohort():
    # check that we can have at the most 3 users in the 'foo' cohort
    # that cohort is at 100% sampleRate for the fr territory under fr-FR
    app = get_app()

    # get the cohort 3 times
    path = '/firefox/39/beta/fr-FR/fr/default/default'
    for i in range(3):
        res = app.get(path)
        assert res.json['cohort'] == 'foo'

    # should be exausthed now, let's check we get a default now
    res = app.get(path)
    assert res.json['cohort'] == 'default'


def test_sampleRate():
    # de-DE has 4 cohorts. each one should represent 1% of the users
    # we're going to make 100 calls and see if we're around those percentages
    app = get_app()

    counts = defaultdict(int)

    # get the cohort 1000 times
    path = '/firefox/39/beta/de-DE/de/default/default'
    for i in range(1000):
        res = app.get(path)
        counts[res.json['cohort']] += 1

    # we should have around 10 users per cohort
    # and around 970 for the default
    assert 0 < counts['one'] <= 20, counts
    assert 0 < counts['two'] <= 20, counts
    assert 0 < counts['three'] <= 20, counts
    assert 955 <= counts['default'] <= 985, counts
