import time
from collections import defaultdict
import random
import operator
import bisect
import string
from string import ascii_lowercase, ascii_uppercase, digits
import copy
import re

from jsonschema import validate

from absearch import logger
from absearch.counters import MemoryCohortCounters
from absearch.exceptions import ReadError

from distutils.version import LooseVersion

DEFAULT_INTERVAL = 3600 * 24


def accumulate(iterable):
    it = iter(iterable)
    try:
        total = next(it)
    except StopIteration:
        return
    yield total
    for element in it:
        total = operator.add(total, element)
        yield total


_O = ascii_uppercase + ascii_lowercase + digits + '.-'
_S = ascii_lowercase + ascii_lowercase + digits + '.-'
_TAB = string.maketrans(_O, _S)
_REMOVE_PRERELEASE_SUFFIX = re.compile(r"(?:\-cdntest|\-localtest)$")


def _lower(s):
    try:
        return string.translate(s, _TAB)
    except Exception:
        return s.lower()


class SearchSettings(object):

    def __init__(self, config_reader, schema_reader=None, counter='memory',
                 counter_options=None, max_age=None):
        self.max_age = max_age
        self.schema_md5 = self.config_md5 = None
        self._last_loaded = None

        logger.info("Use memory backend for counters")
        counters_backend = MemoryCohortCounters

        if counter_options is None:
            counter_options = {}

        self._counters = counters_backend(**counter_options)

        self.config_reader = config_reader
        self.schema_reader = schema_reader
        self.load()

    def load(self):
        """Loads a configuration and builds internal indexes.

        config is a dict.
        """
        schema = None
        try:
            config, self.config_md5 = self.config_reader()

            if self.schema_reader:
                schema, self.schema_md5 = self.schema_reader()
            else:
                self.schema_md5 = None
        except ReadError:
            # if it's the first load we raise
            if self._last_loaded is None:
                raise
            else:
                # otherwise we keep the existing config
                # but we tell ops about the incident
                # XXX tell something to ops
                return

        if schema is not None:
            validate(config, schema)

        self._default_interval = config.get('defaultInterval',
                                            DEFAULT_INTERVAL)
        self._excluded = set(config['excludedDistributionIDPrefixes'])
        self._locales = {}
        self._territories = defaultdict(list)

        for locale, locale_data in config['locales'].items():
            locale = _lower(locale)

            # building indexes
            for territory, data in locale_data.items():
                territory = _lower(territory)

                tests = {}
                if territory == 'default':
                    # fallback territory
                    default = data
                else:
                    # default settings
                    default = data['default']

                    # converting filters
                    for name, test in data.get('tests', {}).items():
                        filters = test['filters']
                        filters['products'] = [_lower(p) for p in
                                               filters.get('products', [])]
                        filters['channels'] = [_lower(c) for c in
                                               filters.get('channels', [])]
                        # Use a very small version
                        filters['minVersion'] = filters.get('minVersion',
                                                            '0.1')
                        # Use a very large version
                        filters['maxVersion'] = filters.get('maxVersion',
                                                            '1000.0')
                        tests[name] = test

                self._locales[locale, territory] = default, tests
                self._territories[locale].append(territory)

        self._last_loaded = time.time()

    def get(self, prod, ver, channel, locale, territory, dist, distver,
            cohort=None):
        """Looks for a match and returns some settings.

        If no match is found, raises a KeyError.

        If cohort is None, randomly picks a cohort.
        """
        # reload the files if needed
        if (self.max_age is not None and
                time.time() - self._last_loaded > self.max_age):
            self.load()

        # we should do this at the http level
        locale = _lower(locale)
        territory = _lower(territory)
        prod = _lower(prod)
        # verify version at least contains a number
        try:
            int(ver.split('.')[0])
        except ValueError:
            raise ValueError("Bad version")
        channel = _lower(channel)
        # Allow for prerelease channels (release-localtest, beta-cdntest)
        channel = _REMOVE_PRERELEASE_SUFFIX.sub('', channel)
        dist = _lower(dist)
        distver = _lower(distver)

        # if dist is part of the excluded list, we're sending back
        # the global interval value
        for excluded in self._excluded:
            if dist.startswith(excluded):
                return {'interval': self._default_interval}

        # if the provided territory is not listed in that locale,
        # switch it to default
        if locale not in self._territories and '-' in locale:
            if locale.split('-')[0] in self._territories:
                locale = locale.split('-')[0]

        if territory not in self._territories[locale]:
            territory = 'default'

        # if we don't have that, send back an interval
        if (locale, territory) not in self._locales:
            return {'interval': self._default_interval}

        # we got something!
        if cohort is not None:
            res, picked_cohort = self._get_cohort(locale, territory, cohort)
            if picked_cohort != 'default':
                res['cohort'] = picked_cohort
        else:
            # pick one
            res = self._pick_cohort(locale, territory, prod, ver, channel)

        if 'interval' not in res:
            res['interval'] = self._default_interval

        allowed_keys = ('cohort', 'settings', 'interval')
        res = copy.deepcopy(res)

        for key in list(res.keys()):
            if key not in allowed_keys:
                del res[key]

        return res

    def _get_cohort(self, locale, territory, cohort):
        default, tests = self._locales[locale, territory]

        if cohort not in tests:
            # we send back a copy of the default settings
            return copy.deepcopy(default), 'default'

        # we send back the cohort settings if the cohort is active
        cohort_data = tests[cohort]
        start_time = cohort_data['filters'].get('startTime')
        if start_time and start_time >= time.time():
            # not active yet
            # we send back a copy of the default settings
            return copy.deepcopy(default), 'default'

        # we send back a copy of the cohort settings
        return copy.deepcopy(cohort_data), cohort

    def _is_filtered(self, prod, ver, channel, locale, territory, cohort,
                     filters):
        start_time = filters.get('startTime')
        if start_time and start_time >= time.time():
            # not active yet
            return True

        if len(filters['products']) > 0 and prod not in filters['products']:
            return True

        if len(filters['channels']) > 0 and channel not in filters['channels']:
            return True

        if LooseVersion(str(ver)) < LooseVersion(str(filters['minVersion'])):
            return True

        if LooseVersion(str(ver)) > LooseVersion(str(filters['maxVersion'])):
            return True

        max = filters.get('maxSize')
        if max:
            current = self._counters.get(locale, territory, cohort)
            if current >= max:
                return True

        # all good
        return False

    def _pick_cohort(self, locale, territory, prod, ver, channel):
        default, tests = self._locales[locale, territory]

        if tests == {}:
            self._counters.incr(locale, territory, 'default')
            return copy.deepcopy(default)

        # building a list of filtered cohorts with their weights
        total_weight = 0
        cohorts = []

        for cohort, info in tests.items():
            filters = info['filters']
            if self._is_filtered(prod, ver, channel, locale, territory,
                                 cohort, filters):
                continue

            weight = filters['sampleRate']
            cohorts.append((cohort, weight))
            total_weight += weight

        # adding default
        cohorts.append(('default', 100 - total_weight))

        # now let's pick one
        choices, weights = zip(*cohorts)
        cumdist = list(accumulate(weights))
        x = random.random() * 100
        picked = choices[bisect.bisect(cumdist, x)]
        self._counters.incr(locale, territory, picked)

        # and send it back
        if picked == 'default':
            return copy.deepcopy(default)

        settings = copy.deepcopy(tests[picked])
        settings['cohort'] = picked
        return settings
