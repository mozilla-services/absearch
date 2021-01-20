import pytest
import requests


SERVER_URL = "http://0.0.0.0:8080"
COHORT_ENDPOINT = (
    "/1/{product}/{ver}/{channel}/{locale}/{territory}/{dist}/{distver}"
)


def is_running():
    try:
        requests.get(f"{SERVER_URL}/")
        return True
    except requests.ConnectionError:
        return False


pytestmark = pytest.mark.skipif(
    not is_running(),
    reason="local server not running"
)


@pytest.fixture(scope="session")
def cli():
    return requests.Session()


def test_search_default(cli):
    url = COHORT_ENDPOINT.format(
        product="firefox",
        ver="83.0",
        channel="release",
        locale="en-GB",
        territory="GB",
        dist="default",
        distver="default",
    )

    resp = cli.get(f"{SERVER_URL}{url}")
    data = resp.json()
    assert data["settings"]["searchDefault"] == "Yahoo"
