from gevent import monkey
monkey.patch_all()

from loads.case import TestCase
import os


class TestSearch(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestSearch, self).__init__(*args, **kwargs)

    def test_api(self):
        res = self.session.get(self.server_url)
        self.assertEqual(res.status_code, 200)
