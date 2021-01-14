import os
import pytest
import requests

ENVS = {
    "prod": "https://search.services.mozilla.com",
    "stage": "https://search.stage.mozaws.net",
    "local": "http://0.0.0.0:8080",
}

SERVER = os.getenv("SERVER", "prod")
SERVER_URL = ENVS.get(SERVER, SERVER)
COHORT_ENDPOINT = "/1/{product}/{ver}/{channel}/{locale}/{territory}/{dist}/{distver}"


@pytest.fixture
def cli():
    return requests.Session()


def test_lbheartbeart(cli):
    resp = cli.get(f"{SERVER_URL}/__lbheartbeat__")
    assert resp.status_code == 200


def test_heartbeart(cli):
    resp = cli.get(f"{SERVER_URL}/__heartbeat__")
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "product,version,channel,locale,territory,cohort",
    [
        ("firefox", 39, "release", "en-US", "US", None),
        ("firefox", 82, "release", "en-US", "US", "nov17-2"),
        ("firefox", 57, "release", "en-US", "US", "nov17-2"),
        ("fennec", 57, "release", "en-US", "US", "nov17-fennec-1"),
        ("firefox", 52.6, "esr", "en-US", "US", "apr18-1"),
        ("firefox", 57, "release", "en-US", "CA", "nov17-2"),
        ("fennec", 58, "release", "en-US", "CA", "nov17-fennec-1"),
        ("fennec", 58, "release", "en-US", "RU", "jan18-fennec-1"),
    ],
)
def test_cohort(cli, product, version, channel, locale, territory, cohort):
    url = COHORT_ENDPOINT.format(
        product=product,
        ver=version,
        channel=channel,
        locale=locale,
        territory=territory,
        dist="default",
        distver="default",
    )

    resp = cli.get(f"{SERVER_URL}{url}")
    data = resp.json()
    assert data.get("cohort") == cohort


@pytest.mark.parametrize(
    "product,cohort,locale,territory,engine",
    [
        ("firefox", "default", "en-US", "US", "Google"),
        ("firefox", "default", "en-US", "CA", "Google"),
        ("firefox", "default", "en-US", "RU", "Google"),
        ("firefox", "jan18-1", "en-US", "RU", "Yandex"),
        ("firefox", "jan18-fennec-1", "en-US", "RU", "Yandex"),
        ("firefox", "default", "be", "BY", "Яндекс"),
        ("firefox", "default", "be", "KZ", "Яндекс"),
        ("firefox", "default", "be", "RU", "Яндекс"),
        ("firefox", "default", "be", "TR", "Яндекс"),
        ("firefox", "default", "kk", "KZ", "Яндекс"),
        ("firefox", "default", "kk", "BY", "Яндекс"),
        ("firefox", "default", "kk", "RU", "Яндекс"),
        ("firefox", "default", "kk", "TR", "Яндекс"),
        ("firefox", "default", "ru", "RU", "Яндекс"),
        ("firefox", "default", "ru", "BY", "Яндекс"),
        ("firefox", "default", "ru", "KZ", "Яндекс"),
        ("firefox", "default", "ru", "TR", "Яндекс"),
        ("firefox", "default", "tr", "TR", "Yandex"),
        ("firefox", "default", "tr", "BY", "Yandex"),
        ("firefox", "default", "tr", "KZ", "Yandex"),
        ("firefox", "default", "tr", "RU", "Yandex"),
        ("firefox", "mar18-firefox-1", "zh-TW", "HK", "Google"),
        ("firefox", "nov17-fennec-1", "zh-TW", "HK", "Google"),
        ("firefox", "mar18-firefox-1", "zh-TW", "TW", "Google"),
        ("firefox", "nov17-fennec-1", "zh-TW", "TW", "Google"),
    ],
)
def test_default_engine(cli, cohort, locale, territory, product, engine):
    url = COHORT_ENDPOINT.format(
        product=product,
        ver=82,
        channel="release",
        locale=locale,
        territory=territory,
        dist="default",
        distver="default",
    )
    resp = cli.get(f"{SERVER_URL}{url}/{cohort}")
    data = resp.json()
    assert data["settings"]["searchDefault"] == engine


@pytest.mark.parametrize(
    "territory",
    [
        "CH",
        "GB",
        "IE",
        "NL",
    ],
)
def test_localized_ebay(cli, territory):
    url = COHORT_ENDPOINT.format(
        product="firefox",
        ver=57,
        channel="release",
        locale="en-US",
        territory=territory,
        dist="default",
        distver="default",
    )

    resp = cli.get(f"{SERVER_URL}{url}/nov17-1")
    data = resp.json()
    assert data["settings"]["visibleDefaultEngines"] == [
        "amazondotcom",
        "bing",
        "ebay-%s" % territory.lower(),
        "google",
        "twitter",
        "wikipedia",
        "ddg",
    ]


DEFAULT_ENGINES = ["amazondotcom", "bing", "google", "twitter", "wikipedia", "ddg"]


@pytest.mark.parametrize(
    "product,version,channel,locale,territory,cohort,engines",
    [
        (
            "firefox",
            39,
            "release",
            "en-US",
            "US",
            "default",
            DEFAULT_ENGINES,
        ),
        (
            "firefox",
            82,
            "release",
            "uk",
            "US",
            "default",
            ["google", "yandex-uk", "meta-ua", "metamarket", "wikipedia-uk", "ddg"],
        ),
    ],
)
def test_default_engines(
    cli, product, version, channel, locale, territory, cohort, engines
):
    url = COHORT_ENDPOINT.format(
        product=product,
        ver=version,
        channel=channel,
        locale=locale,
        territory=territory,
        dist="default",
        distver="default",
    )

    resp = cli.get(f"{SERVER_URL}{url}/{cohort}")
    data = resp.json()
    assert data["settings"]["visibleDefaultEngines"] == engines
