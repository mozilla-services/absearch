from konfig import Config
from absearch.tests.support import (runServers, stopServers, test_config,
                                    capture)
from absearch.counters import MemoryCohortCounters, RedisCohortCounters
from absearch.counters import dump, load


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_memory():
    counter = MemoryCohortCounters()

    for i in range(10):
        counter.incr('en-US', 'US', 'abc')
    counter.decr('en-US', 'US', 'abc')

    value = counter.get('en-US', 'US', 'abc')
    assert value == 9, value


def test_redis():
    config = Config(test_config)
    counter = RedisCohortCounters(**dict(config['redis']))

    for i in range(10):
        counter.incr('en-US', 'US', 'abc')
    counter.decr('en-US', 'US', 'abc')

    value = counter.get('en-US', 'US', 'abc')
    assert value == 9, value


def test_redis_dump_load():
    config = Config(test_config)
    counter = RedisCohortCounters(**dict(config['redis']))
    counter._redis.flushdb()

    for i in range(10):
        counter.incr('en-US', 'US', 'abc')

    dumped = list(counter.dump())

    counter = RedisCohortCounters(**dict(config['redis']))
    counter.load(dumped)

    value = counter.get('en-US', 'US', 'abc')
    assert value == 10, value


def test_dump_load():
    with capture() as out:
        dump(['', test_config])

    with open('/tmp/k', 'w') as f:
        f.write(out[0])

    with capture() as out:
        load(['', test_config, '/tmp/k'])

    stdout, stderr = out
    assert stderr == ''
    assert 'Done' in stdout
