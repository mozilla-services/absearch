import sys
from collections import defaultdict
from konfig import Config


class MemoryCohortCounters(object):

    def __init__(self, **kw):
        self._counters = defaultdict(int)

    def _key(self, *args):
        return ':'.join(args)

    def incr(self, locale, territory, cohort):
        self._counters[self._key(locale, territory, cohort)] += 1

    def get(self, locale, territory, cohort):
        return self._counters[self._key(locale, territory, cohort)]

    def decr(self, locale, territory, cohort):
        self._counters[self._key(locale, territory, cohort)] -= 1

