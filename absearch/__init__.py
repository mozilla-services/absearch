try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:     # pragma: no cover
    pass                # pragma: no cover

__version__ = '0.0.6'

import logging

logger = logging.getLogger('absearch')
