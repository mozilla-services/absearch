import sys
import datetime
import os
import json
import logging.config
import hashlib

from konfig import Config
from bottle import (
    Bottle, HTTPError, TEMPLATE_PATH, request, response)
from raven import Client as Sentry

from absearch import __version__
from absearch.settings import SearchSettings
from absearch import logger


TPL_DIR = os.path.join(os.path.dirname(__file__), 'templates')
TEMPLATE_PATH.insert(0, TPL_DIR)
CACHE_CONTROL_MAX_AGE = 300
app = Bottle()
summary_logger = logging.getLogger("request.summary")


def before_request():
    request._received_at = datetime.datetime.now()


def after_request():
    isotimestamp = datetime.datetime.now().isoformat()
    t_usec = (datetime.datetime.now() - request._received_at).microseconds
    cache_control = "max-age={max_age}".format(max_age=CACHE_CONTROL_MAX_AGE)
    response.set_header("Cache-Control", cache_control)
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

    # sentry configuration
    if app._config['sentry']['enabled']:
        app._sentry = Sentry(app._config['sentry']['dsn'])
    else:
        app._sentry = None

    # backend configuration
    configfile = app._config['absearch']['config']
    schemafile = app._config['absearch']['schema']

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
    counter_options = {}

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


@app.route(PATH)
def add_user_to_cohort(**kw):
    try:
        res = app.settings.get(**kw)
    except ValueError:
        raise HTTPError(status=404)

    cohort = res.get('cohort', 'default')
    if cohort != 'default':
        locale = kw['locale']
        territory = kw['territory']
        cohort = '.'.join([locale, territory, cohort])
    return res


@app.route('%s/<cohort>' % PATH)
def get_cohort_settings(**kw):
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

        return res

    except ValueError:
        raise HTTPError(status=404)


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
