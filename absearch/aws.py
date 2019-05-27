import json
import os
import hashlib
import socket

import boto
import boto.s3.connection
from boto.s3.key import Key
from boto.s3 import connect_to_region as conn_region
from boto.s3.connection import S3ResponseError

from absearch.exceptions import ReadError


class AWSReadError(ReadError):
    pass


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
                                   aws_access_key_id="fake",
                                   aws_secret_access_key="fake",
                                   port=config['aws']['port'],
                                   host=config['aws']['host'],
                                   **kw)

        else:
            conn = conn_region(config['aws']['region'],     # pragma: no cover
                               is_secure=is_secure, **kw)   # pragma: no cover

        conn.num_retries = int(config['aws'].get('num_retries', 1))
        timeout = float(config['aws'].get('timeout', 5))
        conn.http_connection_kwargs['timeout'] = timeout
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
    try:
        conn = _get_connector(config, use_cache=use_cache)
    except (socket.error, S3ResponseError) as e:
        # XXX tell something to ops
        raise AWSReadError(str(e))

    def _get():
        try:
            bucket = conn.get_bucket(config['aws']['bucketname'])
            key = Key(bucket)
            key.key = os.path.split(filename)[-1]
            content = key.get_contents_as_string()
        except (socket.error, S3ResponseError) as e:
            # XXX tell something to ops
            raise AWSReadError(str(e))

        hash = hashlib.md5(content).hexdigest()
        return json.loads(content), hash

    if statsd:
        with statsd.timer('get_s3_file'):
            return _get()
    return _get()
