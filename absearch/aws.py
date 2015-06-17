import json
import os

import boto
import boto.s3.connection
from boto.s3.key import Key

_CONNECTOR = None


def _get_connector(config):
    """Set a global connector.
    """
    global _CONNECTOR

    if _CONNECTOR is None:
        kw = {}
        if config['aws']['use_path_style']:
            kw['calling_format'] = boto.s3.connection.OrdinaryCallingFormat()

        is_secure = config['aws']['is_secure']
        if 'host' in config['aws']:
            conn = boto.connect_s3(is_secure=is_secure,
                                   port=config['aws']['port'],
                                   host=config['aws']['host'],
                                   **kw)

        else:
            conn = boto.s3.connect_to_region(config['aws']['region'],
                                             is_secure=is_secure,
                                             **kw)
        _CONNECTOR = conn
    return _CONNECTOR


def set_s3_file(filename, config, statsd=None):
    """Set a file content in a bucket.
    """
    conn = _get_connector(config)

    def set():
        bucket = conn.get_bucket(config['aws']['bucketname'])
        key = Key(bucket)
        key.key = os.path.split(filename)[-1]
        key.set_contents_from_filename(filename)

    if statsd:
        with statsd.timer('set_s3_file'):
            return set()
    return set()


def get_s3_file(filename, config, statsd=None):
    """Returns a S3 file from a bucket. With TTL-ed cache.
    """
    conn = _get_connector(config)

    def get():
        bucket = conn.get_bucket(config['aws']['bucketname'])
        key = Key(bucket)
        key.key = os.path.split(filename)[-1]
        return json.loads(key.get_contents_as_string().strip())

    if statsd:
        with statsd.timer('get_s3_file'):
            return get()
    return get()
