import sys
import datetime
from functools import partial
import os
import json
import signal
import logging.config
import gevent
import hashlib

from konfig import Config
from bottle import (
    Bottle, HTTPError, template, TEMPLATE_PATH, request, response)
from statsd import StatsClient
from datadog import initialize, statsd
from raven import Client as Sentry

from absearch import __version__
from absearch.settings import SearchSettings
from absearch.aws import get_s3_file
from absearch import logger


TPL_DIR = os.path.join(os.path.dirname(__file__), 'templates')
TEMPLATE_PATH.insert(0, TPL_DIR)
app = Bottle()
summary_logger = logging.getLogger("request.summary")


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


class _Statsd(object):
    def __init__(self, config):
        if config.get('datadog', True):
            initialize(statsd_host=config['host'],
                       statsd_port=config['port'],
                       prefix=config['prefix'])
            self.datadog = True
            self._statsd = statsd
        else:
            self.datadog = False
            self._statsd = StatsClient(config['host'],
                                       config['port'],
                                       config['prefix'])

    def incr(self, metric, count=1, rate=1, **kw):
        if self.datadog:
            return self._statsd.increment(metric, value=count,
                                          sample_rate=rate, **kw)
        else:
            return self._statsd.incr(metric, count=count, rate=rate)

    def timer(self, metric, rate=1, **kw):
        if self.datadog:
            return self._statsd.timed(metric, sample_rate=rate, **kw)
        else:
            return self._statsd.timer(metric, rate=rate)


def before_request():
    request._received_at = datetime.datetime.now()


def after_request():
    isotimestamp = datetime.datetime.now().isoformat()
    t_usec = (datetime.datetime.now() - request._received_at).microseconds
    context = dict(
        agent=request.headers.get("User-Agent"),
        path=request.path,
        method=request.method,
        lang=request.headers.get("Accept-Language"),
        code=response.status_code,
        time=isotimestamp,
        t=t_usec / 1000,  # msec
    )
    if request.GET:
        context["qs"] = request.GET

    summary_logger.info("", extra=context)


def initialize_app(config):
    # logging configuration
    logging.config.fileConfig(config, disable_existing_loggers=False)
    logger.info("Read configuration from %r" % config)

    app._config_file = config
    app._config = Config(config)

    app.add_hook('before_request', before_request)
    app.add_hook('after_request', after_request)

    # statsd configuration
    app._statsd = _Statsd(app._config['statsd'])

    # sentry configuration
    if app._config['sentry']['enabled']:
        app._sentry = Sentry(app._config['sentry']['dsn'])
    else:
        app._sentry = None

    # backend configuration
    configfile = app._config['absearch']['config']
    schemafile = app._config['absearch']['schema']

    if app._config['absearch']['backend'] == 'aws':
        logger.info("Read config and schema from AWS")
        config_reader = partial(get_s3_file, configfile, app._config,
                                app._statsd)
        schema_reader = partial(get_s3_file, schemafile, app._config,
                                app._statsd)
    else:
        # directory
        datadir = app._config['directory']['path']
        logger.info("Read config and schema from %r on disk" % datadir)

        def config_reader():
            with open(os.path.join(datadir, configfile)) as f:
                data = f.read()
                return json.loads(data), hashlib.md5(data).hexdigest()

        def schema_reader():
            with open(os.path.join(datadir, schemafile)) as f:
                data = f.read()
                return json.loads(data), hashlib.md5(data).hexdigest()

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


@app.route('/')
def root():
    desc = ("This service provides regional search settings for Firefox "
            "clients. For more on the code, please see "
            "https://github.com/mozilla-services/absearch")

    return {'description': desc}


@app.route('/__lbheartbeat__')
def lhb():
    return {}


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
    return {'config_md5': app.settings.config_md5,
            'schema_md5': app.settings.schema_md5}


@app.route('/__info__')
def info():
    return {'version': __version__}


_cached_version = None


@app.route('/__version__')
def version():
    global _cached_version
    if _cached_version is None:
        path = os.getenv("VERSION_FILE", "./version.json")
        _cached_version = json.load(open(path, "r"))
    return _cached_version


PATH = '/1/<prod>/<ver>/<channel>/<locale>/<territory>/<dist>/<distver>'


@app.error(500)
def handle_500_error(code):
    if app._sentry:
        ident = app._sentry.get_ident(app._sentry.captureException())
        logger.error('An error occured. Sentry id: %s' % ident)
    logger.exception('An error occured')


@app.error(404)
def handle_404_error(code):
    response.content_type = 'application/json'


@app.route(PATH)
def add_user_to_cohort(**kw):

    with app._statsd.timer('add_user_to_cohort'):
        try:
            res = app.settings.get(**kw)
        except ValueError:
            raise HTTPError(status=404)

        cohort = res.get('cohort', 'default')
        if cohort != 'default':
            locale = kw['locale']
            territory = kw['territory']
            cohort = '.'.join([locale, territory, cohort])
            app._statsd.incr('enrolled', tags=[cohort])
        return res


@app.route('%s/<cohort>' % PATH)
def get_cohort_settings(**kw):
    with app._statsd.timer('get_cohort_settings'):
        try:
            asked_cohort = kw['cohort']
            res = app.settings.get(**kw)
            if asked_cohort == 'default':
                return res

            cohort = res.get('cohort', 'default')
            locale = kw['locale']
            territory = kw['territory']
            asked_cohort = '.'.join([locale, territory, asked_cohort])
            cohort = '.'.join([locale, territory, cohort])

            if asked_cohort != cohort:
                # we're getting discarded
                app._statsd.incr('discarded', tags=[asked_cohort])
            else:
                # we're getting back the cohort settings
                app._statsd.incr('refreshed', tags=[asked_cohort])

            return res

        except ValueError:
            raise HTTPError(status=404)


@app.route('/__api__')
def get_swagger(**kw):
    host = request.headers.get('X-Forwarded-Host')
    if host is None:
        host = request.headers.get('Host', 'localhost')

    scheme = request.headers.get('X-Forwarded-Proto', 'https')
    options = {'HOST': host, 'VERSION': __version__, 'SCHEME': scheme}
    return template('swagger', **options)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) > 0:
        config = args[0]
    else:
        config = os.path.join(os.path.dirname(__file__), '..', 'config',
                              'absearch.ini')

    initialize_app(config)
    abconf = app._config['absearch']

    app.run(host=abconf['host'], port=abconf['port'],
            server=abconf['server'], debug=abconf['debug'],
            quiet=abconf.get('quiet', not abconf['debug']))
