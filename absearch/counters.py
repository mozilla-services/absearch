import sys
from collections import defaultdict
from konfig import Config

import redis


class MemoryCohortCounters(object):

    def __init__(self):
        self._counters = defaultdict(int)

    def _key(self, *args):
        return ':'.join(args)

    def incr(self, locale, territory, cohort):
        self._counters[self._key(locale, territory, cohort)] += 1

    def get(self, locale, territory, cohort):
        return self._counters[self._key(locale, territory, cohort)]


class RedisCohortCounters(object):
    def __init__(self, host='localhost', port=6739, db=0, **kw):
        self._redis = redis.StrictRedis(host=host, port=port, db=db)
        if 'statsd' in kw:
            self._statsd = kw['statsd']
        else:
            self._statsd = None

    def _key(self, *args):
        return ':'.join(args)

    def dump(self):
        for key in self._redis.smembers('absearch:keys'):
            yield '%s:%s' % (key, self._redis.get(key))

    def load(self, lines):
        for line in lines:
            line = line.split(':')
            counter = int(line[-1])
            key = ':'.join(line[:-1])

            with self._redis.pipeline() as pipe:
                pipe.sadd('absearch:keys', key)
                pipe.set(key, counter)
                pipe.execute()

    def incr(self, locale, territory, cohort):
        key = self._key(locale, territory, cohort)

        def _incr(pipe):
            pipe.sadd('absearch:keys', key)
            pipe.incr(key)
            pipe.execute()

        with self._redis.pipeline() as pipe:
            if self._statsd:
                with self._statsd.timer('redis.incr'):
                    _incr(pipe)
            else:
                _incr(pipe)

    def get(self, locale, territory, cohort):
        def _get():
            return self._redis.get(self._key(locale, territory, cohort))

        if self._statsd:
            with self._statsd.timer('redis.get'):
                res = _get()
        else:
            res = _get()

        if res is None:
            res = 0
        return int(res)


def dump():
    config = Config(sys.argv[1])
    counters = RedisCohortCounters(**dict(config['redis']))
    for line in counters.dump():
        print(line)


def load():
    config = Config(sys.argv[1])
    data = sys.argv[2]
    counters = RedisCohortCounters(**dict(config['redis']))

    print('Loading %r into Redis' % data)
    with open(data) as f:
        counters.load(f)
    print('Done')


if __name__ == '__main__':
    dump()
