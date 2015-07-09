import json
import os
import hashlib

import boto
import boto.s3.connection
from boto.s3.key import Key
from boto.s3 import connect_to_region as conn_region


_CONNECTOR = None


def _get_connector(config, use_cache=False):
    """Set a global connector.
    """
    global _CONNECTOR

    if _CONNECTOR is None or not use_cache:
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
            conn = conn_region(config['aws']['region'],     # pragma: no cover
                               is_secure=is_secure, **kw)   # pragma: no cover

        if use_cache:
            _CONNECTOR = conn
        else:
            return conn

    return _CONNECTOR


def set_s3_file(filename, config, statsd=None):
    """Set a file content in a bucket.
    """
    conn = _get_connector(config)

    def _set():
        bucket = conn.get_bucket(config['aws']['bucketname'])
        key = Key(bucket)
        key.key = os.path.split(filename)[-1]
        key.set_contents_from_filename(filename)

    if statsd:
        with statsd.timer('set_s3_file'):
            return _set()
    return _set()


def get_s3_file(filename, config, statsd=None, use_cache=True):
    """Returns a S3 file from a bucket. With TTL-ed cache.

    The returned value is a tuple (json, md5 hash)
    """
    conn = _get_connector(config, use_cache=use_cache)

    def _get():
        bucket = conn.get_bucket(config['aws']['bucketname'])
        key = Key(bucket)
        key.key = os.path.split(filename)[-1]
        content = key.get_contents_as_string()
        hash = hashlib.md5(content).hexdigest()
        return json.loads(content), hash

    if statsd:
        with statsd.timer('get_s3_file'):
            return _get()
    return _get()
