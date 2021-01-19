import os
import subprocess
import sys
import signal
import time
from cStringIO import StringIO
from contextlib import contextmanager
import socket

from webtest import TestApp

from absearch import server


def run_moto():
    socket.setdefaulttimeout(.1)
    args = [sys.executable, '-c',
            "from moto import server; server.main()",
            's3bucket_path']
    return subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid)


_P = []
test_config = os.path.join(os.path.dirname(__file__), 'absearch.ini')


def runServers():
    # run Moto
    _P.append(run_moto())

    time.sleep(.1)


def stopServers():
    for p in _P:
        try:
            os.killpg(p.pid, signal.SIGTERM)
            p.kill()
        except OSError:
            pass
        p.wait()

    _P[:] = []


def get_app():
    # create the web app
    server.app.debug = True
    server.initialize_app(test_config)
    server.app.catchall = False
    return TestApp(server.app)


@contextmanager
def capture():
    oldout, olderr = sys.stdout, sys.stderr
    try:
        out = [StringIO(), StringIO()]
        sys.stdout, sys.stderr = out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()
