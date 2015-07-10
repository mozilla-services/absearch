import os
import time
import signal

from webtest import AppError
from absearch.tests.support import (runServers, stopServers, get_app, _P,
                                    run_redis, capture, run_moto)


def setUp():
    runServers()


def tearDown():
    stopServers()


def test_redis_dies():

    # life is good, we get some cohorts
    app = get_app()
    path = '/1/firefox/39/beta/en-US/US/default/default'
    res = app.get(path)

    # now redis goes down because life is hard
    redis_process = _P[1]
    try:
        os.killpg(redis_process.pid, signal.SIGTERM)
        redis_process.kill()
    except OSError:
        pass
    redis_process.wait()

    # what happens to our app ?
    class MySentry(object):
        exceptions = 0

        def get_ident(self, something):
            self.exceptions += 1
            return 'id'

        def captureException(self):
            return 'yeah'

    old_sentry = app.app._sentry
    app.app._sentry = MySentry()
    app.app.catchall = True

    with capture():
        try:
            res = app.get(path)
        except AppError as e:
            # that's what we want
            assert '500' in str(e)
        else:
            raise Exception(res)
        finally:
            app.app._sentry = old_sentry
            app.app.catchall = False

    # and... redis is back!
    _P.append(run_redis())
    time.sleep(.1)

    # our app should be ok.
    app.get(path)


def test_aws_dies():
    # life is good, we get some cohorts
    app = get_app()
    path = '/1/firefox/39/beta/en-US/US/default/default'
    app.get(path)

    # now aws goes down because life is hard
    moto_process = _P[0]
    try:
        os.killpg(moto_process.pid, signal.SIGTERM)
        moto_process.kill()
    except OSError:
        pass
    moto_process.wait()

    # what happens to our app ?
    # our app should be ok because it has a memory cache.
    app.get(path)

    # but sometimes the cache has to be updated
    app.app.settings.max_age = 10
    app.app.settings._last_loaded = time.time() - 10

    # in that case we want the server to try to
    # call S3 - fail after a specified timeout
    # and fallback to the existing memory
    # but also emit a warning
    app.get(path)

    # and... redis is back!
    _P.insert(0, run_moto())
    time.sleep(.1)

    # our app should be ok.
    app.get(path)
