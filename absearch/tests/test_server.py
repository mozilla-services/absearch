import os
from collections import defaultdict
import json

from absearch import __version__
from absearch.tests.support import get_app


def test_lbheartbeat():
    app = get_app()

    # test the APIs
    resp = app.get('/__lbheartbeat__')
    assert resp.headers["Cache-Control"] == "max-age=300"
    assert resp.status_code == 200


def test_info():
    app = get_app()

    # test the APIs
    resp = app.get('/__info__')
    info = resp.json
    assert resp.headers["Cache-Control"] == "max-age=300"
    assert info['version'] == __version__


def test_version():
    app = get_app()

    try:
        os.remove("./version.json")
    except OSError:
        pass

    try:
        app.get('/__version__')
        assert False, "should crash if version.json is missing."
    except IOError:
        pass

    json.dump({'project': 'absearch'}, open('./version.json', 'w'))

    resp = app.get('/__version__')
    version = resp.json
    assert resp.headers["Cache-Control"] == "max-age=300"
    assert version['project'] == 'absearch'


def test_set_cohort():
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/en-US/US/default/default'
    res = app.get(path)

    assert 'cohort' not in res.json
    assert res.json['settings'] == {'searchDefault': 'Yahoo'}
    assert res.json['interval'] == 31536000
    assert res.headers["Cache-Control"] == "max-age=300"


def test_default_interval():
    # en-US/FR does not exists. we fallback to the default in en-US
    # and if it does not contain an interval we want to add the default
    # interval
    app = get_app()
    path = '/1/Firefox/39/release/en-US/FR/default/default'
    res = app.get(path)
    assert 'cohort' not in res.json
    assert res.json['interval'] == 31536000
    assert res.headers["Cache-Control"] == "max-age=300"


def test_just_3_keys():
    app = get_app()
    path = '/1/Firefoox/39/release/de-DE/DE/default/default'
    res = app.get(path)
    keys = res.json.keys()
    keys.sort()
    wanted = ['cohort', 'interval', 'settings']
    wanted2 = ['interval', 'settings']
    assert keys == wanted or wanted2, keys


def test_weird_locale_name():
    # we want to make sure a cohort with a weird locale fallsback
    # to a local we have. see issue #5
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/cs-WAAAT/cz/default/default'
    res = app.get(path)

    # we get one of those and not 'Google' because the territory
    # falled back to 'cz'
    wanted = ('Google1', 'Google2', 'Google3')
    assert res.json['settings']['searchDefault'] in wanted


def _test_set_cohort2():
    app = get_app()
    # get a cohort
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default'
    res = app.get(path)

    cohort = res.json.get('cohort', 'default')
    assert cohort in ('default', 'foo23542', 'bar34234')
    settings = res.json['settings']

    # now that we have a cohort let's check back the settings
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default/' + cohort
    res = app.get(path)
    assert res.json['settings'] == settings
    if 'cohort' not in res.json:
        wanted = ('Google1',)
    else:
        wanted = ('Google2', 'Google3')

    assert res.json['settings']['searchDefault'] in wanted
    # also, an unexistant cohort should fall back to the default
    # settings for the territory
    path = '/1/firefox/39/beta/cs-CZ/cz/default/default/meh'
    res = app.get(path)
    assert res.json['settings']['searchDefault'] == 'Google1'
    # and we should not see the cohort key in there anymore
    assert 'cohort' not in res.json


def test_pick_test_cohort_and_ask_again():
    app = get_app()

    # get a cohort
    path = '/1/firefox/39/beta/fr-FR/fr/default/default'
    res = app.get(path)

    res = res.json
    cohort = res.get('cohort', 'default')
    assert res['cohort'] == 'fooBaz'
    settings = res['settings']

    # now that we have a cohort let's check back the settings
    path += '/' + cohort
    res = app.get(path)

    assert res.json['settings'] == settings
    assert res.json['cohort'] == 'fooBaz'


def test_unexistant_territory():
    app = get_app()
    # check that an unexistant territory sends back the default
    # from the locale
    path = '/1/firefox/39/beta/fr-FR/uz/default/default'
    res = app.get(path).json
    assert res['settings']['searchDefault'] == 'GoogleD'


def test_unexistant_locale():
    app = get_app()
    # check that an unexistant locale sends back and interval
    path = '/1/firefox/39/beta/hh-FR/uz/default/default'

    res = app.get(path).json
    assert res.keys() == ['interval']


