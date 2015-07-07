import os
import time
import signal
import redis
from absearch.tests.support import (runServers, stopServers, get_app, _P,
                                    run_redis)


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
    try:
        res = app.get(path)
    except redis.ConnectionError:
        pass    # that's what we want
    else:
        raise Exception(res)

    # and... redis is back!
    _P.append(run_redis())
    time.sleep(.1)

    # our app should be ok.
    res = app.get(path)
