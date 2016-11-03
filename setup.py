from setuptools import setup, find_packages
from absearch import __version__

install_requires = ['gevent==1.1rc3',
                    'boto==2.39.0',
                    'bottle==0.12.8',
                    'jsonschema==2.5.1',
                    'redis==2.10.3',
                    'konfig==0.9',
                    'statsd==3.1',
                    'datadog==0.10.0',
                    'raven==5.3.1']


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
