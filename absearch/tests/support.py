import os
import subprocess
import sys
import time

import redis
from webtest import TestApp
from konfig import Config

from absearch import server
from absearch.aws import _get_connector, set_s3_file


def run_moto():
    args = [sys.executable, '-c',
            "from moto import server; server.main()",
            's3bucket_path']
    return subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


def run_redis():
    args = ['redis-server', '--port', '7777']
    return subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


_P = []
test_config = os.path.join(os.path.dirname(__file__), 'absearch.ini')


def runServers():
    # run Moto & Redis
    _P.append(run_moto())
    _P.append(run_redis())

    time.sleep(.1)

    # populate the bucket in Moto
    config = Config(test_config)
    conn = _get_connector(config)
    conn.create_bucket(config['aws']['bucketname'])

    datadir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

    for file_ in (config['absearch']['config'],
                  config['absearch']['schema']):
        filename = os.path.join(datadir, file_)
        set_s3_file(filename, config)

    _redis = redis.StrictRedis(**dict(config['redis']))
    _redis.flushdb()


def stopServers():
    for p in _P:
        p.kill()


def get_app():
    # create the web app
    server.app.debug = True
    server.initialize_app(test_config)
    server.app.catchall = False
    return TestApp(server.app)
