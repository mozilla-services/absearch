import logging
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:     # pragma: no cover
    pass                # pragma: no cover

__version__ = '0.2.0'
logger = logging.getLogger('absearch')
