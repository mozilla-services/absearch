import gevent

from absearch import __version__
from absearch.tests.support import (runServers, stopServers, get_app, capture,
                                    test_config)
from absearch.server import main


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_info():
    app = get_app()

    # test the APIs
    info = app.get("/__info__").json
    assert info["version"] == __version__


def test_all_locales():
    # We want to test that the locale defaults are set correctly, if they are
    # not this test fails to alert the config changes in absearchdata are bad
    locale_configs = {
        "en-US": {
            "US": ("Yahoo")
        },
        "fr-FR": {
            "FR": ("Google", "Yahoo")
        }
    }
    app = get_app()

    for locale, config in locale_configs.iteritems():
        for territory, search_providers in config.iteritems():
            path = "/1/firefox/39/beta/{0}/{1}/default/default"
            path = path.format(locale, territory)
            res = app.get(path)
            assert res.json["settings"]["searchDefault"] in search_providers


def test_main():
    with capture():
        greenlet = gevent.spawn(main, [test_config])
        gevent.sleep(0.1)

    assert greenlet.started
    greenlet.kill()
    gevent.wait([greenlet])
    assert not greenlet.started
