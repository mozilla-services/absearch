from collections import defaultdict
from absearch import __version__
from absearch.tests.support import runServers, stopServers, get_app


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_info():
    app = get_app()

    # test the APIs
    info = app.get('/__info__').json
    assert info['version'] == __version__


def test_set_cohort():
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/en-US/US/default/default'
    res = app.get(path)

    assert res.json['cohort'] == 'default'
    assert res.json['settings'] == {'searchDefault': 'Yahoo'}
    assert res.json['interval'] == 31536000


def test_set_cohort2():
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default'
    res = app.get(path)

    assert res.json['cohort'] in ('default', 'foo23542', 'bar34234')
    settings = res.json['settings']

    # now that we have a cohort let's check back the settings
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default/' + res.json['cohort']
    res = app.get(path)
    assert res.json['settings'] == settings


def test_max_cohort():
    # check that we can have at the most 3 users in the 'foo' cohort
    # that cohort is at 100% sampleRate for the fr territory under fr-FR
    app = get_app()

    # get the cohort 3 times
    path = '/1/firefox/39/beta/fr-FR/fr/default/default'
    for i in range(3):
        res = app.get(path)
        assert res.json['cohort'] == 'foo'

    # should be exausthed now, let's check we get a default now
    res = app.get(path)
    assert res.json['cohort'] == 'default'


def test_sample_rate():
    # de-DE has 4 cohorts. each one should represent 1% of the users
    # we're going to make 100 calls and see if we're around those percentages
    app = get_app()

    counts = defaultdict(int)

    # get the cohort 1000 times
    path = '/1/firefox/39/beta/de-DE/de/default/default'
    for i in range(1000):
        res = app.get(path)
        counts[res.json['cohort']] += 1

    # we should have around 10 users per cohort
    # and around 970 for the default
    assert 0 < counts['one'] <= 20, counts
    assert 0 < counts['two'] <= 20, counts
    assert 0 < counts['three'] <= 20, counts
    assert 955 <= counts['default'] <= 985, counts


def test_hb():
    app = get_app()
    res = app.get('/__heartbeat__')
    assert res.json == {}


def test_excluded():
    app = get_app()

    # make sure an excluded distribution falls back to
    # sending back just a 200 + interval
    path = '/1/firefox/39/beta/de-DE/de/a/default'
    res = app.get(path).json
    assert res.keys() == ['interval']
