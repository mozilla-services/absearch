from absearch.tests.support import runServers, stopServers, test_config
from absearch.aws import get_s3_file
from konfig import Config


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_get_s3_file():
    config = Config(test_config)
    res = get_s3_file(config['absearch']['config'], config)
    assert res['defaultInterval'] == 31536000
