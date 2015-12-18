import hashlib
import os
import shutil
import tempfile
import json
import time

from absearch.settings import SearchSettings, accumulate
from absearch.exceptions import ReadError


def test_max_age():
    datadir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    testdir = tempfile.mkdtemp()

    for file_ in ('config.json', 'config.schema.json'):
        shutil.copyfile(os.path.join(datadir, file_),
                        os.path.join(testdir, file_))
    try:
        _test_max_age(testdir)
    finally:
        shutil.rmtree(testdir)


def _test_max_age(testdir):
    confpath = os.path.join(testdir, 'config.json')

    def config_reader():
        with open(confpath) as f:
            data = f.read()
            return json.loads(data), hashlib.md5(data).hexdigest()

    def schema_reader():
        with open(os.path.join(testdir, 'config.schema.json')) as f:
            data = f.read()
            return json.loads(data), hashlib.md5(data).hexdigest()

    settings = SearchSettings(config_reader, schema_reader, max_age=0.1)
    assert settings._default_interval == 31536000

    time.sleep(.1)

    with open(confpath) as f:
        data = json.loads(f.read())
        data['defaultInterval'] = -1
        with open(confpath, 'w') as fw:
            fw.write(json.dumps(data))

    # reading again should reload the file
    try:
        settings.get('prod', '39', 'channel', 'loc', 'terr',
                     'dist', 'distver')
    except KeyError:
        pass

    assert settings._default_interval == -1


def test_accumulate():
    elmts = [1, 2, 3, 4, 5]
    res = list(accumulate([1, 2, 3, 4, 5]))
    assert res == [1, 3, 6, 10, 15]

    elmts = []
    res = list(accumulate(elmts))
    assert res == []


def test_no_schema_validator():
    datadir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    testdir = tempfile.mkdtemp()
    confpath = os.path.join(testdir, 'config.json')

    shutil.copyfile(os.path.join(datadir, 'config.json'),
                    os.path.join(testdir, 'config.json'))

    def config_reader():
        with open(confpath) as f:
            data = f.read()
            return json.loads(data), hashlib.md5(data).hexdigest()

    try:
        settings = SearchSettings(config_reader, schema_reader=None)
    finally:
        shutil.rmtree(testdir)

    default = settings.get('firefox', '45', 'release', 'fr', 'fr',
                           'default', 'default')
    assert 'interval' in default


def test_loaded_broken():
    def config_reader():
        raise ReadError()

    try:
        SearchSettings(config_reader, schema_reader=None)
    except Exception:
        pass
    else:
        raise AssertionError()
