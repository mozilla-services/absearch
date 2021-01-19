import os
import sys
from cStringIO import StringIO
from contextlib import contextmanager

from webtest import TestApp

from absearch import server


test_config = os.path.join(os.path.dirname(__file__), 'absearch.ini')


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
