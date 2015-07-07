import os
from absearch.tests.support import runServers, stopServers, capture
from absearch.check import main


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_check():

    with capture() as out:
        res = main([])

    stdout, stderr = out
    assert stderr == '', stderr
    assert 'OK' in stdout
    assert res == 0


def test_check_fails():
    conf = os.path.join(os.path.dirname(__file__), '..', '..', 'data',
                        'config.json')
    os.rename(conf, conf + '.saved')
    try:
        with open(conf, 'w') as f:
            f.write("{'valid': 'json but crap'}")

        with capture():
            res = main([])
    finally:
        os.rename(conf + '.saved', conf)

    # we should fail
    assert res == 1
