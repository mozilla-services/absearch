import time
from collections import defaultdict
import random

from jsonschema import validate
from absearch.counters import MemoryCohortCounters, RedisCohortCounters


DEFAULT_INTERVAL = 3600 * 24


class SearchSettings(object):

    def __init__(self, config_reader, schema_reader=None, counter='memory',
                 counter_options=None, max_age=None):
        self.max_age = max_age

        if counter == 'memory':
            counters_backend = MemoryCohortCounters
        else:
            counters_backend = RedisCohortCounters

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
        config = self.config_reader()
        schema = self.schema_reader and self.schema_reader() or None

        if schema is not None:
            validate(config, schema)

        self._default_interval = config.get('interval', DEFAULT_INTERVAL)
        self._excluded = set(config['excludedDistributionIDPrefixes'])
        self._locales = {}
        self._territories = defaultdict(list)
        self._random = {}

        for locale, locale_data in config['locales'].items():
            locale = locale.lower()

            # building indexes
            for territory, data in locale_data.items():
                territory = territory.lower()

                tests = {}
                if territory == 'default':
                    # fallback territory
                    default = data
                else:
                    # default settings
                    default = data['default']
                    # tests
                    if 'tests' in data:
                        tests = data['tests']

                self._locales[locale, territory] = default, tests
                self._territories[locale].append(territory)

                # preparing the random collection
                rates = []
                count = 0
                for test, data in tests.items():
                    rate = data['sampleRate']
                    count += rate
                    rates.extend([test] * rate)

                rates.extend(['default'] * (100-count))
                self._random[locale, territory] = rates

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

        locale = locale.lower()
        territory = territory.lower()

        # XXX prod, ver, channel & distver are not used at this point
        # if dist is part of the excluded list, we're sending back
        # the global interval value
        if dist in self._excluded:
            return {'interval': self._default_interval}

        # if the provided territory is not listed in that locale,
        # switch it to default
        if territory not in self._territories[locale]:
            territory = 'default'

        # if we don't have that
        if (locale, territory) not in self._locales:
            raise KeyError("Could not find the %s/%s combo" % (locale,
                           territory))

        # we got something!
        if cohort is not None:
            res = self._get_cohort(locale, territory, cohort)
            res['cohort'] = cohort
            return res
        else:
            # pick one
            return self._pick_cohort(locale, territory)

    def _get_cohort(self, locale, territory, cohort):
        default, tests = self._locales[locale, territory]

        if cohort not in tests:
            # we send back the default settings
            return default

        # we send back the cohort settings if the cohort is active
        cohort_data = tests[cohort]
        if 'startTime' in cohort_data:
            if cohort_data['startTime'] > time.time():
                # not active yet
                # we send back the default settings
                return default

        return cohort_data

    def _pick_cohort(self, locale, territory):
        default, tests = self._locales[locale, territory]
        default['cohort'] = 'default'

        if tests == {}:
            self._counters.incr(locale, territory, 'default')
            return default

        # XXX pick a random one and check out the counters.
        # next: should use the sampleRate
        picked = None

        while True:
            cohort = random.choice(self._random[locale, territory])
            if cohort == 'default':
                self._counters.incr(locale, territory, cohort)
                return default

            info = tests[cohort]
            # did we reach the max ?
            max = info.get('maxSize')
            if max:
                current = self._counters.get(locale, territory, cohort)
                if current >= max:
                    # yes, we should remove that cohort from _random
                    # and replace all occurrences with 'default'
                    def _pick(value):
                        if value == cohort:
                            return 'default'
                        return value

                    randoms = [_pick(value) for value in
                               self._random[locale, territory]]
                    self._random[locale, territory] = randoms
                    continue
                else:
                    self._counters.incr(locale, territory, cohort)
                    picked = cohort
                    break
            else:
                # no max we can pick it
                self._counters.incr(locale, territory, cohort)
                picked = cohort
                break

        if picked is None:
            return default

        settings = tests[cohort]
        settings['cohort'] = cohort
        return settings
