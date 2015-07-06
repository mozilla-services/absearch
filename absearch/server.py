import sys
from functools import partial
import os
import json
import signal
import logging.config

import gevent
from konfig import Config
from bottle import Bottle
from statsd import StatsClient
from raven import Client as Sentry

from absearch import __version__
from absearch.settings import SearchSettings
from absearch.aws import get_s3_file
from absearch import logger


app = Bottle()


def close():
    # do some cleanup here
    sys.exit(0)


def reload():
    print('Reloading configuration')
    initialize_app(app._config_file)
    print('Done')


gevent.signal(signal.SIGHUP, reload)
gevent.signal(signal.SIGTERM, close)
gevent.signal(signal.SIGINT, close)


def initialize_app(config):
    app._config_file = config
    app._config = Config(config)

    # logging configuration
    logging.config.fileConfig(config)

    # statsd configuration
    app._statsd = StatsClient(app._config['statsd']['host'],
                              app._config['statsd']['port'],
                              prefix=app._config['statsd']['prefix'])

    # sentry configuration
    if app._config['sentry']['enabled']:
        app._sentry = Sentry(app._config['sentry']['dsn'])
    else:
        app._sentry = None

    # backend configuration
    configfile = app._config['absearch']['config']
    schemafile = app._config['absearch']['schema']

    if app._config['absearch']['backend'] == 'aws':
        config_reader = partial(get_s3_file, configfile, app._config,
                                app._statsd)
        schema_reader = partial(get_s3_file, schemafile, app._config,
                                app._statsd)
    else:
        # directory
        datadir = app._config['directory']['path']

        def config_reader():
            with open(os.path.join(datadir, configfile)) as f:
                return json.loads(f.read())

        def schema_reader():
            with open(os.path.join(datadir, schemafile)) as f:
                return json.loads(f.read())

    # counter configuration
    counter = app._config['absearch']['counter']
    if counter == 'redis':
        counter_options = dict(app._config['redis'])
    else:
        counter_options = {}
    counter_options['statsd'] = app._statsd

    max_age = app._config['absearch']['max_age']
    app.settings = SearchSettings(config_reader, schema_reader, counter,
                                  counter_options, max_age)


@app.route('/__heartbeat__')
def hb():
    # doing a realistic code, but triggering a S3 call as well
    configfile = app._config['absearch']['config']
    get_s3_file(configfile, app._config, app._statsd, use_cache=False)

    res = app.settings.get('firefox', '39', 'default', 'en-US', 'US',
                           'default', 'default')

    incremented_cohort = res.get('cohort', 'default')

    # let's decrement so we don't interfer with real counters
    app.settings._counters.decr('en-US', 'US', incremented_cohort)
    return {}


@app.route('/__info__')
def info():
    return {'version': __version__}

PATH = '/1/<prod>/<ver>/<channel>/<locale>/<territory>/<dist>/<distver>'


@app.error(500)
def handle_500_error(code):
    if app._sentry:
        ident = app._sentry.get_ident(app._sentry.captureException())
        logger.error('An error occured. Sentry id: %s' % ident)
    logger.exception('An error occured')


@app.route(PATH)
def add_user_to_cohort(prod, ver, channel, locale, territory, dist, distver):
    with app._statsd.timer('add_user_to_cohort'):
        res = app.settings.get(prod, ver, channel, locale, territory, dist,
                               distver)
        if 'cohort' in res:
            cohort = '.'.join(['cohorts', locale, territory,
                               res['cohort']])
            app._statsd.incr(cohort)
        return res


@app.route('%s/<cohort>' % PATH)
def get_cohort_settings(prod, ver, channel, locale, territory, dist, distver,
                        cohort):
    with app._statsd.timer('get_cohort_settings'):
        return app.settings.get(prod, ver, channel, locale, territory, dist,
                                distver, cohort)


def main():
    if len(sys.argv) > 1:
        config = sys.argv[1]
    else:
        config = os.path.join(os.path.dirname(__file__), '..', 'config',
                              'absearch.ini')

    initialize_app(config)
    abconf = app._config['absearch']

    app.run(host=abconf['host'], port=abconf['port'],
            server=abconf['server'], debug=abconf['debug'])


if __name__ == '__main__':
    main()