def test_max_cohort():
    # check that we can have at the most 3 users in the 'foo' cohort
    # that cohort is at 100% sampleRate for the fr territory under fr-FR
    app = get_app()

    # get the cohort 3 times
    path = '/1/firefox/39/beta/fr-FR/fr/default/default'
    for i in range(3):
        res = app.get(path)
        assert res.json.get('cohort') == 'fooBaz', i

    # should be exausthed now, let's check we get a default now
    res = app.get(path)

    # when default we don't have the cohort key in the response
    assert 'cohort' not in res.json, res.json


def test_product_filter():
    # check that we are filtering by product
    app = get_app()

    # get the cohort for fr-FR+fr
    path = '/1/firefox/39/beta/fr-FR/fr/default/default'
    res = app.get(path)
    assert res.json.get('cohort') == 'fooBaz', res.json

    # if the product it not firefox, we should bypass the foo cohort
    path = '/1/thunderbird/39/beta/fr-FR/fr/default/default'
    res = app.get(path)
    assert 'cohort' not in res.json, res.json


def test_channel_filter():
    # check that we are filtering by product
    app = get_app()

    # get the cohort for fr-FR+fr
    path = '/1/firefox/39/beta/fr-FR/fr/default/default'
    res = app.get(path)
    assert res.json.get('cohort') == 'fooBaz', res.json

    # if the channel is not listed, we should bypass the foo cohort
    path = '/1/firefox/39/alpha/fr-FR/fr/default/default'
    res = app.get(path)
    assert 'cohort' not in res.json, res.json

    # cdntest should map to regular channel
    path = '/1/firefox/39/beta-cdntest/fr-FR/fr/default/default'
    res = app.get(path)
    assert res.json.get('cohort') == 'fooBaz', res.json

    # localtest should map to regular channel
    path = '/1/firefox/39/release-localtest/fr-FR/fr/default/default'
    res = app.get(path)
    assert res.json.get('cohort') == 'fooBaz', res.json


def test_version_filter():
    # check that we are filtering by product
    app = get_app()

    # get the cohort for fr-FR+fr
    path = '/1/firefox/39/beta/fr-FR/fr/default/default'
    res = app.get(path)
    assert res.json.get('cohort') == 'fooBaz', res.json

    # if the version is < 39, we should bypass the foo cohort
    path = '/1/firefox/38/beta/fr-FR/fr/default/default'
    res = app.get(path)
    assert 'cohort' not in res.json, res.json


def test_sample_rate():
    # de-DE has 4 cohorts. each one should represent 1% of the users
    # we're going to make 1000 calls and see if we're around those percentages
    app = get_app()

    counts = defaultdict(int)

    # get the cohort 1000 times
    path = '/1/firefox/39/beta/de-DE/de/default/default'
    for i in range(1000):
        res = app.get(path)
        if 'cohort' not in res.json:
            counts['default'] += 1
        else:
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

    assert 'schema_md5' in res.json, res.json
    assert 'config_md5' in res.json, res.json


def test_root():
    app = get_app()
    res = app.get('/')
    assert res.json.keys() == ['description']


def test_excluded():
    app = get_app()

    # make sure an excluded distribution falls back to
    # sending back just a 200 + interval
    path = '/1/firefox/39/beta/de-DE/de/ayeah/default'
    res = app.get(path).json
    assert res.keys() == ['interval']


def test_invalid_url():
    app = get_app()
    # these should return 404
    for url in ('/1/firefox/.*/release/.*/.*/default/default/web.xml',
                '/1/firefox/.*/release/.*/.*/default/default'):
        app.get(url, status=404)


def test_string_min_version():
    app = get_app()

    path = '/1/firefox/39.1/esr/en-GB/GB/default/default'
    res = app.get(path)

    assert res.json['settings'] == {'searchDefault': 'Yahoo'}

    path = '/1/firefox/39.2/esr/en-GB/GB/default/default'
    res = app.get(path)

    assert res.json['settings'] == {'searchDefault': 'Google'}

    path = '/1/firefox/39.3/esr/en-GB/GB/default/default'
    res = app.get(path)

    assert res.json['settings'] == {'searchDefault': 'Google'}


def test_string_max_version():
    app = get_app()

    path = '/1/firefox/45.3/esr/en-GB/GB/default/default'
    res = app.get(path)

    assert res.json['settings'] == {'searchDefault': 'Google'}

    path = '/1/firefox/45.4/esr/en-GB/GB/default/default'
    res = app.get(path)

    assert res.json['settings'] == {'searchDefault': 'Google'}

    path = '/1/firefox/45.5/esr/en-GB/GB/default/default'
    res = app.get(path)

    assert res.json['settings'] == {'searchDefault': 'Yahoo'}
