import json
import os
from contextlib import contextmanager
import hashlib

from absearch.tests.support import runServers, stopServers, test_config
from absearch.aws import get_s3_file, set_s3_file
from konfig import Config


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_get_set_s3_file():
    class Stats(object):
        @contextmanager
        def timer(self, name):
            yield
        timed = timer

    stats = Stats()
    config = Config(test_config)
    datadir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    datafile = os.path.join(datadir, config['absearch']['config'])

    with open(datafile) as f:
        old_data = f.read()
        old_hash = hashlib.md5(old_data).hexdigest()

    # reading the S3 bucket (that was filled with datafile)
    res, hash = get_s3_file(datafile, config, statsd=stats)
    assert res['defaultInterval'] == 31536000
    assert hash == old_hash

    # changing the file content
    res['defaultInterval'] = -1
    with open(datafile, 'w') as f:
        f.write(json.dumps(res))

    try:
        # setting the file in the bucket with the new content
        set_s3_file(datafile, config, statsd=stats)

        # getting back the new content
        res, hash = get_s3_file(config['absearch']['config'], config,
                                use_cache=False, statsd=stats)

        # we should see the change
        assert res['defaultInterval'] == -1
    finally:
        # restore old content
        with open(datafile, 'w') as f:
            f.write(old_data)
