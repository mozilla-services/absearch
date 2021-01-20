import os
import shutil

from jsonschema.exceptions import ValidationError
from absearch.tests.support import capture
from absearch.check import main


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


def test_check_enum_fails():
    conf = os.path.join(os.path.dirname(__file__), '..', '..', 'data',
                        'config.json')
    os.rename(conf, conf + '.saved')
    broken_conf = os.path.join(os.path.dirname(__file__), 'broken-conf.json')
    e = None
    try:
        shutil.copy(broken_conf, conf)
        with capture():
            main([])
    except ValidationError as err:
        # that's what we want
        e = err
    finally:
        os.rename(conf + '.saved', conf)

    # we should fail
    assert e is not None
