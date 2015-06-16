from setuptools import setup, find_packages
from absearch import __version__

install_requires = ['gevent', 'boto', 'bottle', 'jsonschema', 'redis',
                    'konfig', 'statsd', 'raven']

classifiers = ["Programming Language :: Python",
               "License :: OSI Approved :: Apache Software License",
               "Development Status :: 1 - Planning"]


setup(name='absearch',
      version=__version__,
      packages=find_packages(),
      description=("ABSearch Service"),
      license='APLv2',
      author="Mozilla Foundation & contributors",
      author_email="services-dev@lists.mozila.org",
      include_package_data=True,
      zip_safe=False,
      classifiers=classifiers,
      install_requires=install_requires,
      entry_points="""
      [console_scripts]
      absearch-server = absearch.server:main
      absearch-upload = absearch.upload:main
      absearch-check = absearch.check:main
      absearch-redis-dump = absearch.counters:dump
      absearch-redis-load = absearch.counters:load
      """)
