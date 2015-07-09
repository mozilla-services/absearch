import os
import shutil
import tempfile
import json
import time

from absearch.settings import SearchSettings


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
            return json.loads(f.read())

    def schema_reader():
        with open(os.path.join(testdir, 'config.schema.json')) as f:
            return json.loads(f.read())

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
