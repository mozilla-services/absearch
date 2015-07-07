import os
import time
import signal

from webtest import AppError
from absearch.tests.support import (runServers, stopServers, get_app, _P,
                                    run_redis, capture)


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
