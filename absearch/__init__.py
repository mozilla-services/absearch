try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

__version__ = '0.1'

import logging

logger = logging.getLogger('absearch')
